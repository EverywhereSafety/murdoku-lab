"""Provably minimum-cost deduction chains.

`logic.certify()` is *greedy*: at every state it applies the cheapest technique that fires. That
is a good model of a person and it is what the difficulty bands are calibrated against, but it is
not an optimum — a slightly more expensive step now can unlock a much cheaper remainder.

This module answers the harder question: **what is the cheapest chain that exists?** It runs A*
over deduction states, so the number it returns is a lower bound on what any solver following the
same ladder can achieve, and `certify()`'s cost is an upper bound. The gap between them is
`OptimalResult.greedy_regret`, which is itself informative: a case with a large regret is one where
choosing the right first move matters, i.e. a case that punishes a plausible-looking wrong path.

WHAT IS AND IS NOT PROVED  (read this before quoting the number)
---------------------------------------------------------------
The search space is *sequences of technique invocations*. Each `Deducer.t_*` method returns the
first instance of its technique that fires at the current state, deterministically. So an edge out
of a state is "invoke technique T next", giving a branching factor of at most `len(ladder)`.

  * PROVED: no sequence of technique invocations solves the case for less than `cost`, when
    `proved_optimal` is True (the search closed: A* popped a goal with the frontier's f-value
    already above it, without hitting `max_nodes`).
  * NOT PROVED: optimality over the *full* ladder. `probe` is excluded from the search because A*
    runs every technique at every expanded node and probing costs one propagation per candidate cell;
    including it turned a 90-node search into minutes. The number below is therefore the optimum over
    `techniques() - EXCLUDED_FROM_SEARCH`. `greedy_regret` compares against a greedy run over that
    same restricted ladder; the full-ladder greedy cost is reported separately.
  * NOT PROVED: optimality over *instantiations*. If two different naked subsets fire at one
    state, only the one `t_naked_subset` happens to find first is explored. Widening this needs
    the technique bodies to enumerate rather than return-first; the flag `enumerated=False` on the
    result records that we did not.
  * NOT CLAIMED: that a human could not find a shorter argument using a technique not in the
    ladder. "Optimal" here is always relative to the published ladder.

When `proved_optimal` is False the cost is still a genuine achievable chain (an upper bound), just
not certified minimal; callers that need the guarantee must check the flag.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from murdoku_lab.core.instance import Case
from .logic import TIER_COST, Certificate, Deducer, State, Step

MIN_TIER_COST = min(TIER_COST.values())

# Techniques too expensive to run at every node of the A* search. See `optimal_chain`.
EXCLUDED_FROM_SEARCH = frozenset({"probe"})


def _key(st: State) -> tuple:
    """Identity of a deduction state. Includes `placed`, because a singleton candidate set is not
    the same state as a pinned character: pinning also clears the row and column."""
    return (
        tuple(sorted((x, tuple(sorted(c))) for x, c in st.cand.items())),
        tuple(sorted(st.placed.items())),
    )


def _h(st: State) -> float:
    """Admissible heuristic: every technique invocation pins at most one character, and the
    cheapest invocation costs `MIN_TIER_COST`, so at least one such step remains per undetermined
    character. Never overestimates, so A* stays optimal."""
    return MIN_TIER_COST * sum(1 for c in st.cand.values() if len(c) > 1)


@dataclass
class OptimalResult:
    cost: float
    steps: list[Step]
    solved: bool
    proved_optimal: bool
    nodes_expanded: int
    frontier_left: int
    greedy_cost: float
    greedy_solved: bool
    full_greedy_cost: float
    enumerated: bool = False

    @property
    def full_ladder_optimal(self) -> bool:
        """True only for an exhaustive search over all instances of the complete ladder.

        The current search deliberately excludes probe and each technique returns its first
        applicable instance, so this remains False.  Exposing it prevents callers from promoting the
        narrower `proved_optimal` claim into global human-reasoning optimality.
        """
        return self.proved_optimal and self.enumerated and not EXCLUDED_FROM_SEARCH

    @property
    def greedy_regret(self) -> float:
        """How much the cheapest-first heuristic overpays. 0.0 means greedy was already optimal."""
        return round(self.greedy_cost - self.cost, 3)

    @property
    def depth(self) -> int:
        return len(self.steps)

    def to_json(self) -> dict:
        return {
            "cost": round(self.cost, 3),
            "depth": self.depth,
            "solved": self.solved,
            "proved_optimal": self.proved_optimal,
            "enumerated": self.enumerated,
            "full_ladder_optimal": self.full_ladder_optimal,
            "optimality_scope": "technique invocation order; probe excluded; first instance only",
            "greedy_cost": round(self.greedy_cost, 3),
            "greedy_regret": self.greedy_regret,
            "greedy_solved": self.greedy_solved,
            "full_greedy_cost": round(self.full_greedy_cost, 3),
            "nodes_expanded": self.nodes_expanded,
            "frontier_left": self.frontier_left,
            "steps": [s.to_json() for s in self.steps],
        }


def optimal_chain(case: Case, max_nodes: int = 20000) -> OptimalResult:
    """A* for the min-cost deduction chain. `max_nodes` bounds expansions; exceeding it returns
    the best chain found so far with `proved_optimal=False`."""
    d = Deducer(case)
    full_greedy = d.run()
    greedy = d.run(include_probe=False)

    st0, setup = d.initial()
    base = TIER_COST[setup.tier]
    # `probe` is excluded from the A* ladder. It costs one propagation per candidate cell, and A*
    # runs the whole ladder at every node it expands, which turned a 90-node search into minutes.
    # The consequence is stated rather than hidden: the optimum below is over the ladder MINUS
    # probing, so `proved_optimal` is a claim about that ladder. `certify()` still uses the full one.
    ladder = [t for t in d.techniques() if t[0] not in EXCLUDED_FROM_SEARCH]

    # (f, tie, g, state, steps-after-setup)
    start = (base + _h(st0), 0, base, st0, ())
    heap: list[tuple] = [start]
    best_g: dict[tuple, float] = {_key(st0): base}
    tie = 1
    expanded = 0
    best_goal: tuple[float, tuple] | None = None

    while heap:
        f, _, g, st, path = heapq.heappop(heap)
        if best_goal is not None and f >= best_goal[0]:
            break  # frontier can no longer beat the goal: closed
        if g > best_g.get(_key(st), float("inf")):
            continue  # stale entry
        if st.solved and not st.dead:
            if best_goal is None or g < best_goal[0]:
                best_goal = (g, path)
            continue
        if expanded >= max_nodes:
            break
        expanded += 1

        for _name, tier, fn in ladder:
            nxt = st.clone()
            # the technique methods act on the state they are handed; rebind the Deducer's view
            step = fn(nxt)
            if step is None or nxt.dead:
                continue
            ng = g + TIER_COST[tier]
            k = _key(nxt)
            if ng >= best_g.get(k, float("inf")):
                continue
            best_g[k] = ng
            heapq.heappush(heap, (ng + _h(nxt), tie, ng, nxt, path + (step,)))
            tie += 1

    if best_goal is not None:
        cost, path = best_goal
        closed = not heap or heap[0][0] >= cost
        return OptimalResult(
            cost=cost,
            steps=[setup, *path],
            solved=True,
            proved_optimal=closed and expanded < max_nodes,
            nodes_expanded=expanded,
            frontier_left=len(heap),
            greedy_cost=greedy.cost,
            greedy_solved=greedy.solved,
            full_greedy_cost=full_greedy.cost,
        )

    # no solving chain found: fall back to reporting the greedy attempt, marked unsolved
    return OptimalResult(
        cost=greedy.cost,
        steps=list(greedy.steps),
        solved=greedy.solved,
        proved_optimal=False,
        nodes_expanded=expanded,
        frontier_left=len(heap),
        greedy_cost=greedy.cost,
        greedy_solved=greedy.solved,
        full_greedy_cost=full_greedy.cost,
    )


def optimal_certificate(case: Case, max_nodes: int = 20000) -> Certificate:
    """The min-cost chain packaged as a `Certificate`, so it drops into the same difficulty
    features, renderers and JSON records as `certify()`. Note the band calibration is defined
    against `certify()`; use this to *audit* a case, not to re-label it."""
    r = optimal_chain(case, max_nodes=max_nodes)
    order = [s.placed[0] for s in r.steps if s.placed]
    d = Deducer(case)
    st, _ = d.initial()
    return Certificate(
        solved=r.solved,
        steps=r.steps,
        placed={x: k for s in r.steps if s.placed for x, k in [s.placed]},
        place_order=order,
        stuck={},
        max_width=st.width,
    )
