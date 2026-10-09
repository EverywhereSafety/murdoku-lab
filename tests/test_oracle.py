"""The public oracle contract keeps exact, human and optimal evidence separate."""

from dataclasses import replace

from murdoku_lab.setter.pipeline import make_case
from murdoku_lab.solver.oracle import solve


def _case():
    a = make_case(
        variant="classic", size=6, band="easy", seed=8000, attempts=30, time_limit_s=5.0
    )
    assert a.case is not None
    return a.case


def test_oracle_is_unique_deterministic_and_independently_checked():
    case = _case()
    a = solve(case)
    b = solve(case)
    assert a.status == b.status == "unique"
    assert a.solution == b.solution == dict(sorted(case.solution.items()))
    assert a.engines_agree is b.engines_agree is True
    assert a.human is not None and a.human.solved


def test_oracle_distinguishes_multiple_from_unique():
    case = replace(_case(), clues=(), certificate=None)
    r = solve(case, cross_check=False, time_limit_s=5.0)
    assert r.status == "multiple" and not r.unique and r.solution is None


def test_optimal_scope_is_not_overclaimed():
    r = solve(_case(), include_optimal=True, max_optimal_nodes=2000)
    assert r.optimal is not None
    d = r.optimal.to_json()
    assert not d["full_ladder_optimal"]
    assert "probe excluded" in d["optimality_scope"]
