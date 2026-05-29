"""Template-driven semantic remix.

Where v0.2/v0.3 ``pick_sentences`` keeps a contiguous-ish set of sentences
"in order", remix.py picks **and reorders** them according to a creative
template.

Pipeline:
    transcribe → remix_with_template (LLM) → indices_to_ordered_segments
    → extract_and_concat → optional reframe → optional captions

The LLM is asked to (a) classify each sentence's narrative role, then (b)
pick + order indices to fit the template. Output preserves LLM order
(non-chronological allowed) — ffmpeg concat handles arbitrary segment order.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from .asr import Transcript


def _ensure_token() -> None:
    token_path = Path.home() / ".secrets/pluto-auth-token-steve-train.txt"
    if "PLUTO_AUTH_TOKEN" not in os.environ and token_path.exists():
        os.environ["PLUTO_AUTH_TOKEN"] = token_path.read_text().strip()


# ---------------------------------------------------------------------------
# Templates registry — each is a dict with goal/format/example for the LLM.

@dataclass
class RemixTemplate:
    name: str
    description: str          # human-readable, shown in demo
    target_duration_s: float  # roughly how long the output should be
    instructions: str         # the LLM prompt body (after the transcript)


TEMPLATES: dict[str, RemixTemplate] = {
    "viral_hook": RemixTemplate(
        name="viral_hook",
        description="Cold-open with the strongest line, then setup, then payoff. Optimized for TikTok/Reels.",
        target_duration_s=35.0,
        instructions="""You are an expert short-form video editor. From the transcript, build a 30-40 second VIRAL HOOK clip:

1. **Open** (3-6s): the single strongest, most surprising, or most provocative sentence. The hook. Often a punchline, statistic, or contrarian claim. Pick 1-2 sentences.
2. **Setup** (15-20s): briefly establish context for the hook. 3-5 sentences from earlier in the talk. Just enough to make the hook understandable.
3. **Payoff** (10-15s): the resolution, biggest laugh, or "and that's why" moment. 2-4 sentences.

OUTPUT order: [hook indices] + [setup indices] + [payoff indices].

The output WILL be non-chronological. That's intended.
""",
    ),
    "top3": RemixTemplate(
        name="top3",
        description="Top-3 punchlines, ranked by impact (not original timeline). Best moments only.",
        target_duration_s=75.0,
        instructions="""From the transcript, build a TOP-3 HIGHLIGHTS reel ~75 seconds long:

Pick the three single best moments — each 15-25 seconds long. Each moment should be self-contained: a punchline + just enough setup to land. Order them BY IMPACT (strongest first), not by time-in-source.

Each moment is 2-5 sentences from the transcript. Pick sentences that flow into each other naturally — adjacent in the source.

OUTPUT order: [moment 1 indices, strongest] + [moment 2 indices] + [moment 3 indices].
""",
    ),
    "thesis": RemixTemplate(
        name="thesis",
        description="Speaker's main argument distilled to ~50s. One thesis statement + one supporting example.",
        target_duration_s=50.0,
        instructions="""From the transcript, build a THESIS clip ~50 seconds long:

1. **Thesis** (15-20s): the speaker's central claim — what they actually want the audience to remember. Pick 2-4 sentences that state it most clearly. May be from anywhere in the talk.
2. **One example** (25-30s): the single best illustration of that thesis. A story, statistic, or vivid case. 4-7 sentences, ideally adjacent in the source.

OUTPUT order: [thesis indices] + [example indices].

Skip jokes, asides, and tangents. This format is "what was the talk REALLY about". Order is by argument flow, not original timeline.
""",
    ),
    "trailer": RemixTemplate(
        name="trailer",
        description="Movie-trailer style: cryptic teaser from late → setup → climax cut just before resolution.",
        target_duration_s=35.0,
        instructions="""From the transcript, build a 30-40 second TRAILER clip in three beats:

1. **Cold tease** (5-8s): a single cryptic line from the LATE half of the talk that sounds intriguing without context. 1-2 sentences. Make the viewer think "what does that mean?"
2. **Setup montage** (15-20s): rapid-fire 4-6 short sentences from EARLIER, setting the world. Energy.
3. **Climax cut-off** (8-12s): build into the biggest emotional/intellectual moment but CUT before the resolution. 2-4 sentences. Leave the viewer hanging.

OUTPUT order: [tease indices] + [setup indices] + [climax indices].
""",
    ),
}


# ---------------------------------------------------------------------------

@dataclass
class RemixResult:
    template: str
    keep_indices: list[int]   # in OUTPUT order (non-chronological allowed)
    rationale: str            # short LLM explanation, "why this cut"


def remix_with_template(
    transcript: Transcript,
    template: str,
    *,
    model: str = "gemini-2.5-pro",
    verbose: bool = False,
) -> RemixResult:
    """Ask Gemini to classify + reorder sentences per the named template.

    Returns indices in OUTPUT ORDER (may be non-chronological).
    """
    _ensure_token()
    from foundry_aws_gateway.llm import get_google_genai

    if template not in TEMPLATES:
        raise ValueError(f"Unknown template '{template}'. Available: {list(TEMPLATES)}")
    tpl = TEMPLATES[template]

    total_dur = sum(s.end - s.start for s in transcript.sentences)
    numbered = []
    for i, s in enumerate(transcript.sentences):
        numbered.append(f"[{i}] {s.start:6.1f}-{s.end:6.1f}s ({s.end-s.start:4.1f}s) {s.text}")
    transcript_block = "\n".join(numbered)

    prompt = f"""You are remixing a long video transcript into a short clip following a specific TEMPLATE.

## Template: {tpl.name}

{tpl.instructions}

## Target

- Output duration: ~{tpl.target_duration_s:.0f} seconds total
- Source duration: {total_dur:.0f} seconds, {len(transcript.sentences)} sentences

## Output format (strict)

Return JSON ONLY, with two keys:
- "keep" — list of sentence indices in the order they should appear in the OUTPUT (non-chronological allowed!)
- "rationale" — 2-3 sentences explaining the editorial choice (what hook, why this order)

Example (only the shape, not real indices):
{{"keep": [42, 3, 4, 5, 8, 9, 10, 51, 52, 53], "rationale": "Opens with [42] because it's the strongest punchline. Then [3-10] establishes the setup the audience needs. Closes with [51-53], the payoff line."}}

## Transcript ({len(transcript.sentences)} sentences)

{transcript_block}
"""

    client = get_google_genai(location="global")
    resp = client.models.generate_content(model=model, contents=prompt)
    raw = resp.text.strip()

    # Tolerate ```json fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise RuntimeError(f"LLM returned no JSON object:\n{raw[:500]}")
    obj = json.loads(m.group(0))
    keep = obj.get("keep")
    rationale = obj.get("rationale", "").strip()
    if not isinstance(keep, list) or not keep:
        raise RuntimeError(f"LLM returned bad shape: {obj}")
    keep = [int(i) for i in keep if isinstance(i, (int, str)) and str(i).isdigit()
            and 0 <= int(i) < len(transcript.sentences)]
    if not keep:
        raise RuntimeError("LLM returned no valid indices after filtering")

    if verbose:
        kept_dur = sum(
            transcript.sentences[i].end - transcript.sentences[i].start for i in keep
        )
        print(f"[remix] template={tpl.name} kept {len(keep)} sentences "
              f"= {kept_dur:.0f}s of {total_dur:.0f}s")
        print(f"[remix] indices in output order: {keep[:20]}{'...' if len(keep) > 20 else ''}")
        print(f"[remix] rationale: {rationale}")

    return RemixResult(template=tpl.name, keep_indices=keep, rationale=rationale)


def indices_to_ordered_segments(
    transcript: Transcript,
    keep_indices: list[int],
    *,
    margin_s: float = 0.15,
) -> list[tuple[float, float]]:
    """Convert ordered keep-indices to (start, end) segments in OUTPUT ORDER.

    Crucially, this does NOT sort or merge — preserves the LLM's intended order.
    Adjacent indices in the input order are merged (because they're contiguous
    in source AND output, ffmpeg concat handles them as one segment).
    Non-adjacent jumps stay as separate segments.
    """
    if not keep_indices:
        return []
    segments: list[tuple[float, float]] = []
    cur_idx = keep_indices[0]
    cur_start = max(0.0, transcript.sentences[cur_idx].start - margin_s)
    cur_end = min(transcript.duration, transcript.sentences[cur_idx].end + margin_s)
    for nxt in keep_indices[1:]:
        s = transcript.sentences[nxt]
        nxt_start = max(0.0, s.start - margin_s)
        nxt_end = min(transcript.duration, s.end + margin_s)
        # Merge only if next index is the immediate successor in SOURCE
        if nxt == cur_idx + 1 and nxt_start <= cur_end + 0.05:
            cur_end = max(cur_end, nxt_end)
            cur_idx = nxt
        else:
            segments.append((cur_start, cur_end))
            cur_start, cur_end, cur_idx = nxt_start, nxt_end, nxt
    segments.append((cur_start, cur_end))
    return segments
