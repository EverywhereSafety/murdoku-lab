# Formal puzzle model

Murdoku is a permutation-placement constraint problem with a verdict derived
from the placement. Names, settings and artwork render this formal structure.

## Board and props

`murdoku_lab.core.board.Scene` defines width, height, area membership, terrain, object
footprints and doors. A prop has an ID, standability, occupied cells and an
optional landmark attribute. Its public label and illustration come from a theme.

A person can occupy a standable square. Object footprints may cover several
squares. `on` tests membership in the footprint. `beside` tests orthogonal
adjacency within the same area. Terrain and named props are separate layers.
Doors connect adjacent squares but preserve their area identities.

## Placement

`murdoku_lab.core.instance.Case` defines characters, victim, tags, clues and answer type.
A placement maps each character to a board cell. The base rules enforce usable
cells and unique rows and columns. Variant definitions select additional rules,
clue families and supported sizes.

Classic puzzles identify the person alone with the victim: exactly those two
characters occupy the same area. Other variants define their own answer predicate.
The case stores the verified arrangement and requested answer for the trusted grader.

## Clues

`murdoku_lab.core.atoms` defines executable predicates. A clue contains one or more atoms;
all of its atoms apply. Unary masks restrict character domains, relational atoms
link characters, and global atoms constrain the joint placement.

Each predicate has a direct evaluator and a matching exact-solver encoding.
`murdoku_lab.solver.exact` implements CP-SAT constraints and independent DFS counting.
The deduction engine applies sound domain reductions through a ranked technique
ladder. See `tests/test_encoding_agreement.py` and the solver tests for agreement
and deduction checks.

## Generation and admission

The setter supports placement-first and constraint-first search. Placement-first
samples an arrangement, derives true clues and carves them. Constraint-first
selects constraints and searches for an arrangement they determine.

`murdoku_lab.setter.pipeline.gate` checks the recorded case against its formal constraints,
solution, clue quality and difficulty. Generated cases carry a deduction
certificate. Solver calls have explicit search and time budgets; a timeout is
recorded separately from a proven count.

## Difficulty and reasoning

`murdoku_lab.solver.logic` produces a deduction certificate with step kinds, tiers, remaining
candidate width and placement order. `murdoku_lab.solver.difficulty` maps certificate
properties into configured bands. Bands describe the chosen deduction engine;
[reasoning profiles](reasoning-profiles.md) measure opening delay and progress gaps.

`murdoku_lab.solver.optimal` searches for a minimum-cost chain over its declared technique
schedule. `proved_optimal` records whether the search completed its bound; node
budgets can leave the proof incomplete. Technique cost is ordinal. The supported
technique schedule determines the scope of the optimum.

## Semantic presentation

`murdoku_lab.core.theme.Theme` maps formal IDs to names, pronouns, areas, object labels and
attributes. `Theme.assets` stores selected artwork IDs. The semantic setter runs
after the solution is established. Text and image rendering use the same theme.
Theme validation and invariance tests preserve the formal structure and solution.

## Case record

`murdoku.case/1` is serialized by `Case.to_json` and `Case.from_json`:

| Field | Meaning |
|---|---|
| `scene` | Geometry, areas, props, terrain and doors |
| `characters`, `victim`, `tags` | Cast and formal attributes |
| `clues` | Predicate groups |
| `solution`, `answer`, `answer_key` | Trusted arrangement and verdict |
| `seed`, `target_band`, `certificate`, `meta` | Generation and verification metadata |

Query exports add public messages, tool schemas, observation type and theme.
`murdoku_lab.environment.queries.model_inputs` builds requests from the public fields. The
trusted environment receives the formal case for scoring.

[Architecture](architecture.md) · [Generate queries](../guides/queries.md) ·
[Artifact formats](../guides/data.md)
