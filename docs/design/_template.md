# <Feature Name>

> Spec for one feature. Single source of truth. Humans write **Decision**; agents may draft the rest.
> Path: `docs/design/<feature>.md`

---

## Goal

<One sentence. If you can't, the feature isn't ready.>

## Non-goals

- <what this feature does NOT do, even if tempting>

## Acceptance

(Prefer runnable. Free-form bullets only when truly impossible.)

```bash
# e.g.
pytest tests/test_<feature>.py -v
# or
python scripts/check_<feature>.py --threshold 0.9
# or
jsonschema -i out.json schemas/<feature>.json
```

Plain-English fallback (use sparingly):
- [ ] <observable, measurable claim — never "fast" / "clean" / "good">

## Decision

**Candidates considered** (≥3 — if you can't, you haven't explored):

- **A**: <how>. Pros: <…>. Cons: <…>.
- **B**: <how>. Pros: <…>. Cons: <…>.
- **C**: <how>. Pros: <…>. Cons: <…>.

**Chosen**: <X>

**Why**: <2–4 sentences. The synthesis. This is the human's contribution.>
