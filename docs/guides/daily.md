# The daily case

[Play guide](play.md) · [Case bundle format](../reference/play-case-format.md) ·
[Setting packs](../reference/settings.md) · [Project](../../README.md)

Daily cases are numbered from the start of a season, with settings rotating between days.
Cases are generated, reviewed and locked before they ship. The player app only reads
the locked, sealed result: nothing is generated or solved in the browser.

Locked cases contain the answers to upcoming days, so they stay out of this repository. They
live in a private dataset, with a local copy in `data/daily/<season>/`, which git ignores
(`MURDOKU_DAILY_DIR` replaces `data/daily`).

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
| `salted_from` | First day whose farm seeds use the private salt.                       |
| `rhythm`     | Board size and difficulty band per weekday.                             |
| `rhythm_from` | Later changes to the weekly rhythm, by the date they start.            |
| `target_cost` | The solver cost each kind of day aims for, such as `"8 hard": 43`.     |
| `special`    | Optional weekday labels, such as `"sunday": "Sunday Special"`.          |
| `settings`   | The setting packs that take turns.                                      |
| `calendar`   | Chosen dates, such as holidays: their `setting`, label (`name`), `title`, `blurb`, `size`, `band`, closing `motive`, and the `objects` and `skins` that rename and redraw prop kinds that day. |

Season `s01` starts on 2026-10-12 with this week:

| Mon      | Tue        | Wed        | Thu      | Fri        | Sat        | Sun                     |
| -------- | ---------- | ---------- | -------- | ---------- | ---------- | ----------------------- |
| 6×6 easy | 6×6 medium | 7×7 medium | 7×7 hard | 8×8 medium | 8×8 medium | 9×9 hard, Sunday Special |

From 2026-11-09 Saturday is 8×8 hard, so the week has two peaks: it warms up to Thursday, eases
on Friday and builds to the weekend. Holidays ease off to medium boards that visitors can
finish in one sitting.

Each week the settings are shuffled with a seed derived from the season and week, so no
setting repeats within a week and a week never opens with the setting that closed the
week before. A calendar day swaps its setting onto its date within the week. An entry can
name only a `setting`, to keep a swap from putting one setting on two days running.

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
python -m murdoku_lab.setter.daily fetch --through 2026-11-20    # download the days due by then
python -m murdoku_lab.setter.daily release --out SITE --site-url URL   # fetch and build what is due
```

**generate** farms candidates for every planned day that has none, with the
constraint-first farm, the player rhythm policy (`config/rhythm/player.json`) and the
cozy scene spec. A day's farm seed is `sha256("murdoku/daily/v1/<date>/<j>")` (j = 0 for the
first batch, higher j for top-ups), so any day can be regenerated exactly. From `salted_from`
on, that text is prefixed with the private salt in `<season>/seed_salt.txt`, so the public code
cannot reveal upcoming cases, and these commands refuse to farm those days without it. Create
the salt once for a new season with `python -c "import secrets; print(secrets.token_hex(32))"`
and keep it with the private dataset. Fourteen days take about two minutes on an Apple M4.
Candidates land in `data/daily/<season>/candidates/<date>.jsonl`.

**review** lists one day's candidates with the murderer, clue count, certificate cost and
depth, and the predicate kinds of each statement. To play them before choosing, load the
candidate file in the Lab, where they appear undressed as `import-1`, `import-2`, …:

```bash
python -m murdoku_lab.visual.server --records data/daily/s01/candidates/2026-10-15.jsonl
```

A locked day can be played as it will ship with the local release and `?date=` or
`?unlock=all` (below).

**pick** records a reviewer's choice in `picks.json`. Without a pick, `lock` takes the
candidate nearest the day's target difficulty that keeps the variety rules.

**lock** dresses and freezes, in date order, every planned day that has been generated and
has no lock yet. Earlier locks never change, and it stops at the first day it cannot fill,
so the locked days never leave a gap. To redo a day, delete its entry in `lock.json` and its
`days/<date>.json`: `lock` fills it in again and checks it against the days on both sides. For
each day it:

1. takes only a candidate in which every living suspect has a statement, as in the original
   game, and keeps to the variety rules: a room layout not used anywhere in the season, and a
   murderer letter different from the days beside it. When no candidate fits, or the day came
   out with none, it farms two more from further seeds, up to three times, and it stops if no
   candidate gives every suspect a statement;
2. dresses the case in the day's setting, with a title that neither an earlier daily case nor
   the frozen showcase (`content/showcase/`) uses for that setting, and preferably a victim who
   does not appear within five days. A calendar day keeps its own title and blurb. Any
   other day takes the in-season title whose season ends soonest, so dated titles land on
   fitting days and timeless ones are kept for when nothing else suits;
3. writes `days/<date>.json` (case and theme), adds the candidate, seed, dressing salt,
   content hash, git revision and OR-Tools version to `lock.json`, and registers the
   content hash in `content/daily/published.json`.

Query and dataset exports (`setter/export_queries.py`) skip every case in
`published.json`, so the daily cases never become training data.

**status** shows each day's candidates and lock.

Each pack has thirty-four titles and eight blurbs. A setting comes round at most 28 times in
the thirty-week season and the showcase uses three more titles, so a season fits without
repeats; add titles before planning a longer one.

**build** reads the locked days in `data/daily/` (up to `--through`, if given) and writes what
the player app reads. It rebuilds their exported assets without generating new puzzles or
re-theming the locks, and stops with an error before touching its output if it finds no days:

| Output                                  | Contents                                                   |
| --------------------------------------- | ---------------------------------------------------------- |
| `web/public/daily/manifest.json`        | `murdoku.daily_manifest/1`: the season's locked days       |
| `web/public/daily/daily-<n>.json`       | The case bundle, sealed with the day's date                |
| `web/public/daily/daily-<n>.{day,night}.svg`, `.thumb.svg` | Static scene and library thumbnail       |
| `web/public/og/<n>.png`                 | 1200×630 share image (title, setting, size, UNSOLVED stamp) |
| `web/public/d/<n>/index.html`           | Link-preview page with Open Graph tags; opens `?d=<n>`     |

`--site-url` makes the share links and preview images absolute. The local release passes
the address it serves on. These folders are build output and are not committed. The same
locked days always build to byte-identical files.

## In the player

The homepage places the daily case and its date picker on the right of the opening
section. The workshop introduction and main generated-case action remain on the left.
The picker defaults to today's case when the current UTC date is in the published
season. Previous/next buttons and a native range slider let players browse dates;
**Today** returns to the current day's case. Browsing dates does not change the current
day or unlock future cases. A published day's case unlocks at midnight UTC.

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
`content/showcase/player-bundles.jsonl`, five classics and one training case), the brand assets
and a design-token check. It reads versioned release content without requiring
`outputs/showcase/`, generating new puzzles or re-theming the frozen cases. The local release
adds any daily cases in `data/daily/`, with share links for the chosen address. Without them it
builds a player with no daily section.

The local release then runs Vite and serves the player at `/` and the research Lab at
`/lab/`. Use `--no-build` to serve the last build and `--port` to change the port.

The production build uses the same frozen content, leaves daily cases out so no future case
ships, and includes the standalone Pyodide Lab:

```bash
python scripts/build_play.py --site-url https://everywheresafety.github.io/murdoku/play/
```

Copy the contents of `dist/` over the website checkout's `murdoku/play/`
(`../site/murdoku/play/` in the paired checkout), keeping its `daily/`, `og/` and `d/` folders.
The player and daily share links use
`/murdoku/play/`; the Research Lab lives at `/murdoku/play/lab/`. Old `/murdoku/exp/`
links redirect to the player with query parameters and fragments preserved.

For temporary previews, `scripts/package_preview.py --site PREVIEW_BASE` still creates a
smaller player package with `noindex`. Pass
`--lab https://everywheresafety.github.io/murdoku/play/lab/` so the preview opens the
Research Lab directly. Use a separate preview address; `/murdoku/exp/` is the old-link
redirect. None of these build commands publishes the output.

## Daily release

Locked cases stay private until they are due. The website repository's scheduled workflow
(`.github/workflows/murdoku-daily.yml`) runs once a day and:

1. checks out the website and this repository's `main`;
2. runs `daily release`, which downloads only the days due from the dataset named in the
   season's `dataset` (repository and pinned revision) and rebuilds them with `build --through`;
3. commits whatever changed under `murdoku/play/daily`, `og` and `d`, normally one new case.

**Timing.** A case unlocks at midnight UTC for every player, whatever their time zone. GitHub can
delay or drop scheduled runs, so each run releases through two days ahead and one missed run leaves
no gap. The player keeps a case locked until its date, so the time the job runs does not change when
players see a case. Run the workflow by hand to catch up. Leave its `through` input empty unless you
mean to publish further ahead: the site is public, so anyone can read a released case early.

**Failures.** The job fails if the dataset lacks a day that is due, or if the cases end within the
two days it releases ahead, and GitHub emails whoever last edited the workflow. A failed run
publishes nothing, so the site keeps the days already released while you add more. The job warns
once fewer than 30 days of cases remain.

**Setup**, once. It needs no stored secret. On the dataset's Hugging Face page, someone with
write access opens **Settings → Trusted Publishers** and adds GitHub Actions with repository
`EverywhereSafety/EverywhereSafety.github.io`, branch `main` and workflow `murdoku-daily.yml`, and
ticks **Read-only**. The job then gets a one-hour token that can only read this dataset, and a run
from any other repository or branch is refused. On GitHub it uses its own `GITHUB_TOKEN`, with the
permissions the workflow file declares, and its push starts the usual GitHub Pages build. Once the
workflow is merged, run it by hand and check that its commit reaches the site.

**A new batch.** Generate and lock in `data/daily/`, then upload the result as one commit:

```bash
hf upload EverywhereSafety/murdoku-daily data/daily . --repo-type=dataset --exclude ".cache/*"
```

Then open a pull request here that sets the season's `dataset.revision` to that commit and
includes the updated `content/daily/published.json`, which lists the new cases' content hashes.

## Checks

```bash
python -m pytest tests/test_daily.py tests/test_play_export.py
npm run test:engine        # streaks, numbering, share line, seal vectors
npm run test:play          # needs a build; opens today, checks locked days, solves a daily case
```
