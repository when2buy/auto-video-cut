# The Standard

> One page. Three rules. Everything else is a reference doc.

---

## 1. SPEC — alignment artifact

Every feature has **one** Markdown file: `docs/design/<feature>.md`.
It contains exactly four sections:

```
## Goal              ← one sentence
## Non-goals         ← what we don't do
## Acceptance        ← runnable checks (tests, scripts, schemas)
## Decision          ← which of ≥3 candidates and why
```

Humans write the **Decision** (this is taste / synthesis).
Agents may draft everything else.

If the spec isn't clear, *that's* the work — don't start coding.

## 2. LOOP — auto execution

Agent reads spec → writes code → runs Acceptance → not green, iterates.
**No human in the loop.** Use Claude Code `/loop`, Codex CLI, or any agent harness.

The agent is allowed to fail up to **N=5** times on the same task before stopping and asking. Otherwise it keeps going.

## 3. GATE — the only manual checkpoint

Stop and `/confirm` with a human **only** for actions that can't be undone in 5 minutes:

- push to `main` / `--force` / rebase shared history
- deploy to prod / write to shared S3 / DB schema change
- spend > $50 on GPU or paid APIs
- send messages outside self-channels

Everything else: **don't ask, just do**. The point of this standard is that the human is *not* a bottleneck.

---

## Defaults (rarely overridden)

- **Branch**: feature branches, never push to main
- **Spec lives**: in repo (`docs/design/<feature>.md`)
- **Acceptance form**: prefer runnable (test / script / schema validation). Plain-English bullets only when truly impossible.
- **Multi-agent fan-out**: serial by default. Parallel only for read-only, independent tasks (codebase audit, eval generation, breadth research). Never parallel for coding the same feature.
- **Critic pass**: optional. If you do one, open a fresh session with no runlog access.
- **Learnings**: agents append to `docs/learnings.md` as they go. Periodic distillation back into the standard or a domain how-to.
- **AGENTS.md**: every repo has one at root, points to this standard.

## Why so short?

Long standards don't get followed by humans *or* agents.

> *"现在的模型就是 follow instruction 很好的"* — model is good
> *"你不用你每次你人一直在那个 loop"* — human shouldn't be in loop
> *"我连那个文档也不看，我只看真的 design 档"* — only design doc matters

A 12-SOP earlier draft contradicted all three. This version doesn't.

If a rule isn't on this page, it's not a rule.

---

## Reference (read on demand, not by default)

- [agents.md](https://agents.md) — open spec for `AGENTS.md`, 30+ agents compatible
- [GitHub Spec Kit](https://github.com/github/spec-kit) — heavier SDD framework if you want named slash commands
- [Cognition: "Don't Build Multi-Agents"](https://cognition.ai/blog/dont-build-multi-agents) — why parallel sub-agents fail
- [Anthropic best-practices](https://code.claude.com/docs/en/best-practices) — plan mode, fresh-context critic
- [Software Engineering at Google ch.10](https://abseil.io/resources/swe-book/html/ch10.html) — design-doc culture origin
