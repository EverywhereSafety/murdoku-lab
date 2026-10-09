# Play, create and analyze puzzles

[Play now](https://everywheresafety.github.io/murdoku/play/) ·
[Website](https://everywheresafety.github.io/murdoku/) ·
[Blog](https://everywheresafety.github.io/blog/murdoku-as-vhd/) · [Project](../../README.md) · [Code](https://github.com/EverywhereSafety/murdoku-lab) ·
[Data](data.md) · [Training](https://github.com/EverywhereSafety/agent-horizon)

The illustrated casebook presents a board, the cast and their statements. Place
characters, check placements and submit the arrangement and murderer. Solver
certificates and [reasoning profiles](../reference/reasoning-profiles.md) support
analysis of generated cases.

![Playable casebook](../assets/play-preview.png)

## Board controls

Select a character, then tap a square to add or remove a candidate. Hold the
square briefly or press Space to confirm the placement. Dragging a character
onto the board also confirms it. Undo and redo work for both notes and placements. An incorrect submission offers
**Keep investigating**, preserving the board, candidates and notes in a new attempt.

Use **Focus on the board** to expand the workspace, with the cast and clues
alongside it. Zoom and scroll for larger boards; Escape returns to the page.
Observation exports and generated-sample review are under **For developers**.

## Static hosting

The [online casebook](https://everywheresafety.github.io/murdoku/play/) runs in
your browser, with progress saved on this device. It uses the same Python
sessions, actions, scoring and SVG renderer through Pyodide in a Web Worker.
The build includes the Python runtime, so gameplay needs no external CDN.
The first visit downloads it from the game website; subsequent visits use the browser cache.

Build it for GitHub Pages or any static host:

```bash
npm ci
python scripts/build_play.py
# Publish dist/ at /murdoku/play/ or another directory.
```

Static play bundles the demo cases and their answer keys. Training and evaluation
continue to use the Python environment independently.

## Run locally

Use the sibling Agent Horizon checkout from the [installation quickstart](../../README.md#install).

```bash
python -m pip install -e ../agent-horizon -r requirements.txt
npm ci
npm run build
python -m murdoku_lab.visual.server --port 8765
# Optional: --records /path/to/trusted/cases-or-queries.jsonl
```

Open http://localhost:8765/. The React frontend is in `web/`; the Python server
owns sessions and serves public observations. Private answers stay server-side.

## Host shared play

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

## Colorful artwork

The renderer supports bundled Microsoft [Fluent Emoji Flat](https://github.com/microsoft/fluentui-emoji)
SVGs. The local catalog includes 47 assets with concepts, categories and compatible
formal roles. Upstream MIT attribution is retained with the source artwork.

`murdoku_lab/setter/visual_assets.py` selects approved IDs from the catalog; public object
labels use the selected concepts. Selection supports exact formal roles or
standable/blocking classes, with distinct labels within a case. Formal geometry
and grading remain unchanged. Paired exports can use `artwork_style="fluent"`.

See [asset sources and selection](../reference/artwork.md). The frontend preview
at `/art-preview/index.html` is a style gallery; actual query images are generated
by the board renderer.

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

Rendering code lives in `murdoku_lab/visual/art.py`; these scripts provide rendering and demo-verification commands.

## Frontend checks

With the session server running, use `npm run test:browser` and
`npm run test:proxy`. Set `MURDOKU_TEST_URL` for another port. The proxy check
works with bundled demo cases; to also check a generated query gallery, supply
that bundle to the server and set `MURDOKU_TEST_REVIEW_COUNT` to its case count.
