# claudia-example-project — Lessons Learnt Register (LLR)

**Append-only.**

---

### 001 — Bootstrap exception: the first scaffold commit predates the gates
**2026-08-03.** Created via Claudia's project-factory automation. The initial scaffold was
committed to `preview` and fast-forwarded to `main` before branch protection existed —
same documented exception as Claudia's own repo (see Claudia's `plan.md` LLR 001).

**Rule:** this is the only permitted commit that bypasses the pipeline.
