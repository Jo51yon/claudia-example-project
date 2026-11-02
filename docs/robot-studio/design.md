# Robot Studio: the Claudia example project's UI

> **Version:** 1.2 — **Last updated:** 2026-11-02. Moved from `Jo51yon/claudia` and turned into this repo's package
> (`@jo51yon/claudia-example-project`); see `docs/source-code-map.md`.

Status: built 2026-11-01 (owner request). Ledger tasks on `claudia-example-project`: `example-robot-studio-design:develop`
(this design), `example-robot-studio:develop`, then test and demo. Test script `testing/scripts/example-robot-studio.md` (this repo).

## Why

The example project's card linked to the Claudia dashboard (its Demo tour), because the project has no app of its own and
its own repo (`Jo51yon/claudia-example-project`) is private and not reachable by Claudia's GitHub App. A visitor wants to
*see something work*. Robot Studio is a small, friendly app that shows the shared component library in use and gives a
chat (MCP) something visible to control.

## What it is

Open `/?app=robot-studio` (the example project's card and the project page link there). It has a top navigation
(Studio, Settings, About, a link back to the project's ledger), a dark background with a drifting grid and glow, and:

| Area | What it does | Shared component |
|---|---|---|
| Left pane | Categories (Colour, Hair, Glasses, Hat, Neckwear, Voice) open to options; clicking one changes the robot at once | `ClaudiaTree` |
| Stage | An SVG robot; the text box and **Speak** button speak the text with the chosen voice while the mouth moves | - |
| Settings | Connect Claude (or another MCP client) so a chat can control the robot | `ConnectAIPanel` |
| About | What was reused, and a link to the ledger that built it | `ClaudiaCard` |

## Speech

`example-robot-speak` (edge function) takes text and a Chirp 3 HD voice name (`en-GB-Chirp3-HD-<Voice>`, one of
Aoede, Kore, Leda, Zephyr, Puck, Charon, Fenrir, Orus) and returns MP3 from Google Cloud Text-to-Speech. The page plays it
through Web Audio and sets the mouth opening from the live audio level, so the lips follow the actual sound.

Rules it keeps: signed-in users only (JWT checked), 600 characters, 12 requests a minute per user per instance.
The key is the edge function secret `GOOGLE_TTS_API_KEY`; without it the function answers `503 tts_not_configured`.

The voice list starts with **Robot**, the browser's own speech voice, which always works. On load the page sends
`{"probe":true}` to `example-robot-speak`, which answers `{"chirp":<secret set>}`. When Chirp is unavailable (signed out
or secret missing) Robot is the selected voice and the Chirp voices are greyed out and cannot be chosen, so the demo
plays the voice it shows with no error. A Chirp request that fails (upstream error, rate limit) also speaks with Robot,
silently. The mouth follows the real audio for Chirp and a rhythm for Robot. A browser voice is never labelled Chirp.

## Chat control (MCP)

`example-robot-mcp` is its own MCP server, registered as product `robot-studio` on the shared `claudia-mcp-oauth`
server (same sign-in as Lintel, PETGI and S3 Photobook). Tools: `robot_options`, `robot_get`, `robot_set`,
`robot_say`. Values are checked against the same catalogue the page draws (`src/robot-studio/options.ts`;
`robot_parity.test.ts` fails if the two differ). Each person controls only their own robot.

It is separate from `claudia-mcp` on purpose: a demo toy should not add tools to the control plane, and every tool added
to `claudia-mcp` must also be added to the SafeSpaces parity manifest (`docs/_platform/mcp-parity.json`).

Data: table `claudia_example_robot` (one row per user: attributes, `say_seq`, `say_text`). The page subscribes over
Realtime; `robot_say` bumps `say_seq`, and a page seeing a higher number speaks the text. The page must be open for the
speech to be heard. Migration `20261101130000_claudia_example_robot_studio.sql`.

## Known limits

- Speech from a chat is played by an open page; with none open the text is stored and nothing is heard.
- The demo reset (`claudia_example_demo_reset`) keeps every task in the demo baseline, these ledger tasks included, and
  removes only changes made after it (claudia #633).
- A signed-out visitor can design the robot and use the browser voice; nothing is saved and chat control is off.

## Where the code lives (2026-11-02)

Owner decision 2026-11-02: the project's code lives in the project's own repo. Robot Studio's page is this repo's package
`@jo51yon/claudia-example-project` (`src/robot-studio/`). Claudia installs it from this repo by tag, like
`@jo51yon/claudia-calendar`, and mounts it at `/?app=robot-studio` through a small host adapter
(`src/robot-studio-host.tsx` in `Jo51yon/claudia`) that hands over the Supabase client, the endpoints and the shared Claudia
components (`ClaudiaTree`, `ClaudiaCard`, `ConnectAIPanel`). The package never imports Claudia code (`src/robot-studio/host.ts`).

The server side stays on Claudia's platform because it runs there: the edge functions `example-robot-speak` and
`example-robot-mcp` and the migration `20261101130000_claudia_example_robot_studio.sql` deploy only from `Jo51yon/claudia`.
Claudia's robot MCP catalogue (`supabase/functions/example-robot-mcp/robot.ts`) is checked against this package's
catalogue in Claudia's CI.
