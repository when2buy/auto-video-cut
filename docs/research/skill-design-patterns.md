# Skill Design Patterns — what to steal for `auto-video-cut`

**Date:** 2026-05-29 · **Audience:** the agent that's going to write the v0.3 SKILL.md tonight.
**Source material:** 12 skills (10 read in full, 2 spot-checked). Stars verified via `gh api`.

---

## 1. TL;DR — five things to do right now

1. **Frontmatter = `name` + `description` only.** `description` is *strictly* "use when..." triggers + concrete phrases (English + 中文). No workflow summary in the frontmatter — that's the one mistake `superpowers/writing-skills` calls out by name (lines 150–172 of its SKILL.md). `clipify` and `whisper-transcribe` get this right; copy their pattern verbatim.
2. **One SKILL.md, ≤200 lines.** Anthropic's official guideline is ≤500 (`skill-creator/SKILL.md`). The best skills I read are 80–170. Going past 250 is a smell — anything bigger goes to a `references/<topic>.md` file Claude reads on demand.
3. **Scripts/, not inline Python.** Heavy logic lives in `scripts/*.py` invoked via Bash. SKILL.md tells Claude *which script and why*, not *how to compute*. `clipify` (4 scripts, 167-line SKILL.md) and Anthropic's `pdf` skill (forms.md, reference.md) are the templates. **This is exactly the split we need: `transcribe.py` / `pick.py` / `reframe.py` / `caption.py` as scripts, SKILL.md as the conductor.**
4. **The "Pitfalls" section is the differentiator.** Every skill that "feels professional" has a final section listing 5–8 traps and lessons-from-prior-runs (`clipify` lines 160–167, `whisper-transcribe` Troubleshooting table). This is where the skill *earns its keep* over a generic LLM doing the same task ad-hoc.
5. **Default behavior > options menu.** `whisper-transcribe`'s "Default is the right answer 99% of the time" + only-add-flags-when-asked pattern beats clipify's "ask the user 4 times" pattern for an overnight build. Make Claude run the happy path end-to-end without questions, only ask if user explicitly customized something.

**Single biggest insight:** the skills that ship value aren't the longest, they're the ones that **encode hard-won negative knowledge** (what NOT to do). Anyone can write the happy path. The "don't run whisper on the full 90-min source if a 20s clip suffices" line in clipify is worth more than the next 100 lines of ffmpeg recipes.

---

## 2. Inventory of skills surveyed

Stars verified `2026-05-29` via `gh api repos/...`. Line counts via `wc -l SKILL.md`.

| Skill | Repo / path | Stars | SKILL.md LOC | What's good | What to steal |
|---|---|---|---|---|---|
| **clipify** | `louisedesadeleer/clipify` | **393** | 167 | Direct competitor; 4 scripts + tight 6-step workflow; opinionated ffmpeg flags; "don't over-tune ROIs" pitfalls | Step-numbered workflow, scripts/ split, Pitfalls section, default file conventions (`/tmp/clipify/`, `<src>/clipify_out/`) |
| **report-skill** | `oyzh888/report-skill` | 1 (Steve's bar) | 105 | "engineered like an SDK" — install / use / extend split; 4-verb channel ABI; templates as data files | Three-section structure (Install / Use / Extend), CLI tool + skill-doc duality |
| **agent-native-repo** | local (Steve, no public repo) | — | 110 | Two modes (`init` / `audit`); explicit "When to use / Don't trigger on"; STANDARD.md as canonical reference | Anti-trigger list (rare, valuable); referencing a sibling canonical doc |
| **whisper-transcribe** | local (Steve) | — | 123 | "Default is right 99%"; performance table with real numbers; troubleshooting table; explicit script contract w/ exit codes | Performance benchmarks in-doc, exit-code contract, decision matrix for flags |
| **paper-figures** | local (Steve) | — | 56 | Tightest skill that still has teeth — decision tree table + hard style rules + "When NOT to use" | Decision-tree table format; 3-line "When NOT to use" |
| **citation-check** | `when2buy/citation-check` (mirror) | local | 114 | Concrete failure mode (tau-bench / TextArena) sells the skill in one sentence | Lead with the disaster you prevent |
| **deploy-service** | local (Steve) | — | 144 | "Currently deployed" inventory table; security policy section; decision tree | Inventory section if skill manages persistent state |
| **web-qa** | local (Steve) | — | 157 | Inline Python recipes (3 functions); explicit "after creating HTML, screenshot it" trigger | Code-as-recipe pattern when scripts/ overhead isn't worth it |
| **pluto-job-manage** | local (Steve) | — | 255 | At the long end — split into `pluto_client.py` (SDK) + `manage.py` (CLI) + `toolkit/` (frozen) | Versioning frozen entry-points when stability matters |
| **superpowers/writing-skills** | `obra/superpowers` | 211k* | 655 | Meta-skill for skill-writing — TDD-for-skills; CSO (Claude Search Optimization) section | The CSO concept (lines 140–197) — `description` field IS the trigger |
| **anthropic/skills/pdf** | `anthropics/skills` | 143k* | ~250 SKILL.md + 2 ref files | Official Anthropic pattern — SKILL.md + `forms.md` + `reference.md`; "Quick Start" before everything | Three-tier doc split: SKILL → reference → forms |
| **anthropic/skills/skill-creator** | `anthropics/skills` | 143k* | ~700 | Anthropic's own meta-skill — explicit "progressive disclosure" model; "anatomy of a skill" diagram | Progressive disclosure framing (metadata → body → bundled) |

`*` Anthropic & superpowers stars look anomalously high for repos this young; I report what `gh api` returned. If treating as a tiebreaker, weight clipify/report-skill (working production skills) over star counts.

---

## 3. Five patterns I should adopt

### Pattern A — Frontmatter as a trigger contract, not a TOC

**Steal from:** `clipify/SKILL.md` line 3, `whisper-transcribe/SKILL.md` line 3.

```yaml
---
name: auto-video-cut
description: Auto-edit a long video into social-ready clips — transcribe, AI-pick highlights, reframe 16:9→9:16 with face-pan, burn captions, output multiple formats. Use when the user says "auto-cut this video", "make clips from this", "剪个短视频", "make shorts", or pastes a video file path expecting clips back. Also triggers on "auto edit", "highlight reel", "TikTok 版本", "自动剪辑".
---
```

Notice three things:
- Description is **two sentences**: what it does (one line) + when to use (the trigger phrases).
- **Both languages** in trigger phrases — Steve's environment is bilingual; Claude's matcher rewards explicit zh+en triggers.
- **No workflow** ("then it does X, then Y"). `superpowers/writing-skills` lines 150–172 documents that workflow-in-description causes Claude to skip reading the SKILL body.

Anti-version (what NOT to write — this is exactly the trap `writing-skills` calls out):
```yaml
description: Use this skill to auto-cut videos. First it transcribes with Whisper, then picks highlights with an LLM, then reframes to 9:16, then adds captions.
```

### Pattern B — Workflow as numbered shell-runnable steps, scripts/ for the math

**Steal from:** `clipify/SKILL.md` Step 1–6 structure; Anthropic `pdf/SKILL.md` "Quick Start" + Python Libraries split.

The SKILL.md should have, in order:

```
## Inputs           (3 bullets, what user provides + defaults)
## Tooling          (which CLI tools, which models — version-locked)
## Workflow
   ### Step 1 — Transcribe       (5–10 lines bash + which script)
   ### Step 2 — Pick highlights  (5–10 lines bash, points at scripts/pick.py)
   ### Step 3 — Reframe           ...
   ### Step 4 — Caption          ...
   ### Step 5 — Deliver           (file paths + report-skill URL)
## Pitfalls         (the 6–10 things that go wrong)
```

`clipify` lines 31–157 is the gold-standard execution of this. The agent reads the bash, copies it, edits values. **No prose explaining "why ffmpeg".** It just runs. All the heavy logic — analyze.py, build_pan.py, build_ass.py — sits in `scripts/` (clipify lines 22–26 maps them).

**For our project:** scripts should be `scripts/asr.py`, `scripts/pick.py`, `scripts/reframe.py`, `scripts/caption.py`. SKILL.md says "run `python3 <skill-dir>/scripts/pick.py /tmp/avc/transcript.json --topk 5 > /tmp/avc/picks.json`" — that's the level of detail.

### Pattern C — A "Pitfalls" / "Lessons from prior runs" closing section

**Steal from:** `clipify/SKILL.md` lines 160–167 (literally copy this format).

```markdown
## Pitfalls (lessons from prior runs — don't repeat)

- **Don't over-tune ROIs.** Two iterations max...
- **Watch out for scene cuts inside a clip.** Run `ffmpeg ... showinfo`...
- **Source resolution matters.** If 4K, downscale to 1920×1080 first...
- **Don't run whisper on the full feature-length source if a short clip suffices.**
- **State the plan in one line, then act.** Don't narrate every iteration.
```

This pattern takes ~60 seconds to write per pitfall and saves Claude 5–10 minutes of wrong-direction every run. It's the highest-ROI section of any skill. **Plan to fill 5–8 pitfalls during the overnight build's first complete run-through** (literally write down what went wrong in iteration 1 → put it here so iteration 2 doesn't repeat).

### Pattern D — Default-driven workflow, options gated behind explicit user ask

**Steal from:** `whisper-transcribe/SKILL.md` "Agent guidance" section (lines 80–93).

```markdown
**Default is the right answer 99% of the time.** Just run:
\`\`\`bash
~/.claude/skills/auto-video-cut/scripts/run.sh <video>
\`\`\`

Only add flags when the user explicitly asks:
- `--format 9:16` → user says "vertical", "TikTok", "Reels", "竖版"
- `--captions opus` → user explicitly picks a style; default is opus
- `--topk N` → user asks for N clips specifically
```

Compare to `clipify` Step 3 (asks the user about format) and Step 4 (asks again about pan vs split-screen) and Step 5 (asks again about subtitle style). **Three blocking questions per run is too many for an overnight headless pipeline.** Pick sane defaults, mention them in one line, run end-to-end. Only branch if user explicitly disagrees in their initial ask.

### Pattern E — Output is files + a report-skill URL, not a wall of text

**Steal from:** `report-skill/SKILL.md` lines 65–69 + `agent-native-repo/AGENTS.md` rule 4 (Steve's own AGENTS.md in this repo already mandates this).

The skill's final step (Step 5/6) must produce two things:

1. **Files on disk** — clips at `<src>/auto_video_cut_out/clip_001.mp4`, transcript at `transcript.json`, picks at `picks.json`. Discoverable, git-able if user wants.
2. **A `report publish` URL** — a self-contained HTML showing `compare-grid` of the N candidate clips with thumbnails + transcript snippets + WHY-it-was-picked + "open in finder" links.

```markdown
### Step 6 — Deliver

1. Save outputs to `<source_dir>/auto_video_cut_out/`
2. Generate review HTML:
   ```bash
   report new compare-grid --out reports/$(date +%Y%m%d)-clips.html
   # fill in JSON data block with clip thumbnails, transcripts, scores
   report publish reports/<file>.html
   ```
3. Reply with: URL first, file paths second.
```

This is what makes the deliverable feel professional vs. "here's a folder, look through it yourself." Steve's `identity.md` rule explicitly demands this: "重要更新必须附链接 ... Demo 链接 — 网站 URL / HTML viz / 截图".

---

## 4. Three anti-patterns I should avoid

### Anti-pattern 1 — Workflow summary in `description`

Documented in `superpowers/writing-skills` lines 150–172 with a real failure: Claude did 1 review instead of 2 because the description compressed "between tasks" into pseudo-workflow. Don't write `description: ... First transcribe, then pick, then reframe.` Claude follows the description's compressed workflow and skips the SKILL.md body.

### Anti-pattern 2 — 500+ line SKILL.md with everything inline

`superpowers/writing-skills` itself is 655 lines — defensible because it teaches, not executes. For task skills, cross 250 → split. Anthropic's `pdf` does this: 250-line SKILL + 470-line `reference.md` + 330-line `forms.md`. For us: FFmpeg recipes, LLM prompts, ASS spec → `references/`, not SKILL.md.

### Anti-pattern 3 — Asking the user N times mid-run

`clipify` asks 3–4 questions per execution (format, pan-vs-split, caption style, ROI confirm). Fine for interactive use; kills overnight headless loops. **Fix:** sane defaults + one line at start: "running with 5 clips / 9:16 / opus — say override now". One ask at start, none in the middle.

---

## 5. Verdict on existing skills

**Should we use clipify as a sub-skill?** No, but **fork its scripts/**.

Reasoning:
- Clipify's *workflow* is wrong for us: it's interactive (3+ user prompts), single-clip-at-a-time, Mac-specific (`videotoolbox` hwaccel). We want headless, batch, Linux/CUDA.
- Clipify's *scripts* are excellent and we should fork them with attribution:
  - `analyze.py` (80 LOC) — speaker timeline from ROI motion. **Take as-is.**
  - `build_pan.py` (18 LOC) — ffmpeg crop expression generator. **Take as-is.**
  - `build_ass.py` (73 LOC) — opus/karaoke/minimal ASS captions. **Take as-is, this is gold for caption styling.**
  - `audio_align.py` (27 LOC) — sub-clip offset finder. **Maybe useful for source-matching, optional.**

Action: `cp /home/colligo/.claude/skills/clipify/scripts/*.py src/avc/scripts/` and credit in `docs/decisions.md`. License is MIT (verified via `gh api`).

**Don't wrap clipify or shell out to it.** Their face-detection-by-frame-differencing assumption (camera static within clip) holds for our use case but the install pathway (clone-into-`~/.claude/skills/`) and the prompt-asking workflow would conflict with ours.

**Don't rewrite the scripts from scratch tonight.** Steve has 10 hours; reinventing build_pan.py is hour 3 wasted.

---

## 6. Recommended skill architecture for v0.3

**One skill, multi-script.** Not multiple skills. Reasoning: the four stages (ASR → pick → reframe → caption) share state (transcript JSON, segment timeline, video paths) and *always* run together. Splitting into 4 skills means every invocation re-reads 4 SKILL.md files; that's pure overhead.

**File layout:**

```
auto-video-cut/                      (this repo)
├── SKILL.md                         ≤180 lines, the conductor
├── README.md                        for humans, not for Claude
├── scripts/
│   ├── run.sh                       full pipeline wrapper, sane defaults
│   ├── asr.py                       wraps whisper-transcribe skill or whisperx directly
│   ├── pick.py                      LLM call (Gemini via gemini-foundry, fallback Claude)
│   ├── reframe.py                   ffmpeg crop/scale; calls build_pan.py
│   ├── caption.py                   wraps build_ass.py + ffmpeg burn-in
│   └── _vendored/                   (forked from clipify, MIT)
│       ├── analyze.py
│       ├── build_pan.py
│       ├── build_ass.py
│       └── LICENSE-clipify
├── references/
│   ├── ffmpeg-recipes.md            full filter_complex library
│   ├── llm-prompts.md               highlight-picking prompt templates
│   └── caption-styles.md            opus/karaoke/minimal ASS specs
└── tests/
    └── test_pipeline_e2e.py         one 30s clip → asserts 3+ outputs exist
```

**SKILL.md skeleton (target ≤180 lines):**

```markdown
---
name: auto-video-cut
description: <Pattern A>
---

# Auto-Video-Cut

One-line pitch.

## Inputs (5 lines)
## Tooling (5 lines — whisperx, ffmpeg, gemini-foundry, scripts/)
## Defaults (3 lines — "9:16, 5 clips, opus captions; override at start")

## Workflow
### Step 1 — Transcribe (10 lines)
### Step 2 — Pick highlights (10 lines)
### Step 3 — Reframe each clip (15 lines)
### Step 4 — Burn captions (10 lines)
### Step 5 — Deliver (report-skill compare-grid + file paths)

## Pitfalls (8 bullets, fill during first dry-run)

## References
- Heavy ffmpeg recipes: references/ffmpeg-recipes.md
- LLM prompts: references/llm-prompts.md
- Caption styles: references/caption-styles.md
```

**Where the heavy stuff lives:**
- **In SKILL.md:** workflow, sane defaults, what to call when
- **In scripts/:** all Python logic (the parts Claude shouldn't be writing fresh each time)
- **In references/:** ffmpeg recipes, LLM prompts, ASS spec — large reference Claude reads only when a step deviates from happy path
- **In tests/:** one e2e test that runs in CI on a checked-in 10s sample, so the auto-loop in `AGENTS.md` rule 2 (LOOP) actually has something to grade against

**Testing:** drop a 10s sample video in `tests/fixtures/sample.mp4` (gitignored, downloaded by setup script). Test asserts: `auto_video_cut_out/clip_001.mp4` exists, has audio, is 9:16 aspect, has burned captions (frame-pick + OCR sanity check or just file size > N bytes). This satisfies SPEC's "Acceptance must be runnable" rule.

**One opinionated call:** **don't put the LLM provider behind config.** Hardcode Gemini via `gemini-foundry` skill as the default picker. If user wants Claude or GPT they say so. Multi-provider abstractions you build at hour 4 will eat hours 5–7 and won't ship.

---

## Sources

All under `/home/colligo/.claude/skills/<name>/SKILL.md` unless noted: clipify (167 LOC + scripts/*.py full), report-skill (105), agent-native-repo (110), whisper-transcribe (123), web-qa (157), deploy-service (144), paper-figures (56), citation-check (114), pluto-job-manage (255, first 80). Plugin: `superpowers/skills/{writing-skills (655, lines 1–200), test-driven-development (371, first 120), brainstorming (164, first 80)}/SKILL.md`. Anthropic official (`github.com/anthropics/skills`): pdf, skill-creator, webapp-testing — first 60–120 lines each via raw.githubusercontent.com.
