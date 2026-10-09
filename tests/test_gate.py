"""Everything the setter emits must survive independent re-verification."""

import pytest

from murdoku_lab.setter.pipeline import gate, make_case


@pytest.mark.parametrize("band", ["easy", "medium"])
def test_emitted_cases_pass_the_gate(band):
    a = make_case(
        variant="classic", size=6, band=band, seed=9000, attempts=30, time_limit_s=5.0
    )
    if not a.ok or a.case is None:
        pytest.skip(f"no {band} case within the attempt budget")
    g = gate(a.case, expect_band=band)
    assert g.ok, f"gate rejected an emitted case: {g.failed} / {g.detail.get('band')}"
    assert g.checks["independent_solver_agrees"]


def test_gate_catches_a_tampered_solution():
    a = make_case(
        variant="classic", size=6, band="easy", seed=9100, attempts=30, time_limit_s=5.0
    )
    if not a.ok or a.case is None:
        pytest.skip("no case")
    from dataclasses import replace

    bad_sol = dict(a.case.solution)
    xs = list(bad_sol)
    bad_sol[xs[0]], bad_sol[xs[1]] = bad_sol[xs[1]], bad_sol[xs[0]]
    g = gate(replace(a.case, solution=bad_sol, certificate=None), expect_band="easy")
    assert not g.ok, "the gate accepted a case whose recorded solution was swapped"


def test_round_trip_json():
    a = make_case(
        variant="classic", size=6, band="easy", seed=9200, attempts=30, time_limit_s=5.0
    )
    if not a.ok or a.case is None:
        pytest.skip("no case")
    from murdoku_lab.core.instance import Case

    back = Case.from_json(a.case.to_json())
    assert back.content_hash() == a.case.content_hash()
    assert back.satisfies(back.solution)
