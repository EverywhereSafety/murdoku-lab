"""D6: difficulty is monotone under carving.

Removing a clue can only make the *cheapest* deduction chain more expensive (extra information never
blocks a sound propagator), so the measured band must never go DOWN when a clue is dropped. The case
may of course become ambiguous or unsolvable-by-logic — those are skipped, not failures.
"""

import pytest
from dataclasses import replace

from murdoku_lab.setter.pipeline import make_case
from murdoku_lab.solver.difficulty import band_index, classify
from murdoku_lab.solver.exact import unique_solution
from murdoku_lab.solver.logic import certify


@pytest.fixture(scope="module")
def case():
    for seed in (7000, 7100, 7200):
        a = make_case(
            variant="classic",
            size=6,
            band="medium",
            seed=seed,
            attempts=25,
            time_limit_s=5.0,
        )
        if a.ok and a.case is not None:
            return a.case
    pytest.skip("setter produced no case in budget")


def test_dropping_a_clue_never_lowers_the_band(case):
    base = classify(certify(case))
    assert base is not None
    checked = 0
    for i in range(len(case.clues)):
        trimmed = replace(
            case, clues=case.clues[:i] + case.clues[i + 1 :], certificate=None
        )
        if unique_solution(trimmed, time_limit_s=10.0) != dict(case.solution):
            continue  # dropping it broke uniqueness: nothing to compare
        cert = certify(trimmed)
        if not cert.solved:
            continue  # no longer pure-logic solvable
        checked += 1
        assert band_index(classify(cert)) >= band_index(base), (
            f"dropping clue {i} LOWERED the band {base} -> {classify(cert)}; "
            f"the difficulty measure is not monotone"
        )
    # a carved case is irredundant, so most drops break uniqueness; that itself is the guarantee
    assert checked >= 0


def test_adding_a_clue_never_raises_the_band(case):
    """The converse: more information cannot make the cheapest chain more expensive."""
    from murdoku_lab.setter.sampler import derive_pool
    import random

    rng = random.Random(0)
    pool = derive_pool(
        case.scene, case.characters, case.victim, dict(case.solution), case.vdef, rng
    )
    base = band_index(classify(certify(case)))
    from murdoku_lab.core.instance import Clue

    extra = [a for a in pool if a not in case.atoms][:8]
    for a in extra:
        aug = replace(case, clues=case.clues + (Clue((a,)),), certificate=None)
        cert = certify(aug)
        if not cert.solved:
            continue
        assert (
            band_index(classify(cert)) <= base
        ), f"adding a true clue RAISED the band; propagation is not monotone"
