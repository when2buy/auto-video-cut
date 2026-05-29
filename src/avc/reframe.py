"""9:16 face-tracked reframe via OpenCV + ffmpeg.

For each input video, sample N frames evenly, run OpenCV Haar cascade face
detection on each, EMA-smooth the dominant face center over time, then build
a single ffmpeg ``crop=W:H:x(t):y=0`` expression that pans the crop window to
follow the face. Falls back to center-crop if face tracking fails (no faces
or <50% of samples have a face).

Why Haar and not MediaPipe Face Detection: MediaPipe 0.10.35 (latest on
this pod) requires the new Tasks API + a model file download. OpenCV Haar
ships built-in (``cv2.data.haarcascades``) and works immediately. Quality
is lower (more false positives, no orientation), but for "find the speaker
in a 16:9 talking-head clip" it's adequate, and the EMA smoothing + 50%
fallback threshold compensates for its noise.

Single-face only in v0.3 — multi-face split-screen is a future feature.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FaceBox:
    x: float  # normalized 0..1
    y: float
    w: float
    h: float
    score: float = 0.0


def _haar_classifier():
    """Lazy-load the bundled OpenCV Haar frontal-face classifier."""
    import cv2
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    return cv2.CascadeClassifier(cascade_path)


def detect_faces(image_path: Path) -> list[dict]:
    """Run OpenCV Haar Frontal Face on a single image. Returns list of dicts.

    Each dict has keys ``x``, ``y``, ``w``, ``h``, ``score`` — all 0..1.
    Score is a heuristic (= w*h normalized) since Haar doesn't provide one.
    """
    import cv2
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(image_path)
    img_h, img_w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clf = _haar_classifier()
    detections = clf.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
    out: list[dict] = []
    for (x, y, w, h) in detections:
        out.append({
            "x": float(x) / img_w,
            "y": float(y) / img_h,
            "w": float(w) / img_w,
            "h": float(h) / img_h,
            "score": float(w * h) / (img_w * img_h),  # area-based heuristic
        })
    return out


def track_face_over_clip(
    video: Path,
    *,
    n_samples: int = 10,
    confidence: float = 0.0,  # Haar has no confidence; use 0
) -> list[tuple[float, FaceBox]] | None:
    """Sample frames, detect faces, return [(timestamp_s, FaceBox), ...] or None.

    Returns None if fewer than 50% of sampled frames contain a face;
    callers should fall back to center crop in that case.
    """
    info = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)],
        check=True, capture_output=True, text=True,
    )
    dur = float(json.loads(info.stdout)["format"]["duration"])
    timestamps = [dur * (i + 0.5) / n_samples for i in range(n_samples)]
    samples: list[tuple[float, FaceBox]] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        for ts in timestamps:
            frame = tmp_p / f"f_{ts:.2f}.jpg"
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-ss", f"{ts:.3f}", "-i", str(video),
                    "-frames:v", "1", str(frame),
                ], check=True)
            except subprocess.CalledProcessError:
                continue
            if not frame.exists():
                continue
            try:
                faces = detect_faces(frame)
            except Exception:
                continue
            if not faces:
                continue
            # Pick the largest face (Haar can give many false positives at small scales)
            best = max(faces, key=lambda f: f["w"] * f["h"])
            if best["score"] < confidence:
                continue
            samples.append((ts, FaceBox(**best)))

    if len(samples) < n_samples * 0.5:
        return None
    return samples


def _ffprobe_video_size(path: Path) -> tuple[int, int]:
    info = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    s = json.loads(info.stdout)["streams"][0]
    return int(s["width"]), int(s["height"])


def reframe_to_vertical(
    input_video: Path,
    output_video: Path,
    *,
    target_w: int = 1080,
    target_h: int = 1920,
    smooth_alpha: float = 0.18,
    n_samples: int = 10,
    confidence: float = 0.0,
    fallback_center: bool = True,
    verbose: bool = False,
) -> dict:
    """Crop a target_w x target_h vertical strip centered on the dominant face.

    Returns ``{'mode': 'face-tracked' | 'center-crop', 'samples': N, 'output': str}``.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not on PATH")
    output_video.parent.mkdir(parents=True, exist_ok=True)

    src_w, src_h = _ffprobe_video_size(input_video)
    # Width of the strip we crop FROM the source (height = full source height).
    # After ``scale=target_w:target_h`` it'll be a target_w x target_h vertical.
    strip_w = max(1, int(round(src_h * target_w / target_h)))
    if strip_w > src_w:
        strip_w = src_w  # source narrower than 9:16 — pillarbox falls out of scale

    samples = track_face_over_clip(input_video, n_samples=n_samples, confidence=confidence)
    if samples is None:
        if not fallback_center:
            raise RuntimeError("face tracking failed and fallback disabled")
        crop_x = (src_w - strip_w) // 2
        x_expr = str(crop_x)
        mode = "center-crop"
        n_used = 0
        if verbose:
            print(f"[reframe] no face track on {input_video.name}; center crop")
    else:
        max_x = src_w - strip_w
        smoothed: float | None = None
        smoothed_xs: list[tuple[float, float]] = []
        for ts, face in samples:
            cx = (face.x + face.w / 2) * src_w
            if smoothed is None:
                smoothed = cx
            else:
                smoothed = smooth_alpha * cx + (1 - smooth_alpha) * smoothed
            crop_x = max(0.0, min(float(max_x), smoothed - strip_w / 2))
            smoothed_xs.append((ts, crop_x))

        if len(smoothed_xs) == 1:
            x_expr = f"{smoothed_xs[0][1]:.0f}"
        else:
            expr = f"{smoothed_xs[-1][1]:.0f}"
            for ts, x in reversed(smoothed_xs[:-1]):
                expr = f"if(lt(t,{ts:.3f}),{x:.0f},{expr})"
            x_expr = expr
        mode = "face-tracked"
        n_used = len(samples)
        if verbose:
            print(f"[reframe] face-tracked, {n_used} samples on {input_video.name}")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(input_video),
        "-filter_complex",
        f"[0:v]crop={strip_w}:{src_h}:x='{x_expr}':y=0,scale={target_w}:{target_h}:flags=lanczos[v]",
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(output_video),
    ]
    subprocess.run(cmd, check=True, capture_output=not verbose)
    return {"mode": mode, "samples": n_used, "output": str(output_video)}
