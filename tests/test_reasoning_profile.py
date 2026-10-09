"""Observer equivalence, trace soundness, and controlled scheduling variations."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from murdoku_lab.core.instance import Case
from murdoku_lab.solver.exact import CountResult
from murdoku_lab.solver.logic import certify
from murdoku_lab.solver.reasoning_profile import (
    ProfileDeducer,
    opening_unary_witnesses,
    clue_ablation,
    profile_case,
    verdict_support,
)


@pytest.fixture
def case():
    return Case.from_json(
        json.loads(
            (Path(__file__).parent / "fixtures/quality_base_case.json").read_text()
        )
    )


@pytest.mark.parametrize("include_probe", [False, True])
def test_observer_preserves_production_certificate(case, include_probe):
    engine = ProfileDeducer(case)
    observed = engine.run(include_probe=include_probe)
    assert observed.to_json() == certify(case, include_probe=include_probe).to_json()
    assert len(engine.snapshots) == len(observed.steps)
    profile = profile_case(case, include_probe=include_probe)
    assert profile["retains_solution_at_every_step"]
    assert profile["trace"][-1]["uncertainty"] == 0
    assert all(
        a["candidate_count"] >= b["candidate_count"]
        for a, b in zip(profile["trace"], profile["trace"][1:])
    )


@pytest.mark.parametrize("order", ["clues", "characters", "techniques"])
def test_order_variants_are_reproducible_and_do_not_use_answer(case, order):
    before = case.to_json()
    first = profile_case(case, order=order, seed=23)
    second = profile_case(case, order=order, seed=23)
    assert first == second
    assert first["solved"] and first["matches_solution"]
    assert first["retains_solution_at_every_step"]
    assert case.to_json() == before
    without_key = profile_case(replace(case, solution={}), order=order, seed=23)
    assert first["trace"] == without_key["trace"]


def test_verdict_support_is_domain_based_and_keeps_true_murderer(case):
    full_domains = {x: case.scene.open_cells for x in case.characters}
    assert case.murderer in verdict_support(case, full_domains)
    fixed = {x: [cell] for x, cell in case.solution.items()}
    assert verdict_support(case, fixed) == [case.murderer]
    # Domains, not the hidden placement, control the inference.
    assert verdict_support(replace(case, solution={}), fixed) == [case.murderer]


def test_opening_witnesses_are_presented_clues_and_match_setup(case):
    witnesses = opening_unary_witnesses(case)
    setup, _ = ProfileDeducer(case).initial()
    assert {w["character"] for w in witnesses} == {
        x for x, c in setup.cand.items() if len(c) == 1
    }
    for witness in witnesses:
        if witness["witness_clue_ids"] is None:
            assert witness["exceeds_cap"]
            continue
        clues = tuple(case.clues[i - 1] for i in witness["witness_clue_ids"])
        reduced, _ = ProfileDeducer(replace(case, clues=clues)).initial()
        assert len(reduced.cand[witness["character"]]) == 1


def test_ablation_timeout_is_not_classified_as_unique(case, monkeypatch):
    monkeypatch.setattr(
        "murdoku_lab.solver.exact.enumerate_cp",
        lambda *args, **kwargs: CountResult(1, [dict(case.solution)], True),
    )
    # One observed solution is not proof of uniqueness when enumeration times out.
    short = replace(case, clues=case.clues[:1])
    result = clue_ablation(short)[0]
    assert result["exact_status"] == "timeout"
    assert result["exact_timed_out"]
