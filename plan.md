# claudia-example-project — Lessons Learnt Register (LLR)

**Append-only.**

---

### 001 — Bootstrap exception: the first scaffold commit predates the gates
**2026-08-03.** Created via Claudia's project-factory automation. The initial scaffold was
committed to `preview` and fast-forwarded to `main` before branch protection existed —
same documented exception as Claudia's own repo (see Claudia's `plan.md` LLR 001).

**Rule:** this is the only permitted commit that bypasses the pipeline.

---

### 002 — The project's work was committed to another repo, and the gates let it through
**2026-11-02.** Robot Studio (ledger `example-robot-studio-design:develop`, `example-robot-studio:develop`) was built with
its code, design and test script in `Jo51yon/claudia` (PR #617), because this repo was not reachable by Claudia's GitHub
App. Both tasks closed done/pass on a PR link alone; the independent verifier said `insufficient_evidence` on both and
nothing changed. No exemption was involved: Claudia's develop gate did not ask for the change to be in the project's own
repo, nor for a test script.

**Fixes:** the design, test script and a source-code map moved here; claudia #649 adds the gates `change_in_project_repo`
and `test_script_named` and makes the verifier blocking (`insufficient_evidence` sends a claim back).

**Rule:** a project's design, test scripts, source-code map and documentation live in the project's own repo. If the repo is
not reachable, that is a blocker to fix (connect the Claudia GitHub App), not a reason to commit elsewhere.
