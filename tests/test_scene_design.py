"""Subject coverage, scene-contract preservation, and sound clue simplification."""

from dataclasses import replace
import json
from pathlib import Path
import random

import pytest

from murdoku_lab.core.atoms import Atom, holds_atom, unary_mask
from murdoku_lab.core.board import Scene
from murdoku_lab.core.instance import Case, Clue, VARIANTS
from murdoku_lab.setter.constraint_first import candidate_atoms, _interleave_candidates
from murdoku_lab.setter.quality import implied_atom_refs, prune_implied_atoms
from murdoku_lab.setter.sampler import gen_scene
from murdoku_lab.setter.scene_spec import (
    SceneSpecInfeasible,
    apply_spec,
    choose_area_count,
    normalize_spec,
    spec_satisfied,
)
from murdoku_lab.solver.exact import enumerate_dfs, unique_solution
from murdoku_lab.solver.logic import certify


def test_global_subjects_cover_permuted_cast_without_repeating_subject_free_facts():
    scene = gen_scene(6, 3, random.Random(61), objects=VARIANTS["classic"].objects)
    cast = tuple("ABCDE") + ("V",)
    for people in (cast, cast[::-1]):
        candidates = candidate_atoms(
            scene, people, VARIANTS["classic"], {}, random.Random(2)
        )
        for kind in ("only_on", "only_beside", "alone", "other_beside"):
            assert {a.holder for a in candidates if a.kind == kind} == set(cast)
        assert {a.holder for a in candidates if a.kind == "area_empty"} == {people[0]}


def test_candidate_masks_are_possible_and_local_clues_are_informative():
    scene = gen_scene(6, 4, random.Random(61), objects=VARIANTS["classic"].objects)
    candidates = candidate_atoms(
        scene, tuple("ABCDE") + ("V",), VARIANTS["classic"], {}, random.Random(2)
    )
    for atom in candidates:
        if atom.spec.mask is not None:
            mask = unary_mask(atom, scene)
            assert mask
            if atom.spec.arity == "unary":
                assert mask != scene.open_cells
        if atom.kind in {"on", "only_on"}:
            assert scene.prop_by_id[atom["obj"]].standable


def test_beam_exposure_does_not_follow_one_kinds_argument_multiplicity():
    many = [Atom("in_area", person, (area,)) for person in "ABCDE" for area in range(4)]
    few = [Atom("with", "A", ("B",)), Atom("alone", "C")]
    ordered = _interleave_candidates(many + few, random.Random(71))
    assert {a.kind for a in ordered[:3]} == {"in_area", "with", "alone"}
    assert set(ordered) == set(many + few)


def test_area_sampling_varies_and_respects_explicit_requests():
    assert {choose_area_count(6, random.Random(seed)) for seed in range(32)} == {
        3,
        4,
        5,
    }
    rng, control = random.Random(31), random.Random(31)
    assert choose_area_count(6, rng, n_areas=4) == 4
    assert rng.random() == control.random()


def anchor_scene():
    objects = [None] * 64
    objects[0], objects[4], objects[20] = "flag", "tee", "tree"
    terrain = ["floor"] * 64
    terrain[1] = "water"
    return Scene(
        8,
        8,
        tuple((r // 4) * 2 + c // 4 for r in range(8) for c in range(8)),
        tuple(objects),
        terrain_of=tuple(terrain),
    )


def test_scene_spec_preserves_blockers_terrain_and_non_target_props():
    scene = anchor_scene()
    original = scene.to_json()
    spec = normalize_spec(
        {
            "schema": "murdoku.scene_spec/1",
            "area_count": 4,
            "anchors_per_area": {"flag": 1, "tee": 1},
        },
        size=8,
    )
    changed = apply_spec(scene, spec, random.Random(19))
    assert scene.to_json() == original
    assert spec_satisfied(changed, spec)
    assert changed.area_of == scene.area_of and changed.terrain_of == scene.terrain_of
    assert changed.open_cells == scene.open_cells
    assert changed.prop_by_id["tree"] == scene.prop_by_id["tree"]
    assert all(len(changed.prop_by_id[p].cells) == 4 for p in ("flag", "tee"))
    assert changed.to_json() == apply_spec(scene, spec, random.Random(19)).to_json()


def test_infeasible_spec_never_discards_an_unrelated_prop_to_make_space():
    scene = Scene(
        4,
        4,
        tuple(c // 2 for r in range(4) for c in range(4)),
        (None,) + ("tree",) * 15,
    )
    spec = normalize_spec(
        {"schema": "murdoku.scene_spec/1", "anchors_per_area": {"flag": 1, "tee": 1}},
        size=4,
    )
    with pytest.raises(SceneSpecInfeasible):
        apply_spec(
            scene, spec, random.Random(1), allowed_objects=VARIANTS["course"].objects
        )
    assert len(scene.prop_by_id["tree"].cells) == 15


@pytest.mark.parametrize(
    "extra",
    [
        {"solution": {"A": 0}},
        {"area_count": True},
        {"area_count": 12},
        {"anchors_per_area": {"flag": 0}},
        {"anchors_per_area": {"flag": True}},
    ],
)
def test_scene_spec_rejects_unimplemented_fields_and_invalid_counts(extra):
    with pytest.raises(ValueError):
        normalize_spec({"schema": "murdoku.scene_spec/1", **extra}, size=6)


def test_spec_is_explicit_and_does_not_silently_change_prop_affordances():
    value = {
        "schema": "murdoku.scene_spec/1",
        "area_count": 4,
        "anchors_per_area": {"tree": 1},
    }
    with pytest.raises(ValueError, match="conflicts"):
        normalize_spec(value, size=8, n_areas=3)
    spec = normalize_spec(value, size=8)
    with pytest.raises(ValueError, match="standable"):
        apply_spec(anchor_scene(), spec, random.Random(0))


@pytest.fixture(scope="module")
def original_valid_case():
    source = Path(__file__).parent / "fixtures/quality_base_case.json"
    return replace(
        Case.from_json(json.loads(source.read_text())),
        variant="extended",
        certificate=None,
    )


def test_implied_subclause_removal_preserves_solution_band_and_reveal(
    original_valid_case,
):
    from murdoku_lab.solver.difficulty import classify

    case = original_valid_case
    index = next(
        i
        for i, clue in enumerate(case.clues)
        if any(a.kind == "in_corner" for a in clue.atoms)
    )
    clue = case.clues[index]
    weak = Atom("against_wall", clue.holder)
    case = replace(
        case,
        clues=case.clues[:index]
        + (Clue(clue.atoms + (weak,)),)
        + case.clues[index + 1 :],
    )
    before = certify(case)
    assert implied_atom_refs(case)
    after_case, after, removed = prune_implied_atoms(case, before)
    assert removed == 1 and not implied_atom_refs(after_case)
    assert (
        unique_solution(case, time_limit_s=5)
        == unique_solution(after_case, time_limit_s=5)
        == dict(case.solution)
    )
    assert enumerate_dfs(after_case, cap=2).solutions == [dict(case.solution)]
    assert after.placed == before.placed and classify(after) == classify(before)
    assert case.victim in after.place_order[-case.vdef.victim_last_k :]


def test_implication_checks_keep_holder_and_object_identity(original_valid_case):
    case = replace(
        original_valid_case,
        clues=(
            Clue(
                (
                    Atom("beside", "A", ("tree",)),
                    Atom("beside_through_wall", "A", ("table",)),
                )
            ),
            Clue((Atom("beside_through_wall", "B", ("tree",)),)),
        ),
    )
    assert not implied_atom_refs(case)


def test_corner_wall_implications_hold_for_every_open_cell():
    for seed in range(6):
        scene = gen_scene(
            6, 4, random.Random(seed), objects=VARIANTS["classic"].objects
        )
        for cell in scene.open_cells:
            placement = {"A": cell}
            if holds_atom(Atom("in_corner", "A"), scene, placement):
                assert holds_atom(Atom("against_wall", "A"), scene, placement)
            if holds_atom(Atom("in_grid_corner", "A"), scene, placement):
                assert holds_atom(Atom("in_corner", "A"), scene, placement)
                assert holds_atom(Atom("on_grid_edge", "A"), scene, placement)
