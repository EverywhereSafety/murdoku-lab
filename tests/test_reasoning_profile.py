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


def test_partial_discoveries_are_sound_without_changing_deductions(case):
    profile = profile_case(case)
    seen = {axis: set() for axis in ("row", "column", "area")}
    project = {
        "row": case.scene.row,
        "column": case.scene.col,
        "area": lambda k: case.scene.area_of[k],
    }
    for row in profile["trace"]:
        for axis, names in row["new_partial_locations"].items():
            for name in names:
                cells = row["candidates"][name]
                assert len(cells) > 1
                assert len({project[axis](k) for k in cells}) == 1
                assert name not in seen[axis]
                seen[axis].add(name)
    assert profile["first_progress_step"] <= profile["first_determination_step"]
    assert profile["progress_gap_max"] <= profile["determination_gap_max"]
    assert profile["steps"] == len(certify(case).steps) - 1


def test_rhythm_policy_rejects_early_reveal_and_checks_alternate_orders(case, tmp_path):
    from murdoku_lab.setter.quality import check_rhythm

    baseline = check_rhythm(case, {"schema": "murdoku.rhythm_policy/1"})
    assert baseline["ok"]
    assert {row["order"] for row in baseline["runs"]} == {
        "canonical",
        "characters",
        "clues",
    }
    strict = check_rhythm(
        case,
        {
            "schema": "murdoku.rhythm_policy/1",
            "min_verdict_determined_fraction": 1,
        },
    )
    assert not strict["ok"]
    assert any(
        not row["checks"]["min_verdict_determined_fraction"] for row in strict["runs"]
    )
    from murdoku_lab.setter.export_queries import write_bundle

    manifest = write_bundle(
        [case.to_json()],
        tmp_path / "rejected",
        views=("text",),
        rhythm_policy={
            "schema": "murdoku.rhythm_policy/1",
            "min_verdict_determined_fraction": 1,
        },
    )
    assert manifest["accepted_cases"] == 0
    assert manifest["admission"][0]["gate_checks"]["rhythm_policy"] is False


@pytest.mark.parametrize(
    "fields",
    [
        {"max_probe_fraction": 2},
        {"seeds": []},
        {"max_progress_gap": float("nan")},
        {"unknown": 1},
    ],
)
def test_invalid_rhythm_policy_fails_early(fields):
    from murdoku_lab.setter.quality import normalize_rhythm_policy

    with pytest.raises(ValueError):
        normalize_rhythm_policy({"schema": "murdoku.rhythm_policy/1", **fields})


def test_clue_vocabulary_policy_is_checked_independently(case):
    from murdoku_lab.setter.quality import check_rhythm, normalize_rhythm_policy

    kind = case.atoms[0].kind
    report = check_rhythm(
        case,
        {
            "schema": "murdoku.rhythm_policy/1",
            "orders": ["canonical"],
            "excluded_kinds": [kind],
        },
    )
    assert not report["ok"]
    assert report["runs"][0]["checks"]["clue_vocabulary"] is False
    with pytest.raises(ValueError):
        normalize_rhythm_policy(
            {"schema": "murdoku.rhythm_policy/1", "excluded_kinds": ["invented"]}
        )


@pytest.mark.parametrize(
    "kind,args",
    [
        ("row_offset", ("B", -2)),
        ("col_offset", ("B", 1)),
        ("with", ("B",)),
        ("alone_with", ("B",)),
        ("not_with", ("B",)),
        ("diagonal", ("B",)),
        ("adjacent_to", ("B",)),
    ],
)
def test_projected_pair_support_matches_cellwise_relation(case, kind, args):
    import random
    from murdoku_lab.core.atoms import Atom
    from murdoku_lab.solver.logic import Deducer

    engine = Deducer(case)
    atom = Atom(kind, "A", args)
    relation = engine._relation(atom)
    rng = random.Random(71)
    cells = sorted(case.scene.open_cells)
    for _ in range(20):
        left = set(rng.sample(cells, rng.randrange(len(cells) + 1)))
        right = set(rng.sample(cells, rng.randrange(len(cells) + 1)))
        expected = (
            {k for k in left if any(relation(k, m) for m in right)},
            {m for m in right if any(relation(k, m) for k in left)},
        )
        assert engine._pair_supports(atom, left, right) == expected


@pytest.mark.parametrize("value", [1])
@pytest.mark.parametrize("key", ["balance_clues", "simplify_area_options"])
def test_quality_options_require_booleans(value, key):
    from murdoku_lab.setter.quality import normalize_rhythm_policy

    with pytest.raises(ValueError, match=key):
        normalize_rhythm_policy({"schema": "murdoku.rhythm_policy/1", key: value})
