# AGENTS.md

This repo follows the **3-rule agent-native standard**.
Standard: `STANDARD.md` (in this repo) · Canonical: https://github.com/when2buy/agent-native-repo
Format: https://agents.md

---

## The three rules

1. **SPEC** — One file per feature: `docs/design/<feature>.md` with `Goal / Non-goals / Acceptance / Decision`. Acceptance must be runnable. Humans write the Decision; you may draft everything else.

2. **LOOP** — Read spec → write code → run Acceptance → if not green, iterate. Don't ask the human between iterations. Stop after **5** failed attempts on the same task.

3. **GATE** — Stop and `/confirm` only for irreversible actions (see below).

Everything else: just do.

---

## Irreversible (the only times to stop and ask)

- `git push` to `main` / shared branch / `--force` / rebase shared
- Deploy to prod / write to shared S3 / DB schema migration
- Spend > $50 (GPU jobs, paid APIs)
- Send messages outside self-channels (Slack, email)
- Delete files outside `docs/runlog/` or `_cache/`

If unsure → treat as irreversible.

---

## Project context

- **Project**: auto-video-cut
- **Goal**: <one sentence>
- **Stack**: <e.g. Python 3.11, pytest, ruff>
- **Build**: `<cmd>`
- **Test**: `pytest tests/`
- **Lint**: `ruff check .`

## Where things live

- Specs: `docs/design/`
- Past decisions worth remembering: `docs/decisions.md`
- Agent-appended notes (you write here, humans curate periodically): `docs/learnings.md`

## Domain-specific guides

(Add only as needed. Empty by default.)

- ML training: <link>
- Frontend demo: <link>
- Deploy: <link>
