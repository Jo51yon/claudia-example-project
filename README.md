# claudia-example-project

**This repository was created entirely by Claudia''s project-factory automation** — the
first real test of it, and the direct fulfilment of the exit test set at the start of the
Claudia epic: *"Claudia creates Project #2 with zero manual steps, and Project #2''s first
PR is blocked by a Claudia gate for a real reason."*

## What's real here

- Repo, branches, this governance scaffold, and branch protection were all created via
  Claudia's own `gh_api_request`/`gh_api_result` (in Claudia's database, using a GitHub
  credential in Claudia's own vault — not borrowed from SafeSpaces for this).
- Registered in Claudia's project registry (`claudia_projects`), so it shows up in the
  workbench dashboard alongside Claudia itself.
- Branch protection is proven the same way Claudia's own was: a deliberately non-conforming
  PR should be rejected by the `gate` check before this project is considered done.

## What this is NOT (yet)

A fully provisioned project. Supabase, Cloudflare, vault credentials, and an EP entry are
still a manual runbook — see `skills/claudia-project-factory/SKILL.md` in the Claudia repo
for the current state of that automation boundary.
