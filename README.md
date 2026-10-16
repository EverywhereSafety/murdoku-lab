<div align="center">

<img src="docs/assets/hero.png" width="100%" alt="Murdoku Lab — A PUZZLE WORKSHOP FOR HUMANS AND AGENTS">

# Murdoku Lab

[![Queries](https://img.shields.io/badge/Queries-Text_%2B_Vision-0F766E?style=flat-square)](#export-text-and-vision-queries) [![Models](https://img.shields.io/badge/Trained_solver-4B-D97706?style=flat-square)](docs/guides/model.md)

[Play now](https://everywheresafety.github.io/murdoku/play/) · [Website](https://everywheresafety.github.io/murdoku/) · [Blog](https://everywheresafety.github.io/blog/treasure-hunt/) · [Generate](#generate-and-solve) · [Data](docs/guides/data.md) · [Trained example](#trained-example-a-small-model-solving-larger-puzzles) · [Agent Horizon](https://github.com/EverywhereSafety/agent-horizon)

</div>

**Murdoku Lab is a setter, solver and playable environment for Murdoku-like
logic puzzles.** Generate boards and clues, check their solutions, play them in
the illustrated frontend, or export them as verifiable agent-training tasks.

For players: **more detective puzzles to play, create and analyze**. Explore
illustrated scenes, work through the clues, and inspect the deductions behind a
solution. See [what makes a puzzle satisfying](#what-makes-a-puzzle-satisfying).

For researchers: **diverse agentic RL queries with rich semantics**,
stateful tools, and paired text or visual observations. Following [VHD-Play](https://arxiv.org/abs/2609.27321),
solutions are established before the LLM setter adds the setting and story,
providing **gold rewards** for training.

![Semantic setter, paired queries, agent interaction and verification](docs/assets/semantic-pipeline.png)

Read the motivation: **[How we solved the Treasure Hunt in 20 minutes](https://everywheresafety.github.io/blog/treasure-hunt/)**.

## Features

| Component            | What you can do                                                                                 |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| Setter               | Generate boards up to 24×24 with scene roles, semantic themes and verified solutions                       |
| Solver               | Verify accepted cases with CP-SAT and independent DFS; inspect deduction and difficulty signals |
| Player app           | A daily case, graded hints, a coached training case and eight illustrated settings, as a static web app |
| Research Lab         | Place characters with row/column exclusions, personal notes, clue focus, exports and solver views       |
| Text + vision export | Produce paired inputs for the same verified case: text or board PNG + clues                     |
| Semantic diversity   | Vary settings, cast and scene labels through optional LLM theming                               |
| Agent environment    | Execute stateful tools and check placement and murderer answers                                 |
| Rollout replay       | Check model trajectories against the executable environment                                     |

## Play, create, analyze

Explore the [Murdoku Lab website](https://everywheresafety.github.io/murdoku/)
for the illustrated casebook and project resources. Place the cast on the board,
follow the evidence, and identify who was alone with the victim.

[![The playable casebook: board, clues and characters](docs/assets/play-preview.png)](https://everywheresafety.github.io/murdoku/)

Generate more cases with the setter, inspect solver deductions and difficulty
profiles, or bring your own cases into the frontend. See [playing and hosting](docs/guides/play.md).

## Experimental Play

An experimental version of Play is in preview at
[everywheresafety.github.io/murdoku/exp/](https://everywheresafety.github.io/murdoku/exp/),
next to the current casebook. It is a static web app that plays the same verified
puzzles without loading Python, and the research casebook moves to `/lab/` in the same
build. A daily case is one of its features:

| Feature | What it does |
| --- | --- |
| Board | Pick a suspect and tap a square; rows, columns and clashes update at once; notes, undo, drag and keyboard play |
| Training case | A coach walks a first case one deduction at a time |
| Hints | Three levels, from a nudge to the square itself, from solver data computed offline |
| Daily case | A new case every day, planned by season, reviewed and locked ahead; streaks and a spoiler-free share line |
| Settings | Eight illustrated settings, from a manor and an ocean liner to a night train and a college library |
| Large classics | The 16 × 16 estate and 24 × 24 museum, drawn in their own themes |
| Results | The reveal, a closing paragraph, stars and a share card |

![Eight settings of the experimental Play](docs/assets/play-exp-settings.jpg)

### How the art is made

- **Drawn as code.** Boards, furniture, characters and cards are SVG generated from the
  public observation by `murdoku_lab/visual/art/` (the `casebook` style). There are no
  bitmap or icon-pack assets, and the same drawings serve the game, case pages and
  image exports. Fonts are OFL (Newsreader, DM Sans, DM Mono) and colours follow the
  Everywhere Safety palette; the fonts are bundled so exported PNGs match on every machine.
- **Board.** A 3/4 "dollhouse" view: floor finishes and colourways per room, walls with
  caps and skirting, wallpaper on the wall faces, brass door thresholds, numbered room
  plaques and a frame for each setting. Touching rooms get floors far enough apart in
  colour to tell them apart.
- **Furniture and objects.** Each prop kind has a base drawing (`art/props.py`, 27 kinds),
  and setting packs add skins (`art/skins/<setting>.py`, 77 so far): deck chairs and a
  lifeboat aboard the liner, a sarcophagus and a meteorite in the museum, a snowmobile at
  the chalet. All follow one recipe, drawn in the footprint's frame with light from the
  upper left, 2.2 px ink outlines and a soft shadow, with tall pieces rising up to 36 px
  above their squares. Each was rendered beside its neighbours (`scripts/art_gallery.py`)
  and redrawn until it read at board size.
- **Mascot.** Everywhere Safety's mark, the sprinkled donut and its white rice-ball
  friend, is kept exactly as it is, plus one thing: a deerstalker on the donut. Its four
  poses (idle, thinking, pointing, celebrating) come from `art/brand.py`, and
  `scripts/build_brand_assets.py` writes the favicon and app icons from them.
- **People.** Portraits come from a generated roster of looks (`art/portraits.py`),
  assigned so a name always has the same face. Suspects A–H are a recurring cast
  (`resources/cast.json`), and the victim is always one of the Vane family.
- **Settings.** A setting pack (`setter/settings/<id>.json`) is data: room names with the
  furniture they suit, a noun and a drawing for each prop kind, wallpapers, floors, a
  frame and an accent colour, titles, spoiler-free blurbs and closing paragraphs.
  `settings.dress()` names each room after the furniture inside it and never changes the
  puzzle, since the content hash ignores themes. See [setting packs](docs/reference/settings.md).
- **Cases with their own theme.** The large classics keep every word they were written
  with. A restyle (`setter/restyles/`) only picks drawings that still show each noun in
  the setting's manner (the museum's "bed" is an antique four-poster, never a
  sarcophagus) and a floor and wallpaper for each room by name.
- **Share cards** put the same drawings in a sticker style (`art/cards.py`) and show
  public facts only.
- **Checks.** `scripts/check_vision_legibility.py` gates the art: text contrast, colour
  distance between touching rooms, coordinate size at export widths, and that no two
  drawings in a setting look alike. The older styles behind published datasets are frozen
  byte for byte (`tests/test_legacy_art.py`).

Along the way the board moved from flat stickers to the 3/4 view, with stickers kept for
share cards; a snail detective gave way to the Everywhere Safety mark; and every case got
a setting of its own rather than one shared look.

Try it locally with `npm run release:local`, or build a zip for testers with
`npm run package:preview`; see [playing and hosting](docs/guides/play.md),
[the daily case](docs/guides/daily.md) and [the player case format](docs/reference/play-case-format.md).

## From a puzzle to an agentic RL query

**Verified puzzle → semantic setting → text / visual query → agent interaction → gold reward.**
The formal solver establishes the solution first. The LLM setter adds varied
settings, cast and scene labels; both query views retain the same puzzle dynamics
and reward reference.

![Generated scenes with different settings, casts and colorful objects](docs/assets/semantic-diversity.png)

| Artifact              | What it contains                                                                       |
| --------------------- | -------------------------------------------------------------------------------------- |
| Verified puzzle       | Board, objects, clues, unique solution and deduction certificate                       |
| Themed case           | Setting, character names, room names and object labels                                 |
| Text / visual query   | Public observations, tool interface and environment record; visual inputs include PNGs |
| Query + model rollout | Query, assistant/tool interaction and verifier outcome in one JSONL record             |

See [generation and query export](docs/guides/queries.md),
[artifact formats and datasets](docs/guides/data.md), and
[reasoning analysis](docs/reference/reasoning-profiles.md).

## Install

Python 3.11+ is required. Node.js and npm are needed for the frontend and PNG
export. Standalone generation and solving run on CPU; no model endpoint is needed.

```bash
git clone https://github.com/EverywhereSafety/agent-horizon.git
git clone https://github.com/EverywhereSafety/murdoku-lab.git
cd murdoku-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ../agent-horizon -r requirements.txt
```

The combined install uses the local Agent Horizon checkout; it does not fetch a
floating remote dependency. See [versioned installation](docs/guides/rl.md#install-the-rl-bridge)
for the optional training plugin.

Install `requirements/tools.txt` for scientific Python tool workloads and
`requirements/data.txt` for Hugging Face downloads.

## Generate and solve

```bash
# Generate one small puzzle and print its public description.
python -m murdoku_lab.setter.generate --size 6 --band easy --n 1 \
  --seed 1 --render 1 --out data/cases/demo.jsonl

# Inspect the verified solution.
python -m murdoku_lab.solver.oracle data/cases/demo.jsonl --case-index 0
```

Use `--size 8 --band medium` to request a larger case.
Use `--llm-theme "a robotics laboratory after a demonstration"` to request
a semantic theme through a configured setter endpoint; see `python -m murdoku_lab.setter.generate --help`. Use `--scene-spec` to
control layout and density; see [generation configuration](docs/guides/queries.md).
Difficulty bands are solver-based labels. The CLI's oracle and diagnostic output
contain answers; keep those separate from model-facing inputs.

## Run the frontend locally

```bash
npm ci
npm run release:local
```

Open **http://127.0.0.1:4173/** for the player (today's case, the training case and the
illustrated cases) and **/lab/** for the research Lab. To play your own cases in the Lab:

```bash
npm run build
python -m murdoku_lab.visual.server --port 8765 --records data/cases/demo.jsonl
```

See [playing and hosting](docs/guides/play.md) and [the daily case](docs/guides/daily.md).

## Export text and vision queries

```bash
python -m murdoku_lab.setter.export_queries \
  --input data/cases/demo.jsonl --out data/paired-queries
```

| Output            | Contents                                         |
| ----------------- | ------------------------------------------------ |
| `text.rl.jsonl`   | Text queries with trusted environment records    |
| `vision.rl.jsonl` | Visual queries with trusted environment records  |
| `public/`         | Model-facing inputs without private answer state |
| `images/`         | Board PNGs referenced by visual queries          |

Both views share `paired_case_id`. Split by case before training so text/vision
variants and rollout attempts remain together. Use
`murdoku_lab.environment.queries.model_inputs(record, asset_root=...)` to resolve images and
extract messages/tools for the model.

![Actual text query excerpt and matching visual board](docs/assets/query-views.png)

## Trained example: a small model solving larger puzzles

The trained solver illustrates how a small 4B model tackles larger structured
puzzles through reasoning and tools. Model rollouts expose the interaction:
board inspection, deductions, code execution, placements and final submission.
Pair each rollout with its exact query and verifier result to inspect the solve.

## Train your own solver with RL

1. Generate semantically diverse queries and freeze case-level splits.
2. Sample model rollouts through the environment's stateful tools.
3. Compute gold rewards with the executable grader and update the policy.
4. Evaluate the trained model on held-out cases.

[Agent Horizon](https://github.com/EverywhereSafety/agent-horizon) provides the
long-horizon training infrastructure on veRL. Its
[Murdoku demo](https://github.com/EverywhereSafety/agent-horizon/tree/refactor/murdoku-demo/examples/murdoku)
connects queries, rollouts and the puzzle grader to training. See
[integration setup](docs/guides/rl.md).

## Queries and model rollouts

The queries can be used directly for **agentic RL**. Each initializes a puzzle
with stateful tools and a gold reward reference. Text and visual queries expose
the same underlying task through different observations.

Use **query + rollout JSONL** for SFT or to inspect model interactions: each record
contains the query and its recorded assistant/tool messages.
Visual records reference PNG assets by relative path. See
[dataset formats](docs/guides/data.md) for schemas and split construction.

[Download queries and rollouts on Hugging Face](https://huggingface.co/datasets/EverywhereSafety/murdoku-lab).

## What makes a puzzle satisfying?

A satisfying detective puzzle invites you in, gives each discovery a consequence,
and ends with a reveal that brings the clues together. We design for four moments:

- **A way in.** Find a promising clue and earn the first placement.
- **Steady progress.** New deductions open possibilities and connect earlier clues.
- **An aha moment.** A tricky combination clicks, unlocking a chain of discoveries.
- **A satisfying reveal.** The final deductions explain who was alone with the victim.

Unique solutions and logical solvability provide the foundation. Our reasoning
profiles examine the path through a puzzle: opening clue combinations, gaps
between discoveries, consecutive placements, shrinking candidate sets and when
the verdict becomes available. Different deduction orders help distinguish a
puzzle's structure from one solver's chosen route.

These measurements let us compare puzzles and explore different rhythms—from a
smooth introduction to a demanding mystery with a decisive breakthrough.
Difficulty describes the challenge; rhythm describes how it unfolds.

### Measuring our generated puzzles

We profiled **96 generated training cases**, with 12 cases in each board-size /
difficulty group. Paired text and visual queries count as one formal puzzle.

![Opening, discovery gaps and progress through 96 generated puzzles](docs/assets/puzzle-rhythm.png)

| Board | Difficulty | First discovery | Longest discovery gap | Longest placement chain |
| --- | --- | ---: | ---: | ---: |
| 6×6 | Medium | 4.5 | 2 | 4 |
| 6×6 | Hard | 8 | 2.5 | 4 |
| 7×7 | Medium | 4 | 3 | 3 |
| 7×7 | Hard | 5.5 | 3.5 | 3 |
| 8×8 | Medium | 2.5 | 4 | 4 |
| 8×8 | Hard | 6 | 2.5 | 3 |
| 9×9 | Medium | 2 | 5.5 | 4 |
| 9×9 | Hard | 2 | 6.5 | 5 |

Values are medians under the canonical deduction solver. First discovery counts
steps to the first determined position; discovery gaps count intervening steps
without a newly determined position; placement chains count consecutive placement
steps. The figure shows medians and the middle 50% of cases.

The 9×9 sample starts quickly but has longer interruptions later. Opening ease
and sustained progress capture different parts of the challenge.

Explore the [measurements and sampling method](docs/reference/reasoning-profiles.md#generated-query-sample)
to analyze your own cases.

## Code and documentation

[Documentation index](docs/README.md)

| Directory                     | Purpose                                       |
| ----------------------------- | --------------------------------------------- |
| `murdoku_lab/core/`           | Puzzle state, constraints and themes          |
| `murdoku_lab/setter/`         | Generation and optional LLM theming           |
| `murdoku_lab/solver/`         | Solvers, deduction and difficulty             |
| `murdoku_lab/visual/`, `web/` | Rendering, sessions and playable frontend     |
| `murdoku_lab/environment/`    | Task state, prompt, tools, rewards and replay |
| `murdoku_lab/evaluation/`     | Benchmark runners, metrics and analysis       |
| `scripts/`                    | Data download and preparation utilities       |

[Architecture and code map](docs/reference/architecture.md) ·
[Formal model](docs/reference/formal-model.md) · [Tool harness](docs/guides/tools.md)

## Acknowledgments

Inspired by **[Murdoku](https://murdoku.com/), by Manuel Garand**. This is an
independent, unofficial project. We also appreciate community tools such as
[Murdoku Playground](https://murdoku-playground.online/about) and
[4color](https://pmlemay.github.io/4color/).
