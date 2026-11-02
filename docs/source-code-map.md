# Source code map: claudia-example-project

> **Version:** 1.1 — **Last updated:** 2026-11-02

What this project is made of, where each part lives, and the document that explains it. Keep it current in the same
commit as the change (`docs/_contract.md`); `package-ci` fails a PR whose source file is not listed here.

## This repo: the package `@jo51yon/claudia-example-project`

| File | What it does | Documented in |
|---|---|---|
| `src/index.ts` | Package entry: `RobotStudio`, the host type, the catalogue | `docs/robot-studio/design.md` §Where the code lives |
| `src/robot-studio/RobotStudio.tsx` | Studio, Settings and About pages; nav; the attribute tree; the speak box | §What it is |
| `src/robot-studio/host.ts` | What the host app hands over: Supabase client, endpoints, `Tree`, `Card`, the connect panel | §Where the code lives |
| `src/robot-studio/Robot.tsx` | The robot as SVG; `mouth` 0..1 drives the mouth while speaking | §What it is |
| `src/robot-studio/options.ts` | The single catalogue: colours, hair, glasses, hats, neckwear, voices (Robot plus 8 Chirp); `sanitise()` | §Speech, §Chat control |
| `src/robot-studio/useRobotState.ts` | Loads and saves the signed-in person's robot row, subscribes over Realtime, speaks when a chat bumps `say_seq` | §Chat control |
| `src/robot-studio/useSpeech.ts` | Probes Chirp availability; Chirp 3 HD audio, or the Robot (browser) voice with no error | §Speech |
| `test/catalogue.test.mjs` | Catalogue checks on the built package | test script A0 |
| `.github/workflows/package-ci.yml` | This project's gates: build, type-check, tests, this map, the PR's ledger task | — |
| `docs/robot-studio/design.md` | Design | — |
| `testing/scripts/example-robot-studio.md` | Test script | — |

## On Claudia's platform (repo `Jo51yon/claudia`)

These run on Claudia's Supabase project and deploy only from the Claudia repo.

| Path | What it does |
|---|---|
| `src/robot-studio-host.tsx` | Host adapter: mounts this package at `/?app=robot-studio` with Claudia's client and shared components |
| `supabase/functions/example-robot-speak/index.ts` | Signed-in text to MP3 (Google Chirp 3 HD, `GOOGLE_TTS_API_KEY`); `{"probe":true}` reports availability |
| `supabase/functions/example-robot-mcp/index.ts`, `robot.ts` | MCP tools `robot_options`, `robot_get`, `robot_set`, `robot_say` on the caller's own row |
| `supabase/functions/claudia-mcp/dashboard.d/example-robot-studio.ts` | The RPCs the page calls, for `dashboard.test.ts` |
| `supabase/migrations/20261101130000_claudia_example_robot_studio.sql` | `claudia_example_robot` (RLS own row), save RPC, MCP bearer resolver |

## Not this project's code

The example project's **demo** on the Claudia dashboard (open to every account, Reset Demo, seeded ledger data) is a Claudia
platform feature on the `claudia` project's ledger. Its documents stay in `Jo51yon/claudia`: `docs/example-project/README.md`,
`testing/scripts/claudia-example-project-demo.md`.
