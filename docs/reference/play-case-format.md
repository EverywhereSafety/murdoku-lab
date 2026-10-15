# Player case format

[Play guide](../guides/play.md) · [Daily case](../guides/daily.md) ·
[Architecture](architecture.md)

The player app (`web/src/play/`) never runs Python. Every case reaches it as static files
written offline by `murdoku_lab/visual/play_export.py` (library cases) and
`murdoku_lab/setter/daily.py build` (daily cases). Python remains the source of truth: the
JavaScript engine mirrors `VisualSession.act`, and both are pinned by shared fixtures.

## Files

| Path under `web/public/`              | Written by       | Schema / contents                          |
| ------------------------------------- | ---------------- | ------------------------------------------ |
| `cases/index.json`                    | `play_export`    | `murdoku.play_library/1`                   |
| `cases/<id>.json`                     | `play_export`    | `murdoku.play_case/1`                      |
| `cases/<id>.day.svg`, `.night.svg`    | `play_export`    | Static scene for each colour theme         |
| `cases/<id>.thumb.svg`                | `play_export`    | 320 px library thumbnail                   |
| `daily/manifest.json`                 | `daily build`    | `murdoku.daily_manifest/1`                 |
| `daily/daily-<n>.json` (+ scenes, thumb) | `daily build` | `murdoku.play_case/1` with a `daily` field |
| `og/<n>.png`                          | `daily build`    | 1200×630 share image                        |
| `d/<n>/index.html`                    | `daily build`    | Link-preview page that opens `?d=<n>`      |

All of these are build output (git-ignored). Paths inside the files are relative to their
own folder, so one build works at `/`, under a path prefix or from a LAN address.

## Library: `murdoku.play_library/1`

```json
{"schema": "murdoku.play_library/1", "cases": [
  {"id": "tutorial", "kind": "tutorial", "title": "…", "blurb": "…",
   "setting": {"id": "manor", "name": "Training case"}, "size": "6×6",
   "difficulty": {"band": "easy", "label": "Easy", "minutes": [2, 6]},
   "people": 6, "rooms": 5, "accent": "#3d6a5b", "goal_type": "murderer",
   "content_hash": "…", "thumb": "tutorial.thumb.svg", "url": "tutorial.json"}
]}
```

`kind` is `tutorial` (the coached training case), `classic` (the four built-in cases) or
`themed` (dressed records, such as the setting showcase). The library can draw every card,
including its progress stamp, without loading a case.

## Daily manifest: `murdoku.daily_manifest/1`

```json
{"schema": "murdoku.daily_manifest/1", "season": "s01", "epoch": "2026-10-12", "days": [
  {"n": 1, "id": "daily-1", "date": "2026-10-12", "weekday": "monday", "special": null,
   "title": "…", "blurb": "…", "setting": {"id": "glasshouse", "name": "…"},
   "size": "6×6", "difficulty": {…}, "accent": "#2f7d5f",
   "content_hash": "…", "thumb": "daily-1.thumb.svg", "url": "daily-1.json"}
]}
```

The manifest lists the whole locked season, so the calendar can show future days as
locked. The app decides which days open from the player's local date.

## Case bundle: `murdoku.play_case/1`

| Field          | Contents                                                                         |
| -------------- | -------------------------------------------------------------------------------- |
| `schema`       | `murdoku.play_case/1`                                                            |
| `id`           | Stable case id: `tutorial`, a classic slug, a 12-hex id, or `daily-<n>`           |
| `kind`         | `tutorial`, `classic`, `themed` or `daily`                                        |
| `locale`       | `en`                                                                              |
| `content_hash` | Hash of the formal case; saved progress is dropped when it changes               |
| `meta`         | Title, blurb, eyebrow, `setting {id, name}`, size, width, height, people, rooms, `difficulty {band, label, minutes}`, accent, frame |
| `public`       | The public observation (below)                                                   |
| `scene`        | `{day, night}`: scene file names                                                 |
| `thumb`        | Thumbnail file name                                                              |
| `share`        | Daily only: `{url, og_image}`                                                    |
| `ai_results`   | Reserved for "Can AI solve it?" results; `null` for now                          |
| `secret`       | The sealed answers (below)                                                       |
| `daily`        | Daily only: `{n, date, weekday, season, special}`                                |

### Public observation

`public` is `murdoku_lab.visual.projection.public_observation` (`murdoku.observation/1`)
without the session fields (`session_id`, `revision`, `notebook`, `done`, `terminal`,
`can_undo`, `can_redo`, `last_event`, `placements`, `marks`). It holds:

- `title`, `blurb`, `eyebrow`, `setting`, `variant`, `goal_type`, `goal` and `rules`;
- `scene`: `width`, `height`, `cells` (label, row, column, area, terrain, prop, standable,
  walls), `areas` (id, number, name, colour), `props` (id, name, art, standable, cells),
  `terrains`, `doors` and `visual` (the setting's colours, finishes, wallpapers, frame and
  skins);
- `people`: id, name, victim flag, colours, `look` (portrait index) and `face` (the
  portrait's SVG markup, so the app draws faces without the portrait code);
- `clues`: id, number, holder (`null` for scene facts) and text.

Nothing in `public` is derived from the solution. `tests/test_play_export.py` checks that no
answer appears in the clear.

### Sealed secret

```json
{"alg": "murdoku.seal/1", "data": "<base64>"}
```

`data` is the JSON below, XORed with a mulberry32 keystream seeded by FNV-1a over
`"<id>|<salt>"` and base64-encoded. The salt is the date for daily cases and empty
otherwise. This only prevents accidental spoilers, such as a glance at the network panel
or a search snippet; anyone determined can unseal a static file.
`murdoku_lab/visual/seal.py` and `web/src/play/engine/seal.js` implement the same steps,
pinned by `tests/fixtures/seal_vectors.json`.

| Field         | Contents                                                              |
| ------------- | --------------------------------------------------------------------- |
| `goal_type`   | `murderer`, `victim_cell` or `placement`                              |
| `solution`    | Person id → cell label (`"c4"`)                                       |
| `victim_cell`, `victim_area` | Where the victim was found                             |
| `murderer`    | Person id for `murderer` goals, otherwise `null`                      |
| `epilogue`    | The closing paragraph from the setting pack, or `null`                |
| `hints`       | `order`, `candidates`, `forbid` (below)                                |

### Hint data

Hints are computed offline because the solver needs OR-Tools.

- `order`: the order in which pure deduction places people (`certify(case).place_order`).
  The first person in it whom the player has not placed can always be deduced from the
  clues and the people before them.
- `candidates`: person → squares their own statements allow.
- `forbid`: person → square → the number of the statement that rules it out.

`web/src/play/engine/hints.js` turns these into graded hints, one level deeper each time
the player asks about the same target:

- a person placed wrongly: something is off → look at this person → the statement that
  rules out their square (`forbid`) → the right square, with a button that moves them;
- otherwise the next person in `order`: read their statement → their room (or their row,
  when their statements already pin the room) → their square, with a button;
- everyone placed correctly: who shares the victim's room → look only at that room → the
  murderer's name.

Only the last level of each target counts as a reveal when stars are awarded.

## Scenes

Scene SVGs are `casebook.scene_svg(..., layers=STATIC_LAYERS, cell_labels="none",
backdrop=False)`: floors, walls, doors, furniture, room plaques and the setting's frame,
in the board coordinate system (`CELL=100`, `PAD=40`). The app injects the scene once and
draws people, notes, crosses, conflicts, highlights and axis letters in an overlay with
the same coordinates. Geometry and colours shared by both sides are generated into
`web/src/generated/tokens.{json,css}` by `murdoku_lab.visual.art.design_tokens --write`;
`--check` fails when they drift.

## Local saves

Progress stays in the browser's `localStorage`. Nothing is sent anywhere.

| Key                      | Contents                                                                 |
| ------------------------ | ------------------------------------------------------------------------ |
| `murdoku:v1:profile`     | `settings` and `daily` (per case number: date, day solved, stars, hints, wrong verdicts, time) |
| `murdoku:v1:case:<id>`   | `content_hash`, the move batches (replayed on load), time, wrong verdicts, hints and the finished result |

A case record whose `content_hash` no longer matches the bundle is ignored, so a rebuilt
case starts fresh instead of replaying moves on the wrong board.

## Compatibility

New optional fields may be added to any of these schemas. Removing or changing the meaning
of a field requires a new schema version (`/2`).
