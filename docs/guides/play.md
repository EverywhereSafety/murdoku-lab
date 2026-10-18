# Play, create and analyze puzzles

[Play now](https://everywheresafety.github.io/murdoku/play/) ·
[Website](https://everywheresafety.github.io/murdoku/) ·
[Blog](https://everywheresafety.github.io/blog/treasure-hunt/) · [Project](../../README.md) · [Code](https://github.com/EverywhereSafety/murdoku-lab) ·
[Data](data.md) · [Training](https://github.com/EverywhereSafety/agent-horizon)

The web build has two pages:

- **The player** at `/`: the generated case collection, with setting and size filters,
  guided training, daily cases and the built-in classics. It is a static JavaScript app
  that plays exported puzzles without loading Python.
- **The Lab** at `/lab/`: the research casebook. It runs the Python sessions, either through
  the session server or in the browser through Pyodide, and adds the journal, exports,
  solver views and query review.

On the public site, the player lives at `/murdoku/play/` and the separate Research Lab
at `/murdoku/play/lab/`. Existing project and blog Play links open the player. Old
`/murdoku/exp/` links redirect to `/murdoku/play/` with their query parameters and
fragment preserved.

## Run the local release

```bash
npm ci
npm run release:local
```

This prepares the complete release from versioned inputs: 24 frozen themed cases, five
classics, one training case and 14 locked daily cases, plus the brand assets and a
design-token check. It then builds the web app and serves everything on one port.
The release does not generate new puzzles or re-theme existing release cases, and it
does not depend on an `outputs/showcase/` directory.

| URL                                   | What                                            |
| ------------------------------------- | ----------------------------------------------- |
| http://127.0.0.1:4173/                | The player                                      |
| http://127.0.0.1:4173/?date=2026-10-20 | The player as if it were that day              |
| http://127.0.0.1:4173/?unlock=all     | Every daily case of the season                  |
| http://127.0.0.1:4173/?case=tutorial  | One case by id (`?d=<n>` for daily case n)       |
| http://127.0.0.1:4173/d/4/            | Link-preview page of daily case #4              |
| http://127.0.0.1:4173/lab/            | The Lab                                         |

To try it on a phone on the same Wi-Fi, run `.venv/bin/python scripts/release_local.py --lan`
and open the printed address. `--no-build` serves the last build; `--port` changes the
port. Nothing is published and the player makes no requests to other sites.

## Share a test build

```bash
npm run package:preview
```

This builds the player and writes `outputs/preview/murdoku-preview-<date>.zip`: the static game
without the Lab, a double-click launcher for macOS and one for Windows that serve it on
http://127.0.0.1:4173/ with the computer's own Python and open the browser, and a short guide
for testers in Chinese (`scripts/preview/`). Opening `index.html` straight from disk does not
work, because the browser will not let the page load its case files. Nothing is uploaded; hand
the zip round yourself.

For a temporary player preview on another static address, use the preview packager and
point its Lab link at the production Research Lab:

```bash
python scripts/package_preview.py --site https://example.org/murdoku-preview/ \
  --lab https://everywheresafety.github.io/murdoku/play/lab/
```

Replace the example address with your preview host. This prepares the current frozen
collection and locked daily cases, then writes `outputs/site/murdoku-preview/`.
Share links and preview images point at the preview address, every page carries
`noindex`, and `lab/` links to the explicit `--lab` destination. This package is for
temporary previews; the public `/murdoku/exp/` address remains a redirect to the canonical
player. For production, use the complete [static build](#static-hosting) below.

The player's saves (`murdoku:v1:*` in local storage) do not touch the Lab's
(`murdoku-visual-session:<path>`), so both can live on one origin.

## Playing

The homepage opens with the workshop introduction and main generated-case action on the
left, explaining the focus on unique solutions, discovery rhythm and varied worlds. The
daily case appears on the right, with previous/next date controls, a **Today** reset and
a native range slider for browsing the published season. Future cases remain locked.
Daily statistics and an expandable season calendar appear farther down the page.
Project and Blog links stay in the header; the full resource navigation stays in the footer.

The main action resumes a generated case in progress or opens an unsolved case. After a
solve, **Play another case** prefers an unseen puzzle in another setting, skips the current
puzzle and solved versions of the same formal puzzle, and falls back to unsolved classics.
When the collection is exhausted, the homepage offers a replay. These actions select from
published cases; generating and publishing more remains an offline workflow.

Every case has one solution. Each suspect, and the victim, stands on exactly one square;
no two people share a row or a column; crossed-out squares are blocked. Place everyone,
then name the person who was alone with the victim.

| Action                         | Touch or mouse                                 | Keyboard                       |
| ------------------------------ | ---------------------------------------------- | ------------------------------ |
| Pick a suspect                 | Tap their card or their standee                | Their letter                   |
| Place, move or swap            | Tap a square, or drag a card or standee        | Arrows, then Enter or Space    |
| Pick up                        | Tap the suspect's square again                 |                                |
| Notes (maybe → ruled out → clear) | Turn on **Notes**, or press and hold a square | Shift+N toggles Notes; Shift+Enter writes a note |
| Undo, redo                     | Toolbar buttons                                | Ctrl/Cmd+Z, Shift+Ctrl/Cmd+Z   |
| Deselect                       |                                                | Escape                         |

Placing someone crosses out the rest of their row and column. Two people in a row,
column or blocked square are ringed in red. Tapping a name, room or object in a statement
highlights it on the board. **Accuse** becomes available once everyone is placed without
a conflict.

Press a person’s letter to select them; **Shift+N** toggles Notes. Public roles appear below each person’s name.

**Hints** have three levels per target: a nudge toward the statement to read, then a
partial answer (a room or a row), then the square itself. A hint first checks whether
someone is placed wrongly. Only the last level counts as a reveal.

**Stars**: ★★★ with no hints and no wrong verdict; ★★ with hints that revealed nothing and
at most one wrong verdict; ★ otherwise. A solved case shows the murderer, a GUILTY stamp,
the closing paragraph, stars and time, and a spoiler-free share line.

The **training case** coaches a first-time player through each deduction in order. It opens
from the home page and from **How to play**. Requested hints temporarily replace the coach;
closing or placing a hint restores the coach. These hints use the same star rules as other cases.

**Settings**: night mode, sound, vibration, a visible timer (time is always kept for the
results), and the Lab's habit of tapping for notes and holding to place.

Progress, stars and streaks stay in this browser's local storage. See the
[daily case guide](daily.md) for how daily cases are made and the
[case format](../reference/play-case-format.md) for what the player loads.

## Build the case library

The player reads static bundles from `web/public/cases/`. Both default export commands
read the 24 frozen themed bundles in the version-controlled
`content/showcase/player-bundles.jsonl`, then combine them with five built-in classics
and one training case to write the 30-case library:

```bash
python -m murdoku_lab.visual.play_export
# Equivalent: npm run export:cases
```

For a complete release, `npm run release:local` and `scripts/build_play.py` share
`scripts.release_local.prepare_assets()`: each build prepares this library, the 14 locked
daily cases with share links for its base URL, the brand assets and the design-token check
before invoking Vite. These commands read the frozen inputs each time; previous files in
`outputs/showcase/` are not release inputs.

### Generate a custom collection

Generating future cases is a separate authoring workflow. For example, create three
new cases per setting and export them in place of the frozen showcase:

```bash
python scripts/build_showcase.py
python -m murdoku_lab.visual.play_export --records outputs/showcase/cases.jsonl
npm run build
```

An explicit `--records PATH` accepts JSONL of dressed records with `murdoku_case` and
`murdoku_theme`. It replaces the showcase while keeping the classics and training case.
This custom export does not update the versioned release input; running a default release
afterward restores the frozen collection. Review and freeze new content separately before
using it in a future release.

## The Lab

The built-in casebook includes **The Museum After Hours**, a 24 × 24 case with
24 people and fifteen rooms. Connect statements about the exhibits, staff roles
and distances between people. Zoom in to read the room labels and use pencil
marks to keep track of possible placements.

![Playable casebook](../assets/play-preview.png)

### Board controls

Select a character, then tap a square to add or remove a candidate. Hold the
square briefly or press Space to confirm the placement. Dragging a character
onto the board also confirms it. Undo and redo work for both notes and placements. An incorrect submission offers
**Keep investigating**, preserving the board, candidates and notes in a new attempt.

Placing a person immediately crosses out the rest of their row and column.
Choose **Exclude** (E) to toggle purple exclusions for the selected person;
**Erase** (X), undo and redo also work on these notes. Exclusions survive refresh
and appear in the session journal. Selecting a person highlights statements that
mention them, including statements held by other people.

Hover or focus a square to highlight its row, column, coordinates and room.
Use Ctrl/Cmd + scroll or a two-finger pinch to zoom around that position.
Shift + drag pans on desktop; a single finger scrolls on touchscreens.
**Fit the board** resets the view. **View underlying objects** temporarily hides
people and notes so you can inspect furniture and terrain without moving anyone.

Use **Focus on the board** to expand the workspace, with the cast and clues
alongside it. Zoom and scroll for larger boards; Escape returns to the page.
Observation exports and generated-sample review are under **For developers**.
The **Casebook** style shows the board as the player draws it; the older styles remain
available for comparison with published query images.

### Run the Lab with the session server

Use the sibling Agent Horizon checkout from the [installation quickstart](../../README.md#install).

```bash
python -m pip install -e ../agent-horizon -r requirements.txt
npm ci
npm run build
python -m murdoku_lab.visual.server --port 8765
# Optional: --records /path/to/trusted/cases-or-queries.jsonl
```

Open http://localhost:8765/lab/. The same server serves the player at `/`. The React Lab is
in `web/src/` (the player is in `web/src/play/`); the Python server owns sessions and serves
public observations. Private answers stay server-side.

### Static hosting

The production build serves the player at `/murdoku/play/` and an independent Research
Lab at `/murdoku/play/lab/`. It runs the same complete asset preparation as the local
release, then adds the Python runtime and engine that the Lab runs in a Web Worker
through Pyodide. The player does not load that runtime.

```bash
npm ci
python scripts/build_play.py --site-url https://everywheresafety.github.io/murdoku/play/
```

Copy the contents of `dist/` into the website checkout's `murdoku/play/`
(`../site/murdoku/play/` in the paired checkout). Existing Play links in the project
and blog then open the new player, and its Research Lab link opens `lab/` beneath it.
The old `/murdoku/exp/` address is kept as a redirect that preserves query parameters
and fragments. The build command itself does not publish.

For another static host, replace `--site-url` with the public base URL where you will
serve `dist/`; it sets the daily share links and preview-image URLs. This full build
includes the Lab's demo cases and answer keys. Training and evaluation continue to use
the Python environment independently.

### Host shared play

Build the frontend and run it with the Python session API:

```bash
npm ci && npm run build
python -m murdoku_lab.visual.server --host 0.0.0.0 --port 8765 \
  --records /absolute/path/to/cases.jsonl
```

Put an HTTPS reverse proxy in front of this service. Serve `/` and `/api/` from
the same origin; the frontend uses relative API URLs. A future `play` subdomain
can point at the same service without rebuilding the frontend. GitHub Pages can
host the project website and Blog, while this API requires a Python host.

Sessions currently live in the server process: restarting it resets sessions.
Use a single service process until session storage is shared. The playable API
exposes puzzle interactions rather than the agent's Python execution tool.

Public navigation links connect the game to Everywhere Safety, the project,
Blog, query documentation and Agent Horizon.

## Artwork

The casebook style draws every board as a 3/4 dollhouse in the case's setting; see
[artwork](../reference/artwork.md) and [setting packs](../reference/settings.md).

The renderer also supports bundled Microsoft [Fluent Emoji Flat](https://github.com/microsoft/fluentui-emoji)
SVGs. The local catalog includes 47 assets with concepts, categories and compatible
formal roles. Upstream MIT attribution is retained with the source artwork.
`murdoku_lab/setter/visual_assets.py` selects approved IDs from the catalog; public object
labels use the selected concepts. Formal geometry and grading remain unchanged. Paired
exports can use `artwork_style="fluent"`.

## Preview a query bundle

```bash
python -m murdoku_lab.visual.preview --bundle data/paired-queries
npm run build
python -m murdoku_lab.visual.server --records data/paired-queries/text.rl.jsonl --port 8765
```

Open http://localhost:8765/review/index.html to browse paired images and text queries.
`--out` selects another preview directory.

## Export an SVG

```bash
python scripts/render_svg.py --case glasshouse --scope full --out outputs/board.svg
```

Rendering code lives in `murdoku_lab/visual/art/`; these scripts provide rendering and demo-verification commands.

## Frontend checks

```bash
npm run test:engine     # the player's game engine against Python fixtures
npm run test:play       # after a build: the player on desktop and phone
```

With the session server running, `npm run test:browser` and `npm run test:proxy` check
the Lab. Set `MURDOKU_TEST_URL` for another port. The proxy check works with bundled demo
cases; to also check a generated query gallery, supply that bundle to the server and set
`MURDOKU_TEST_REVIEW_COUNT` to its case count. The browser checks use Playwright's
Chromium, or another Chrome set with `MURDOKU_BROWSER_PATH`.
