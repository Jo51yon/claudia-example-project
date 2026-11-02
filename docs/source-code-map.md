# Source code map: claudia-example-project

> **Version:** 1.0 — **Last updated:** 2026-11-02

What this project is made of, where each part lives, and the document that explains it. Keep it current in the same
commit as the change (`docs/_contract.md`).

## Where the code is today

Robot Studio, this project's app, runs inside the Claudia web app at `https://claudia.sicoru.org/?app=robot-studio`, and its
server parts are Claudia edge functions and migrations. Its **code** therefore currently lives in `Jo51yon/claudia`; its
**design, test script and this map** live here (moved 2026-11-02, see `plan.md` LLR 002). Moving the code itself into this
repo is an open owner decision (ledger `example-robot-studio-repo-home:develop`).

| Area | Path (repo `Jo51yon/claudia` unless marked) | What it does | Documented in |
|---|---|---|---|
| Page | `src/robot-studio/RobotStudio.tsx` | Studio, Settings and About pages; nav; the attribute tree (shared `ClaudiaTree`), the speak box, the MCP connect panel (shared `ConnectAIPanel`) | `docs/robot-studio/design.md` §Pages |
| Drawing | `src/robot-studio/Robot.tsx` | The robot as SVG; every attribute is a visible change; `mouth` 0..1 drives the mouth while speaking | §Pages |
| Catalogue | `src/robot-studio/options.ts` | The single list of colours, hair, glasses, hats, neckwear and voices; `sanitise()` keeps only known values | §Data model |
| State | `src/robot-studio/useRobotState.ts` | Loads and saves the signed-in person's robot row, subscribes over Realtime, speaks when a chat bumps `say_seq` | §Data model |
| Speech | `src/robot-studio/useSpeech.ts` | Chirp 3 HD audio through `example-robot-speak`, browser voice otherwise; mouth follows the audio level | §Speech |
| Speech function | `supabase/functions/example-robot-speak/index.ts` | Signed-in text to MP3 via Google Text-to-Speech (`GOOGLE_TTS_API_KEY`), rate limited | §Speech |
| MCP server | `supabase/functions/example-robot-mcp/index.ts`, `robot.ts` | `robot_options`, `robot_get`, `robot_set`, `robot_say`, acting only on the caller's own row | §MCP |
| MCP parity test | `supabase/functions/example-robot-mcp/robot_parity.test.ts` | Fails when the MCP catalogue and `options.ts` differ | test script A1 |
| Dashboard registry | `supabase/functions/claudia-mcp/dashboard.d/example-robot-studio.ts` | Lists the RPCs the page calls, checked by `dashboard.test.ts` | — |
| Database | `supabase/migrations/20261101130000_claudia_example_robot_studio.sql` | `claudia_example_robot` (one row per user, RLS own-row), save RPC, MCP bearer resolver | §Data model |
| Design | `docs/robot-studio/design.md` (**this repo**) | Why, pages, speech path, MCP, data model, limits | — |
| Test script | `testing/scripts/example-robot-studio.md` (**this repo**) | Automated, signed-out browser and live checks | — |

## Not this project's code

The example project's **demo** on the Claudia dashboard (open to every account, Reset Demo, seeded ledger data) is a Claudia
platform feature on the `claudia` project's ledger (`claudia-example-project-demo`, `claudia-example-project-data`). Its
documents stay in `Jo51yon/claudia`: `docs/example-project/README.md`, `testing/scripts/claudia-example-project-demo.md`.
