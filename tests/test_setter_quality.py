"""Small, offline checks for spatial generation and non-spoiling presentation."""

from collections import Counter
from dataclasses import replace
import json
import random
from types import SimpleNamespace

import pytest
from murdoku_lab.core.atoms import Atom
from murdoku_lab.core.board import Scene
from murdoku_lab.core.instance import Case, Clue, VARIANTS
from murdoku_lab.core.theme import canonical_theme
from murdoku_lab.core.render import render_atom, render_clue, render_case
from murdoku_lab.setter.llm_setter import _shape
from murdoku_lab.setter.quality import gives_verdict, direct_verdict_clues
from murdoku_lab.setter.sampler import gen_scene
from murdoku_lab.setter.scene_layout import enrich_scene


def kwargs(variant, size):
    v = VARIANTS[variant]
    kw = dict(objects=v.objects, prop_mix=v.prop_mix)
    if size >= 10:
        kw.update(
            terrain=("fairway", "rough", "sand", "water"),
            terrain_rate=0.4,
            blob_scale=size // 4,
        )
    return kw


@pytest.mark.parametrize("variant,n", [("classic", 6), ("anon", 8), ("course", 16)])
def test_scenes_are_reproducible_and_keep_formal_invariants(variant, n):
    for seed in range(10):
        args = (n, max(4, n // 2) if n >= 10 else n)
        original = gen_scene(*args, random.Random(seed), **kwargs(variant, n))
        scene = enrich_scene(
            original, random.Random(seed + 123), anonymous=variant == "anon"
        )
        assert {
            p.pid: (p.standable, p.landmark, len(p.cells)) for p in scene.props
        } == {p.pid: (p.standable, p.landmark, len(p.cells)) for p in original.props}
        assert scene.terrain_of == original.terrain_of
        assert all(
            scene._connected(scene.cells_of_area(a)) for a in range(scene.n_areas)
        )
        assert all(scene.standable(k) for d in scene.doors for k in d)
        pairs = [tuple(sorted(scene.area_of[k] for k in d)) for d in scene.doors]
        assert len(pairs) == len(set(pairs))
        one = gen_scene(*args, random.Random(seed), **kwargs(variant, n))
        two = gen_scene(*args, random.Random(seed), **kwargs(variant, n))
        assert one.to_json() == two.to_json()


def test_explicit_no_doors():
    assert not gen_scene(
        6, 4, random.Random(0), door_rate=0, objects=VARIANTS["classic"].objects
    ).doors


def tiny_case():
    s = Scene(6, 6, tuple(c // 2 for r in range(6) for c in range(6)), (None,) * 36)
    people = tuple("ABCDE") + ("V",)
    return Case(
        s,
        people,
        "V",
        (Clue((Atom("with", "A", ("B",)),)),),
        {p: i * 7 for i, p in enumerate(people)},
    )


def test_direct_identity_hints_are_distinct_from_rules_or_open_tasks():
    assert gives_verdict(Atom("with", "A", ("V",)), "V")
    assert gives_verdict(Atom("alone_with", "V", ("A",)), "V")
    assert gives_verdict(Atom("area_no_offset", "A", ("V", 0)), "V")
    assert not gives_verdict(Atom("area_no_offset", "A", ("V", 1)), "V")
    assert not gives_verdict(Atom("with", "A", ("B",)), "V")
    assert not gives_verdict(Atom("with", "A", ("V",)), "V", "open")


def test_late_victim_relabel_cannot_create_a_direct_verdict_hint(monkeypatch):
    import murdoku_lab.setter.constraint_first as cf

    case = tiny_case()
    assert not direct_verdict_clues(case)
    assert direct_verdict_clues(cf._swap_symbols(case, "V", "A"))
    cert = SimpleNamespace(place_order=["C", "D", "E", "V", "A", "B"])

    def forbidden(*a, **kw):
        raise AssertionError("Obvious spoiler should be filtered before an exact solve")

    monkeypatch.setattr(cf, "unique_solution", forbidden)
    assert (
        cf._relabel_for_late_victim(
            case, cert, time_limit_s=1, avoid_verdict_hints=True
        )
        is None
    )


def test_llm_shape_supplies_only_public_geometry():
    n = 8
    scene = gen_scene(n, 4, random.Random(3), **kwargs("anon", n))
    # Deliberately no solution, clue, seed or certificate attributes to inspect.
    case = SimpleNamespace(
        scene=scene, characters=tuple("ABCDEFG") + ("V",), victim="V"
    )
    shape = _shape(case)
    assert "Area 1:" in shape["layout"] and "neighbouring areas" in shape["layout"]
    assert not set(shape) & {"solution", "clues", "answer_key", "seed", "certificate"}
    assert all(p.pid in shape["layout"] for p in scene.props)
    assert all(
        noun not in shape["props"] for noun in ("piano", "chair", "shelf", "carpet")
    )


def test_short_wording_preserves_axis_and_explicit_existential_subjects():
    case = tiny_case()
    theme = canonical_theme(case)
    row = render_atom(Atom("row_offset", "A", ("B", 2)), case, theme)
    col = render_atom(Atom("col_offset", "A", ("B", -2)), case, theme)
    assert "A's row" in row and "B's row" in row and "below" in row
    assert "A's column" in col and "B's column" in col and "left" in col
    assert "column" not in row and "row" not in col
    clue = Clue((Atom("other_beside", "V", ("table",)), Atom("in_corner", "V")))
    text = render_clue(clue, case, theme)
    assert "Someone else" in text and "V was in a corner" in text
    whole = render_case(case, theme)
    assert whole.count("TERMS\n") == 1 and "zero is even" in whole
    assert "terrain square" in render_atom(
        Atom("beside_terrain", "A", ("water",)), case, theme
    )


def test_text_and_theme_context_include_public_attributes():
    case = replace(
        tiny_case(), tags={"A": frozenset({"woman"}), "V": frozenset({"man"})}
    )
    text = render_case(case)
    assert "ATTRIBUTES\n" in text and "A: woman" in text and "V: man" in text
    assert "solution" not in _shape(case)
    tags = json.loads(_shape(case)["public_tags"])
    assert tags["A"] == ["woman"] and tags["V"] == ["man"]


def test_neutral_victim_note_and_object_terrain_wording():
    from murdoku_lab.setter.llm_setter import _coerce

    case = tiny_case()
    theme = canonical_theme(case)
    data = theme.to_json()
    data["victim_note"] = "was found alone"
    with pytest.raises(ValueError, match="neutral"):
        _coerce(data, case)
    assert "a sand patch" in render_atom(Atom("on", "A", ("sand",)), case, theme)
    assert "water feature" in render_atom(Atom("beside", "A", ("water",)), case, theme)
    assert "water terrain square" in render_atom(
        Atom("beside_terrain", "A", ("water",)), case, theme
    )
    assert "a flowers" not in render_atom(
        Atom("other_beside", "A", ("flowers",)), case, theme
    )


def test_placement_setter_still_passes_original_gate():
    from murdoku_lab.setter.pipeline import make_case, gate
    from murdoku_lab.solver.exact import enumerate_dfs

    result = make_case(
        variant="classic", size=6, band="easy", seed=8000, attempts=30, time_limit_s=4
    )
    assert result.ok and result.case is not None
    assert result.case.meta["quality_version"] == "scene-design-v1"
    assert not direct_verdict_clues(result.case)
    report = gate(result.case, expect_band="easy", exact_count=False, time_limit_s=5)
    assert report.ok, report.failed
    check = enumerate_dfs(result.case, cap=2)
    assert check.unique and check.solutions[0] == dict(result.case.solution)


def test_constraint_first_rejects_a_disagreeing_final_certificate(monkeypatch):
    import murdoku_lab.setter.constraint_first as cf

    original = cf._prune_useless

    def disagree(case, cert, **kwargs):
        case, cert = original(case, cert, **kwargs)
        return case, replace(cert, placed={})

    monkeypatch.setattr(cf, "_prune_useless", disagree)
    result = cf.generate(
        variant="classic",
        size=6,
        band=None,
        seed=3,
        workers=1,
        beam=24,
        max_clues=30,
        cap=50,
        attempts=1,
        time_limit_s=5,
    )
    assert result.reason == "logic_solution_mismatch"
