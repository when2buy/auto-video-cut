"""Burned word-by-word captions using PIL + ffmpeg overlay.

Why PIL+overlay and not ASS/libass: this pod's ffmpeg build (6.1.1, custom)
ships without libass — neither ``ass`` nor ``subtitles`` filter is available.
Rendering captions to transparent PNGs and overlaying via the ``overlay``
filter (which IS available) gives us word-by-word burned captions in any
language and any font, with no libass dependency.

API mirrors the originally-planned ASS-based approach so callers stay simple:
- ``build_caption_assets(transcript, work_dir, ...)`` — emits PNGs + a JSON timing manifest
- ``burn_captions(input_video, manifest, output_video)`` — runs the ffmpeg overlay graph

Performance: ~0.005s/word in PIL (negligible) + ffmpeg encode time (~realtime
on libx264 ultrafast). For a 90s clip with 200 words: ~1s PIL, ~3-5s ffmpeg.

The two functions also accept a ``style`` preset and a ``play_w`` / ``play_h``
hint that determines font size + position.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from .asr import Transcript

# ---------------------------------------------------------------------------
# Style presets

# Path discovery — try multiple system fonts; fall back to PIL default.
_FONT_CANDIDATES = {
    "latin-bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/lato/Lato-Black.ttf",
        "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    ],
    "cjk": [
        # Verified present on this pod (`fc-list :lang=zh`) — Droid Sans Fallback
        # has full CJK glyph coverage including 4 BMP CJK Unified Ideographs blocks.
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/source-han-sans/SourceHanSans-Bold.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # last-ditch (no CJK glyphs)
    ],
}

PRESETS: dict[str, dict] = {
    # name              :  font_key,  size, fill (RGB),         stroke (RGB),     stroke_w, y_frac, chunk
    # font_key="auto" means: per-chunk, pick Latin font if all-ASCII, CJK font if any CJK chars.
    # Use this for any preset that may see mixed-language transcripts.
    "opus":     dict(font_key="auto", size=64, fill=(255, 255, 0),    stroke=(0, 0, 0),     stroke_w=4, y_frac=0.78, chunk=3),
    "opus-cn":  dict(font_key="auto", size=52, fill=(255, 255, 0),    stroke=(0, 0, 0),     stroke_w=3, y_frac=0.80, chunk=2),
    "minimal":  dict(font_key="auto", size=44, fill=(255, 255, 255),  stroke=(0, 0, 0),     stroke_w=3, y_frac=0.85, chunk=4),
    "karaoke":  dict(font_key="auto", size=68, fill=(0, 255, 0),      stroke=(0, 0, 0),     stroke_w=5, y_frac=0.78, chunk=3),
}


def _has_cjk(text: str) -> bool:
    """Return True if any character is in a CJK Unicode block (U+4E00..U+9FFF + extras)."""
    for ch in text:
        cp = ord(ch)
        if (
            0x3000 <= cp <= 0x9FFF or       # CJK Symbols, Hiragana, Katakana, CJK Unified
            0xAC00 <= cp <= 0xD7AF or       # Hangul Syllables
            0xF900 <= cp <= 0xFAFF or       # CJK Compatibility Ideographs
            0xFF00 <= cp <= 0xFFEF or       # Halfwidth/Fullwidth
            0x20000 <= cp <= 0x2FFFF        # CJK Extension B+
        ):
            return True
    return False


def _find_font(font_key: str, size: int):
    """Return a PIL ImageFont, or PIL default if all candidates fail."""
    from PIL import ImageFont
    for path in _FONT_CANDIDATES.get(font_key, []):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Asset builder

@dataclass
class CaptionAsset:
    png_path: str
    start: float
    end: float
    x: int
    y: int


def build_caption_assets(
    transcript: Transcript,
    work_dir: Path,
    *,
    style: str = "opus",
    play_w: int = 1080,
    play_h: int = 1920,
    chunk_size: int | None = None,
) -> list[CaptionAsset]:
    """Render PNGs for each chunk of words. Returns timing manifest.

    Each chunk produces N PNGs (one per word in the chunk) showing the chunk
    text with the current word highlighted. Chunks roll word-by-word.
    """
    from PIL import Image, ImageDraw

    P = PRESETS.get(style, PRESETS["opus"])
    if chunk_size is None:
        chunk_size = P.get("chunk", 3)
    # Pre-load both fonts; we'll pick per chunk if font_key=="auto"
    latin_font = _find_font("latin-bold", P["size"])
    cjk_font = _find_font("cjk", P["size"])
    if P["font_key"] == "auto":
        font = None  # picked per chunk below
    else:
        font = _find_font(P["font_key"], P["size"])

    if not any(s.words for s in transcript.sentences):
        raise ValueError(
            "Transcript lacks word-level timestamps. Re-call transcribe(..., word_timestamps=True)."
        )

    # Collect words (skip empties)
    words: list[dict] = []
    for s in transcript.sentences:
        if not s.words:
            continue
        for w in s.words:
            text = (w.text or "").strip()
            if not text:
                continue
            words.append({"start": w.start, "end": w.end, "text": text})

    if not words:
        raise ValueError("Transcript has sentences but no usable word timestamps.")

    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    work_dir.mkdir(parents=True, exist_ok=True)

    fill = (*P["fill"], 255)
    stroke_fill = (*P["stroke"], 255)
    white = (255, 255, 255, 255)

    assets: list[CaptionAsset] = []
    for ci, chunk in enumerate(chunks):
        chunk_text = " ".join(w["text"] for w in chunk)

        # Pick font per chunk if "auto" — CJK font if chunk has any CJK character,
        # else Latin. Mixed chunks (rare) use CJK font (which on Droid Fallback
        # has no Latin glyphs, but mixed cases are rare enough we accept the trade
        # for now; future improvement: use a font with both like Noto Sans CJK).
        chunk_font = font
        if chunk_font is None:
            chunk_font = cjk_font if _has_cjk(chunk_text) else latin_font

        # Determine total chunk text width (PIL has the actual font metrics)
        tmp_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        tmp_d = ImageDraw.Draw(tmp_img)
        bbox = tmp_d.textbbox((0, 0), chunk_text, font=chunk_font, stroke_width=P["stroke_w"])
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        pad = 24
        png_w = min(play_w - 80, text_w + pad * 2)
        png_h = text_h + pad * 2
        tx = (png_w - text_w) // 2 - bbox[0]
        ty = (png_h - text_h) // 2 - bbox[1]

        for wi, active_word in enumerate(chunk):
            img = Image.new("RGBA", (png_w, png_h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            x_cursor = tx
            for word in chunk:
                w_text = word["text"]
                w_bbox = d.textbbox((x_cursor, ty), w_text, font=chunk_font, stroke_width=P["stroke_w"])
                w_color = fill if word is active_word else white
                d.text(
                    (x_cursor, ty), w_text, font=chunk_font,
                    fill=w_color,
                    stroke_width=P["stroke_w"], stroke_fill=stroke_fill,
                )
                x_cursor = w_bbox[2] + (chunk_font.size // 4)

            png_path = work_dir / f"cap_{ci:04d}_{wi:02d}.png"
            img.save(png_path, "PNG", optimize=True)

            # Time window: this image visible from this word's start to next word's start
            seg_start = float(active_word["start"])
            if wi + 1 < len(chunk):
                seg_end = float(chunk[wi + 1]["start"])
            else:
                seg_end = float(active_word["end"])
            if seg_end <= seg_start:
                seg_end = seg_start + 0.05

            x = (play_w - png_w) // 2
            y = int(play_h * P["y_frac"]) - png_h // 2
            assets.append(CaptionAsset(
                png_path=str(png_path),
                start=seg_start, end=seg_end,
                x=x, y=y,
            ))

    return assets


# ---------------------------------------------------------------------------
# ffmpeg burn

def burn_captions(
    input_video: Path,
    assets: list[CaptionAsset],
    output_video: Path,
    *,
    verbose: bool = False,
) -> Path:
    """Render captions onto input_video via ffmpeg overlay.

    Builds a single -filter_complex with one overlay per asset. ffmpeg handles
    hundreds of overlays without trouble; if assets > 1000, consider batching.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not on PATH")
    output_video.parent.mkdir(parents=True, exist_ok=True)
    if not assets:
        raise ValueError("no caption assets — nothing to burn")

    # Build inputs: -i video -i png1 -i png2 ...
    cmd: list[str] = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(input_video)]
    for a in assets:
        cmd += ["-i", a.png_path]

    # Build filter_complex: chain overlays
    parts: list[str] = []
    prev = "0:v"
    for i, a in enumerate(assets, start=1):
        out_label = f"v{i}" if i < len(assets) else "vout"
        parts.append(
            f"[{prev}][{i}:v]overlay={a.x}:{a.y}:enable='between(t,{a.start:.3f},{a.end:.3f})'[{out_label}]"
        )
        prev = out_label

    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "[vout]",
        "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_video),
    ]
    if verbose:
        print(f"[burn_captions] {len(assets)} overlays, encoding…")
    subprocess.run(cmd, check=True, capture_output=not verbose)
    return output_video


# ---------------------------------------------------------------------------
# Convenience wrapper for callers

def caption_video(
    input_video: Path,
    transcript: Transcript,
    output_video: Path,
    *,
    style: str = "opus",
    play_w: int | None = None,
    play_h: int | None = None,
    work_dir: Path | None = None,
    verbose: bool = False,
) -> Path:
    """One-call: build assets, then burn.

    If play_w/play_h not given, infer from input_video via ffprobe.
    """
    if play_w is None or play_h is None:
        info = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(input_video)],
            check=True, capture_output=True, text=True,
        )
        s = json.loads(info.stdout)["streams"][0]
        play_w = play_w or s["width"]
        play_h = play_h or s["height"]

    if work_dir is None:
        work_dir = output_video.parent / f"{output_video.stem}.captions"
    work_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"[caption_video] target frame: {play_w}x{play_h}, style={style}")

    assets = build_caption_assets(
        transcript, work_dir, style=style, play_w=play_w, play_h=play_h,
    )
    if verbose:
        print(f"[caption_video] generated {len(assets)} caption frames")

    # Persist manifest for debugging
    manifest = work_dir / "manifest.json"
    manifest.write_text(json.dumps([asdict(a) for a in assets], indent=2))

    return burn_captions(input_video, assets, output_video, verbose=verbose)
