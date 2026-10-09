# Reasoning profiles

Describe how a puzzle progresses through the existing deduction engine. Profiles
measure the deduction engine’s progress through a puzzle.

## Profile a case

```python
from murdoku_lab.core.instance import Case
from murdoku_lab.solver.reasoning_profile import profile_case, clue_ablation

case = Case.from_json(row["query"]["murdoku_case"])
profile = profile_case(case)
ablations = clue_ablation(case, exact_time_limit_s=0.5)
```

Use `order` and `seed` to compare deduction schedules. Profiles measure the
solver's progression; player experience can differ. Clue ablation removes each
clue and checks the resulting deduction and uniqueness outcomes.

## Measurements

| Field | Definition |
| --- | --- |
| `first_placement_delay` | Non-placement steps before the first registered placement, excluding setup. |
| `first_determination_step` | First state with a newly singleton character domain; may be setup at step 0. |
| `placement_gap_*` | Median, P90 and maximum non-placement steps between registered placements. |
| `determination_gap_max` | Longest gap between states gaining a new singleton. |
| `longest_placement_run` | Longest consecutive run of registered placements. |
| `max_newly_determined` | Largest number of new singleton domains from one post-setup step. |
| `setup_uncertainty_fraction_removed` | Fraction of board-only candidate uncertainty removed by unary setup. |
| `probe_steps` | Successful probe elimination steps; distinct from whether probe is required. |
| `probe_attempts` | Candidate assumptions actually passed to cheap propagation, including unsuccessful attempts. |
| `probe_contradictions` | Assumptions whose propagation found a contradiction. |
| `probe_max_assumption_depth` | 0 when no probe runs, 1 for the current non-nested probe engine. |
| `verdict_reveal_determined_fraction` | Fraction of singleton character domains when conservative murderer support first has one member. |

Candidate uncertainty is `U(t) = sum_i (len(C_i(t)) - 1)`. Its trajectory uses
observed domain changes, not the approximate removal count printed in a step.
Record both determined positions and registered placements: final bookkeeping
can register positions that were already determined earlier.

### Opening witnesses

For every singleton produced in unary setup, search subsets of up to three
presented clues for the smallest combination that already isolates that
character. Store the minimum count and one witness's clue IDs. A missing witness
beyond the cap is explicit. This measures unary opening combinations; it is not
a dependency graph or a minimum proof for relational/advanced deductions.

### Verdict support

A unique full puzzle logically determines its murderer from the start. Full-clue
exact solving therefore cannot measure when the verdict becomes available along
a deduction trace.

Instead, derive support from current candidate domains and the classic game
rules. A suspect must have a row/column-compatible cell pair with the victim in
one area, while every other character has a candidate outside that area. This
ignores joint feasibility among all other characters, so support is a superset
of feasible murderers. One supported suspect establishes availability from
those domains; several supported suspects do not establish genuine ambiguity.
Other murderer-rule variants leave this metric unset.

The hidden answer is not read by scheduling, opening analysis or support
inference. It is used afterwards to check that the final placement matches and
that no observed domain removed an intended solution cell.

Compare solved status before comparing step counts: an unsolved ablation may
stop early. Keep answer-side traces separate from model-facing observations.

## Generated query sample

The README figure profiles 96 generated training cases: 12 cases for each
combination of board size 6–9 and difficulty label medium/hard. The source pool
contains 698 unique training cases. Text and visual views are deduplicated by
`Case.content_hash()` before sampling.

Within each size/label group, sort by formal case ID, shuffle with
`random.Random(20261009)`, and take the first 12. All 96 sampled cases complete
under the canonical deduction engine, match the stored solution, and retain its
cells at every observed deduction state. Labels are the generator's difficulty
bands. The measurements describe deduction steps, rather than model tokens or
player time.

![Measured puzzle rhythms](../assets/puzzle-rhythm.png)

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

Each table entry is the median across 12 cases. The first two plot panels show
medians with 25th–75th percentile whiskers. The third panel normalizes each case's
trace to 0–100% progress, samples its latest observed state at each percentage,
and summarizes the fraction of characters whose candidate domains are singletons.
Lines show medians; shading shows the middle 50%. Normalization compares the
shape of discovery, not total solving effort.

[Download aggregate measurements and plotted curves](../assets/puzzle-rhythm.json).

To reproduce the analysis with a unified dataset, deduplicate its training
queries, use the sampling rule above, and call `profile_case(case)` for each case.
The table uses `first_determination_step`, `determination_gap_max` and
`longest_placement_run`. Use `trace[*].determined` for discovery curves.
