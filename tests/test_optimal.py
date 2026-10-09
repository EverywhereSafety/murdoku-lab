"""The optimal chain must be a genuine lower bound on the greedy one, and must stay sound."""

import pytest

from murdoku_lab.setter.pipeline import make_case
from murdoku_lab.solver.logic import certify
from murdoku_lab.solver.optimal import optimal_chain


def _cases():
    out = []
    for band in ("easy", "medium", "hard"):
        for seed in (5, 11, 23):
            a = make_case(variant="classic", size=6, band=band, seed=seed, attempts=25)
            if a.case is not None:
                out.append((band, seed, a.case))
    return out


CASES = _cases()


@pytest.mark.parametrize("band,seed,case", CASES, ids=[f"{b}-{s}" for b, s, _ in CASES])
def test_optimal_is_a_lower_bound(band, seed, case):
    """A* searches a superset of the single path greedy walks, so it can never come out dearer."""
    g = certify(case)
    r = optimal_chain(case)
    assert (
        r.cost <= r.greedy_cost + 1e-9
    ), f"optimal {r.cost} exceeded same-scope greedy {r.greedy_cost}"
    assert r.greedy_regret >= 0.0
    if r.greedy_solved:
        assert r.solved, "same-scope greedy solved but the wider search did not"
    assert r.full_greedy_cost == g.cost


@pytest.mark.parametrize("band,seed,case", CASES, ids=[f"{b}-{s}" for b, s, _ in CASES])
def test_optimal_chain_reaches_the_true_solution(band, seed, case):
    """Every technique is sound, so the chain may only ever pin a character where the answer key
    puts them. This is the check that catches an unsound rule sneaking into the ladder.
    """
    r = optimal_chain(case)
    if not r.solved:
        pytest.skip("no solving chain within the ladder")
    truth = case.solution
    for s in r.steps:
        if s.placed:
            who, cell = s.placed
            assert (
                truth[who] == cell
            ), f"{who} pinned to {cell}, answer key says {truth[who]}"


def test_proved_optimal_is_not_claimed_when_budget_runs_out():
    """The flag must be honest: a starved search reports False rather than a bare number."""
    band, seed, case = CASES[-1]
    starved = optimal_chain(case, max_nodes=1)
    assert not starved.proved_optimal
