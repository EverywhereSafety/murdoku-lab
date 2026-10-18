# The daily case

[Play guide](play.md) · [Case bundle format](../reference/play-case-format.md) ·
[Setting packs](../reference/settings.md) · [Project](../../README.md)

Daily cases are numbered from the start of a season, with settings rotating between days.
The current versioned release contains 14 locked cases, dated October 12–25, 2026.
Cases are generated, reviewed and locked before they ship. The player app only reads
the locked, sealed result: nothing is generated or solved in the browser.

```text
plan → generate → review (→ pick) → lock → build → local release
```

## A season

`config/daily/season-<id>.json` fixes everything that does not depend on luck:

| Field        | Meaning                                                                 |
| ------------ | ----------------------------------------------------------------------- |
| `epoch`      | Day of case #1. A case's number is the days since the epoch, plus one.  |
| `start`      | First day this season plans for.                                       |
| `weeks`      | Season length.                                                          |
| `candidates` | Candidates farmed per day.                                              |
| `rhythm`     | Board size and difficulty band per weekday.                             |
| `special`    | Optional weekday labels, such as `"sunday": "Sunday Special"`.          |
| `settings`   | The setting packs that take turns.                                      |

Season `s01` starts on 2026-10-12 with this week:

| Mon      | Tue        | Wed        | Thu      | Fri        | Sat        | Sun                     |
| -------- | ---------- | ---------- | -------- | ---------- | ---------- | ----------------------- |
| 6×6 easy | 6×6 medium | 7×7 medium | 7×7 hard | 8×8 medium | 8×8 medium | 9×9 hard, Sunday Special |

Each week the settings are shuffled with a seed derived from the season and week, so no
setting repeats within a week and a week never opens with the setting that closed the
week before.

## Commands

These commands describe the authoring workflow for preparing future daily content.
Default release builds only export the currently locked cases; they do not run
`generate`, `pick` or `lock`, or change the frozen cases' themes.

All commands take `--season` (default `s01`) and work on the first `--days` days of the
season (default: all of it).

```bash
python -m murdoku_lab.setter.daily plan --days 14        # the calendar: number, size, band, setting
python -m murdoku_lab.setter.daily generate --days 14 --workers 8
python -m murdoku_lab.setter.daily review 2026-10-15     # candidates for one day
python -m murdoku_lab.setter.daily pick 2026-10-15 2     # optional: choose candidate 2
python -m murdoku_lab.setter.daily lock --days 14
python -m murdoku_lab.setter.daily status --days 14
python -m murdoku_lab.setter.daily build                 # → web/public/daily, og/, d/<n>/
```

**generate** farms candidates for every planned day that has none, with the
constraint-first farm, the player rhythm policy (`config/rhythm/player.json`) and the
cozy scene spec. A day's farm seed is `sha256("murdoku/daily/v1/<date>/<j>")` (j = 0 for the
first batch, higher j for top-ups), so any day can be regenerated exactly. Fourteen days
take about two minutes on an Apple M4. Candidates land in
`content/daily/<season>/candidates/<date>.jsonl`.

**review** lists one day's candidates with the murderer, clue count, certificate cost and
depth, and the predicate kinds of each statement. To play them before choosing, load the
candidate file in the Lab, where they appear undressed as `import-1`, `import-2`, …:

```bash
python -m murdoku_lab.visual.server --records content/daily/s01/candidates/2026-10-15.jsonl
```

A locked day can be played as it will ship with the local release and `?date=` or
`?unlock=all` (below).

**pick** records a reviewer's choice in `picks.json`. Without a pick, `lock` takes the first
candidate that keeps the variety rules.

**lock** dresses and freezes every planned day that has candidates and no lock yet. Earlier
locks never change. For each day it:

1. keeps to the variety rules: a room layout not used earlier in the season, and a
   murderer letter different from yesterday's. When no candidate fits, it farms two more
   from further seeds, up to three times;
2. dresses the case in the day's setting, preferring a title that setting has not used yet
   and a victim who has not appeared in the last five days;
3. writes `days/<date>.json` (case and theme), adds the candidate, seed, dressing salt,
   content hash, git revision and OR-Tools version to `lock.json`, and registers the
   content hash in `content/daily/published.json`.

Query and dataset exports (`setter/export_queries.py`) skip every case in
`published.json`, so the daily cases never become training data.

**status** shows each day's candidates and lock.

Each pack has eight titles. A setting comes round about seven times in an eight-week
season, and the showcase uses three more, so add titles to the packs before locking a
whole season, or some titles will repeat.

**build** reads the versioned locked days and writes what the player app reads. It
rebuilds their exported assets without generating new puzzles or re-theming the locks:

| Output                                  | Contents                                                   |
| --------------------------------------- | ---------------------------------------------------------- |
| `web/public/daily/manifest.json`        | `murdoku.daily_manifest/1`: the season's locked days       |
| `web/public/daily/daily-<n>.json`       | The case bundle, sealed with the day's date                |
| `web/public/daily/daily-<n>.{day,night}.svg`, `.thumb.svg` | Static scene and library thumbnail       |
| `web/public/og/<n>.png`                 | 1200×630 share image (title, setting, size, UNSOLVED stamp) |
| `web/public/d/<n>/index.html`           | Link-preview page with Open Graph tags; opens `?d=<n>`     |

`--site-url` makes the share links and preview images absolute. The local release passes
the address it serves on. These folders are build output and are not committed.

## In the player

The homepage places the daily case and its date picker on the right of the opening
section. The workshop introduction and main generated-case action remain on the left.
The picker defaults to today's case when the player's local calendar day is in the
published season. Previous/next buttons and a native range slider let players browse
dates; **Today** returns to the current day's case. Browsing dates does not change the
current day or unlock future cases. A published day's case unlocks at local midnight.

The daily section farther down the page retains the player's statistics and an expandable
season calendar showing each day's stars, missed days and locked dates.

- A **streak** counts days whose case was solved on that same day. Older cases can still
  be played for stars, but they do not extend a streak. An unsolved today does not break a
  streak that ran through yesterday.
- **Stars**: ★★★ with no hints and no wrong verdict; ★★ with hints that never revealed an
  answer and at most one wrong verdict; ★ otherwise.
- **Share** copies a spoiler-free summary: case number, weekday, size and difficulty; one
  square per person (🟩 unaided, 🟨 nudge, 🟧 partial hint, 🟥 revealed); the verdict
  (⚖️✅ first time, ⚖️🔁 with the number of wrong verdicts); stars, hints and the case link.
  It never contains a square, a name or the murderer.

Preview switches, for checking a season locally:

| URL                        | Effect                                    |
| -------------------------- | ----------------------------------------- |
| `?date=2026-10-20`         | Play as if it were that day               |
| `?unlock=all`              | Open every day of the season              |
| `?d=7`                     | Open daily case #7 (subject to the lock)  |

## Local release

```bash
npm run release:local                       # http://127.0.0.1:4173/
.venv/bin/python scripts/release_local.py --lan   # also reachable from a phone on the same Wi-Fi
```

The script's `prepare_assets()` function is also used by `scripts/build_play.py`. Each
default build prepares the full 30-case library (24 themed bundles from
`content/showcase/player-bundles.jsonl`, five classics and one training case), the 14
locked daily cases with share links for the chosen address, the brand assets and a
design-token check. It reads versioned release content without requiring
`outputs/showcase/`, generating new puzzles or re-theming the frozen cases.

The local release then runs Vite and serves the player at `/` and the research Lab at
`/lab/`. Use `--no-build` to serve the last build and `--port` to change the port.
For a standalone static build with a Pyodide Lab, pass the deployment base URL to
`python scripts/build_play.py --site-url PUBLIC_BASE`.

The experimental website package uses the same frozen content:

```bash
python scripts/package_preview.py --site https://everywheresafety.github.io/murdoku/exp/
```

It writes `outputs/site/murdoku/exp/` with `noindex` and a `lab/` link to `../../play/`.
Copying this folder to the site's `/murdoku/exp/` leaves the production `/murdoku/play/`
casebook unchanged. None of these build commands publishes the output.

## Checks

```bash
python -m pytest tests/test_daily.py tests/test_play_export.py
npm run test:engine        # streaks, numbering, share line, seal vectors
npm run test:play          # needs a build; opens today, checks locked days, solves a daily case
```
