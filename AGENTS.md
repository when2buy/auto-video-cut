# AGENTS.md

This repo follows the **4-rule agent-native standard**.
Standard: `STANDARD.md` (in this repo) · Canonical: https://github.com/when2buy/agent-native-repo
Format: https://agents.md

---

## The four rules

1. **SPEC** — One file per feature: `docs/design/<feature>.md` with `Goal / Non-goals / Acceptance / Decision`. Acceptance must be runnable. Humans write the Decision; you may draft everything else.

2. **LOOP** — Read spec → write code → run Acceptance → if not green, iterate. Don't ask the human between iterations. Stop after **5** failed attempts on the same task.

3. **GATE** — Stop and `/confirm` only for irreversible actions (see below).

4. **REPORT** — Every human-checkpoint produces a `report-skill` URL, not a Markdown wall. Reply with the URL **first**, file paths second. Triggers: research done → `compare-grid`; spec drafted → `case-study`; feature shipped → `metrics-board`. Commands: `report new <tpl> --out reports/<date>-<slug>.html` then `report publish <file>`.

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
- **Reports for humans (URLs)**: `reports/<YYYY-MM-DD>-<slug>.html` — produced via `report` CLI. Each report logged in `reports/INDEX.md` with URL + 1-line summary.

## Domain-specific guides

(Add only as needed. Empty by default.)

- ML training: <link>
- Frontend demo: <link>
- Deploy: <link>
