"""Use Foundry Gemini to pick which transcript sentences to keep."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .asr import SentenceSegment, Transcript


def _ensure_token() -> None:
    token_path = Path.home() / ".secrets/pluto-auth-token-steve-train.txt"
    if "PLUTO_AUTH_TOKEN" not in os.environ and token_path.exists():
        os.environ["PLUTO_AUTH_TOKEN"] = token_path.read_text().strip()


def pick_sentences(
    transcript: Transcript,
    *,
    target_ratio: float = 0.30,
    style_prompt: str = "保留干货、punchline、关键信息；剪掉铺垫、重复、套话",
    model: str = "gemini-2.5-pro",
    verbose: bool = False,
) -> list[int]:
    """Return list of indices into transcript.sentences to keep."""
    _ensure_token()
    from foundry_aws_gateway.llm import get_google_genai
    client = get_google_genai(location="global")

    numbered = []
    total_dur = sum(s.end - s.start for s in transcript.sentences)
    for i, s in enumerate(transcript.sentences):
        numbered.append(f"[{i}] {s.start:6.1f}-{s.end:6.1f}s ({s.end-s.start:4.1f}s) {s.text}")
    transcript_block = "\n".join(numbered)
    target_dur = total_dur * target_ratio

    prompt = f"""You are editing a Chinese marketing/creator video. The full transcript with timestamps is below. Select sentences to KEEP so the result is ~{target_dur:.0f}s (≈{target_ratio*100:.0f}% of original).

Selection criteria: {style_prompt}

Output: a JSON object with key "keep" whose value is the list of sentence indices to keep, in original order. Output ONLY the JSON, nothing else.

Example: {{"keep": [0, 2, 5, 7, 9]}}

Transcript ({len(transcript.sentences)} sentences, {total_dur:.0f}s total):
{transcript_block}
"""

    resp = client.models.generate_content(model=model, contents=prompt)
    raw = resp.text.strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise RuntimeError(f"LLM returned no JSON object:\n{raw[:500]}")
    obj = json.loads(m.group(0))
    keep = obj.get("keep")
    if not isinstance(keep, list):
        raise RuntimeError(f"LLM returned bad shape: {obj}")
    keep = [i for i in keep if 0 <= i < len(transcript.sentences)]
    keep.sort()

    if verbose:
        kept_dur = sum(transcript.sentences[i].end - transcript.sentences[i].start for i in keep)
        print(f"[llm_pick] kept {len(keep)}/{len(transcript.sentences)} sentences "
              f"= {kept_dur:.0f}s of {total_dur:.0f}s ({kept_dur/total_dur*100:.0f}%)")

    return keep


def keeps_to_segments(
    transcript: Transcript,
    keep_indices: list[int],
    *,
    margin_s: float = 0.15,
    merge_gap_s: float = 0.4,
) -> list[tuple[float, float]]:
    """Convert kept sentence indices to (start, end) cut segments with margin + merging."""
    if not keep_indices:
        return []
    segments: list[tuple[float, float]] = []
    for i in keep_indices:
        s = transcript.sentences[i]
        start = max(0.0, s.start - margin_s)
        end = min(transcript.duration, s.end + margin_s)
        segments.append((start, end))
    merged: list[tuple[float, float]] = [segments[0]]
    for start, end in segments[1:]:
        if start - merged[-1][1] <= merge_gap_s:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
