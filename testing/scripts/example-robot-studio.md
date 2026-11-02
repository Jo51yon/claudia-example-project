# Test script: example-robot-studio

> **Version:** 1.1 — **Last updated:** 2026-11-02 (moved from `Jo51yon/claudia`)

Ledger tasks: `example-robot-studio:develop`, `:test`, `:demo` (project `claudia-example-project`). Guide:
`docs/robot-studio/design.md` (this repo). Code and migration paths are in `Jo51yon/claudia` (`docs/source-code-map.md`). Migration `20261101130000_claudia_example_robot_studio.sql`.

## A. Automated (no secrets needed)

| # | Check | Expected |
|---|---|---|
| A1 | `deno test supabase/functions/example-robot-mcp/` | MCP values equal the page's catalogue; unknown values refused; four tools listed |
| A2 | Migration applied twice on Postgres 16 | second run changes nothing and raises no error |
| A3 | Two users, RLS | each reads only their own row; direct insert/update refused for `authenticated`; `claudia_mcp_example_robot` refused to `authenticated` and `anon`; `claudia_example_robot_save` refused to `anon` |
| A4 | `robot_set` with extra keys and a non-string | only the six known keys with string values are stored |
| A5 | Revoked, expired and unknown bearer tokens | `claudia_example_robot_resolve_bearer` returns null |
| A6 | `tsc --noEmit` | no errors in `src/robot-studio/` |

## B. Browser (signed out)

| # | Step | Expected |
|---|---|---|
| B1 | Open `/?app=robot-studio` | nav, left pane, robot, text box; no sign-in wall |
| B2 | Choose Hat > crown, Glasses > shades, Colour > coral | robot changes at once; each category chip shows its choice |
| B3 | Speak | status says Chirp needs sign-in and the browser voice is used; mouth height varies while speaking and returns to closed at the end |

## C. Live (signed in, after merge, with `GOOGLE_TTS_API_KEY` set)

| # | Step | Expected |
|---|---|---|
| C1 | Project card on the dashboard, example project, Open app | opens Robot Studio, not the dashboard |
| C2 | Change attributes, reload | robot unchanged |
| C3 | Speak with Puck, then Aoede | audible different Chirp voices, pill says "Chirp voice", mouth follows the audio |
| C4 | Settings > connect Claude with the shown URL | connection appears in the list |
| C5 | In that chat: "give the robot a crown, pick Charon, say good morning" | page updates live and speaks it |
| C6 | Ask the chat for `hat: sombrero` | refused with the allowed list |
| C7 | Ledger | design, develop, test and demo tasks for the feature are on the example project with their results |
