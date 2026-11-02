# Standing rules for every agent session in a Claudia project repo (owner: Jolyon Grace)

These are mandatory. They mirror Claudia's RULES CORE (`rules_load` on the Claudia Control Plane MCP returns it in full) and
the SafeSpaces standing rules, ported 2026-11-02 (`claudia-session-hooks-parity:develop`). Follow all of them, every time.
Hooks in `scripts/hooks/`, wired in `.claude/settings.json`, enforce the ones marked **(enforced)**.

1. **Recall before acting (enforced).** At the start of every conversation and whenever the subject changes: `rules_load`,
   then `memory_recall` (with `project_slug`) and `kb_recall`, and `code_recall` before exploring the repo. `ltm_first_gate.py`
   refuses the first working tool of a turn until a recall has run in that turn. `claim_gate.py` pushes back a reply that
   says something is missing, impossible or blocked without a recall on that subject or a `Searched:` receipt.
2. **Look it up before you ask (enforced).** Before asking the owner anything, search memory, the knowledge bank, the ledger,
   the repos and the uploaded files. Open the question with `Searched: <tool>("<q>") -> <hits>; ... Not found, so asking:
   <one question>.` `ask_gate.py` pushes back a question without the recall and the receipt.
3. **Credentials.** Use vault and broker routes without printing a secret. If one is exposed, rotate it yourself.
4. **Blocks are real.** A block must be evidenced and paired with a workaround and a way to stop it recurring. A host that
   cannot be reached is not a block until the recorded route has been tried (`egress_signpost.py` names it).
5. **No selective compliance.** If a rule conflicts with the task, say so and ask. A tool, hook or classifier denial is final
   for that route: report it with the narrowest sanctioned route; do not work around it.
6. **Database writes (enforced).** Migrations go through CI only (a project with its own Supabase project uses its own migration CI the same way): commit the migration with a self-test under
   `testing/sql/`, open a PR into `preview` (`migration-dry-run.yml` runs it on live and rolls back), and
   `apply-migrations.yml` applies it once merged. SafeSpaces writes go through the run-live-sql runner in oursafe-space.
   Ledger and memory writes go only through the Claudia Control Plane MCP, never by SQL. `supabase_write_route.py`
   refuses a Supabase-connector write and names the route. Read-only SELECTs are fine.
7. **Claim what you work, and heartbeat it (enforced).** Claim every ledger task you work (`tasks_claim`, with your session's
   cumulative usage). While you hold it, call `tasks_heartbeat` (pass `actor`) with what landed and the evidence at least
   every 15 minutes and whenever a step lands. `brief_gate.py` pushes back a turn of work on a claimed task with no
   heartbeat, or a gap of more than 15 minutes. A claim with no heartbeat for 6 hours is reclaimed.
8. **Brief chat, detail on the ledger (enforced).** Chat carries only what the owner must see or decide: Decided / Need from
   you / Exceptions, at most about 170 words. Every step's detail, evidence and reasoning goes on the ledger task
   (`tasks_heartbeat`, `tasks_record_decision`) and memory (`memory_write`). `brief_gate.py` pushes back a reply over
   budget, or a turn of real work with nothing written to the ledger or memory.
9. **Record what you learn and what it cost.** Owner decisions go to the ledger in the same turn (`tasks_record_decision`).
   Pass your session meter's cumulative usage on `tasks_claim`, `tasks_transition` and `memory_write`.
10. **A project's work lives in its own repo.** Its design, test scripts, rig manifests, storyboards, source-code map and code
    are committed in the project's repo, never in `Jo51yon/claudia`. Pull requests need no permission: open them into the
    branch the repo's flow names (`preview`).
