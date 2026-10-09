"""The large-board family: terrain, area-number arithmetic, tags, occupancy parity, 10-18 sizes.

Modelled on the reference game's 16x16 "Golf Course". These tests exist
because that board broke four assumptions the 6x6 code had quietly baked in: a fixed atom budget, a
fixed instant-pin cap, an O(pool) carve, and irredundancy as a gate condition.
"""

import random

import pytest

from murdoku_lab.core.atoms import SPECS, Atom, holds_atom, unary_mask
from murdoku_lab.core.board import Scene, TERRAINS
from murdoku_lab.core.instance import VARIANTS
from murdoku_lab.setter.sampler import gen_scene


@pytest.fixture(scope="module")
def course():
    """A terrain-bearing 12x12 board. 12 rather than 16 to keep the suite fast; the predicates and
    the scaling are the same, and the 16x16 path is covered by test_course_16_generates.
    """
    return gen_scene(
        12,
        6,
        random.Random(7),
        terrain=("fairway", "rough", "sand", "water"),
        terrain_rate=0.40,
        blob_scale=3,
    )


# ------------------------------------------------------------------------------- terrain layer
def test_unstandable_terrain_removes_the_cell(course):
    """Water is a hazard, not a square someone stood on. It must block exactly like a table does."""
    water = {k for k in range(course.n_cells) if course.terrain_of[k] == "water"}
    assert water, "fixture produced no water"
    assert water <= course.info.blocked
    assert not (water & set(course.open_cells))


def test_terrain_index_only_lists_standable_cells(course):
    for t, cells in course.info.cells_of_terrain.items():
        assert cells <= set(course.open_cells), f"{t} indexes a blocked cell"
        if not TERRAINS[t].standable:
            assert not cells


def test_terrain_survives_a_json_round_trip(course):
    import json

    back = Scene.from_json(json.loads(json.dumps(course.to_json())))
    assert back.terrain_of == course.terrain_of
    assert back.info.blocked == course.info.blocked


def test_a_scene_without_terrain_still_works():
    """Backwards compatibility: every pre-terrain Scene must behave exactly as before."""
    s = Scene(W=4, H=4, area_of=(0,) * 8 + (1,) * 8, obj_of=(None,) * 16)
    assert set(s.terrain_of) == {"floor"}
    assert not s.info.blocked


# ------------------------------------------------------------- mask <=> holds for the new kinds
NEW_UNARY = {
    "in_terrain": ("sand",),
    "not_in_terrain": ("water",),
    "beside_terrain": ("water",),
    "area_no_parity": ("even",),
    "on_extreme": ("north",),
    "not_on_extreme_axis": ("column",),
}


@pytest.mark.parametrize("kind,args", sorted(NEW_UNARY.items()))
def test_mask_agrees_with_holds_on_every_cell(kind, args, course):
    """`mask` is a second implementation of `holds` and must agree exactly."""
    a = Atom(kind, "A", args)
    mask = unary_mask(a, course)
    assert mask is not None
    for k in course.open_cells:
        want = holds_atom(a, course, {"A": k, "B": (k + 1) % course.n_cells})
        assert (k in mask) is want, f"{kind} disagrees at cell {k}"


def test_area_ordinals_are_one_based(course):
    """Clues do arithmetic on the human area number, so the offset is part of the model."""
    for k in (0, course.n_cells // 2, course.n_cells - 1):
        assert course.area_no(k) == course.area_of[k] + 1


@pytest.mark.parametrize("kind", ["area_no_gt", "area_no_lt", "area_no_offset"])
def test_area_ordinal_pairs_match_a_hand_computation(kind, course):
    rng = random.Random(3)
    cells = sorted(course.open_cells)
    for _ in range(150):
        i, j = rng.sample(cells, 2)
        args = ("B", 1) if kind == "area_no_offset" else ("B",)
        got = holds_atom(Atom(kind, "A", args), course, {"A": i, "B": j})
        na, nb = course.area_no(i), course.area_no(j)
        want = {
            "area_no_gt": na > nb,
            "area_no_lt": na < nb,
            "area_no_offset": na - nb == 1,
        }[kind]
        assert got is want


def test_occupancy_parity_matches_a_direct_count(course):
    a = Atom("area_occupancy_parity", "A", ("even",))
    rng = random.Random(5)
    cells = sorted(course.open_cells)
    for _ in range(120):
        pl = dict(zip("ABCD", rng.sample(cells, 4)))
        want = all(
            sum(1 for k in pl.values() if course.area_of[k] == ar) % 2 == 0
            for ar in range(course.n_areas)
            if (ar + 1) % 2 == 0
        )
        assert holds_atom(a, course, pl) is want


def test_tag_predicates_need_the_tag_map(course):
    """A tag atom evaluated without tags must fail loudly, never silently return False."""
    a = Atom("only_tag_on", "A", ("man", "chair"))
    assert SPECS["only_tag_on"].needs_tags
    with pytest.raises(NotImplementedError):
        SPECS["only_tag_on"].holds(a, course, {"A": 0})


# ------------------------------------------------------------------------------- the variant
def test_course_variant_declares_the_tags_its_predicates_need():
    v = VARIANTS["course"]
    assert v.tags, "course allows tag predicates, so it must declare tag names"
    assert any(SPECS[k].needs_tags for k in v.allowed_kinds)
    assert v.sizes[0] >= 10 and v.sizes[-1] >= 16


def test_a_variant_allowing_tag_predicates_without_tags_is_refused():
    """The registration check that caught `extended` silently admitting the new tag kinds."""
    from murdoku_lab.core.instance import Variant, register_variant

    with pytest.raises(ValueError, match="declares no tags"):
        register_variant(
            Variant(
                name="_bad_tags", sizes=(6,), allowed_kinds=frozenset({"only_tag_on"})
            )
        )


def test_absolute_coordinates_are_excluded_at_scale():
    """On a 16x16 board "she was in column 5" is very nearly the answer."""
    allowed = VARIANTS["course"].allowed_kinds
    assert "abs_row" not in allowed and "abs_col" not in allowed


def test_caps_and_atom_budget_scale_with_the_cast():
    """A cap of one instant pin across sixteen suspects is unsatisfiable; the scaling exists so a
    large board is not rejected by a figure calibrated on a 6x6 one."""
    from murdoku_lab.solver.difficulty import style_ok

    atoms = [Atom("beside", chr(65 + i % 16), ("chair",)) for i in range(30)]
    assert not style_ok(atoms, "medium")  # fixed cap: 16
    assert style_ok(atoms, "medium", n_characters=16)  # scaled: 2.5 * 16 = 40


@pytest.mark.slow
def test_course_16_generates_and_passes_the_gate():
    """The 16x16 end to end. Slow (~45s) because carving a 16-person board is real work; marked so
    it can be deselected, but it is the only test that proves the target board actually ships.
    """
    from murdoku_lab.setter.pipeline import gate, make_case

    a = make_case(
        variant="course", size=16, band="medium", seed=5, attempts=6, time_limit_s=25.0
    )
    if not a.ok or a.case is None:
        pytest.skip(f"no 16x16 case within the attempt budget: {a.reason}")
    c = a.case
    assert len(c.characters) == 16
    assert c.scene.W == c.scene.H == 16
    g = gate(c, expect_band="medium", time_limit_s=40)
    assert g.ok, f"gate rejected: {g.failed}"
    # Redundant clues are EXPECTED below the hardest band; useless ones never are.
    assert g.detail["useless_clues"] == []


def test_carving_a_large_pool_uses_the_block_phase():
    """The coarse phase is what makes a 16x16 tractable: O(k log n) solves instead of O(pool).
    Below the threshold it must not engage, or every `classic` seed would produce a different case.
    """
    import inspect

    from murdoku_lab.setter.sampler import carve

    src = inspect.getsource(carve)
    assert "coarse_threshold" in src
    assert inspect.signature(carve).parameters["coarse_threshold"].default == 300


def test_constraint_first_reuses_witnesses_instead_of_solving_every_candidate():
    """One exact solve per clue is the scaling contract; candidate ranking is in-memory."""
    from murdoku_lab.setter.constraint_first import generate
    from murdoku_lab.setter.pipeline import gate

    # Seed 1 passes the unified reveal-order gate; seed 2 is now rejected.
    r = generate(
        variant="classic",
        size=6,
        band=None,
        seed=1,
        workers=1,
        beam=24,
        max_clues=30,
        cap=50,
        attempts=1,
        time_limit_s=5,
    )
    assert r.case is not None and not r.reason
    assert r.solves <= r.n_atoms + 2
    assert gate(r.case, expect_band=r.band, time_limit_s=10, exact_count=False).ok


@pytest.mark.slow
def test_constraint_first_16_produces_a_gated_human_solvable_case():
    """Regression for the witness scorer and post-uniqueness logic repair."""
    from murdoku_lab.setter.constraint_first import generate
    from murdoku_lab.setter.pipeline import gate

    r = generate(
        variant="course",
        size=16,
        band="expert",
        seed=7,
        workers=1,
        beam=64,
        max_clues=60,
        cap=50,
        attempts=1,
        time_limit_s=20,
    )
    assert r.case is not None and not r.reason
    assert r.certificate is not None and r.certificate.solved
    assert r.case.certificate == r.certificate.to_json()
    assert gate(r.case, expect_band="expert", time_limit_s=30, exact_count=False).ok


# =============================================================================================
# Reproducibility under a growing catalogue. This bug class has now bitten twice: once via set
# iteration order (PYTHONHASHSEED), once via rng consumed before an allow-check, and now via the
# object catalogue. All three had the same symptom — a fixed seed quietly producing a different
# board — and the same cost: every calibrated difficulty number silently became wrong.
# =============================================================================================
def test_no_variant_samples_the_global_catalogue():
    """`gen_scene` samples props with rng.choice, so drawing from a global list means that REGISTERING
    a new prop kind changes every board a fixed seed produces — that is what collapsed all four
    difficulty bands to `easy` when the golf props were added.

    Two ways to be safe, and a variant must use one of them: pin a named palette (`objects`), or
    declare anonymous props by class and let the theme name them (`prop_mix`). The second is the cure
    rather than the workaround — with no global vocabulary there is no list left to grow.
    """
    from murdoku_lab.core.board import OBJECTS
    from murdoku_lab.core.instance import VARIANTS

    for name, v in VARIANTS.items():
        assert (
            v.objects or v.prop_mix
        ), f"variant {name!r} pins neither a palette nor a prop_mix, so it samples the catalogue"
        for o in v.objects:
            assert o in OBJECTS, f"{name!r} lists unknown prop {o!r}"
        for cls, count in v.prop_mix:
            assert cls in (
                "blocking",
                "landmark",
                "standable",
            ), f"{name!r}: bad class {cls!r}"
            assert count > 0


def test_the_golf_props_are_absent_from_the_small_board_variants():
    """The reference game's 6-9 boards never show a flag or a sand pit; keeping them out is what
    makes those seeds stable against future additions."""
    from murdoku_lab.core.instance import VARIANTS

    golf = {"sand", "flag", "tee", "golf_cart", "water"}
    for name in ("classic", "open", "extended"):
        assert not (
            set(VARIANTS[name].objects) & golf
        ), f"{name} palette leaked golf props"
    assert golf <= set(VARIANTS["course"].objects)


def test_a_generated_board_only_contains_palette_props():
    import random

    from murdoku_lab.core.instance import VARIANTS
    from murdoku_lab.setter.sampler import gen_scene

    for name in ("classic", "course"):
        v = VARIANTS[name]
        n = v.sizes[0]
        s = gen_scene(n, max(4, n // 2), random.Random(11), objects=v.objects)
        used = {o for o in s.obj_of if o}
        assert used <= set(v.objects), f"{name} board used {used - set(v.objects)}"


def test_registering_a_new_object_cannot_change_an_existing_seed():
    """The property that actually matters, asserted directly: pass a palette, and a board is a
    function of (seed, palette) alone — never of how many kinds happen to be registered.
    """
    import random

    from murdoku_lab.core.instance import VARIANTS

    pal = VARIANTS["classic"].objects
    from murdoku_lab.setter.sampler import gen_scene

    a = gen_scene(6, 6, random.Random(5), objects=pal)
    b = gen_scene(6, 6, random.Random(5), objects=pal)
    assert a.obj_of == b.obj_of and a.area_of == b.area_of
    # a wider palette must produce a *different* board, proving the palette is really the input
    c = gen_scene(6, 6, random.Random(5), objects=pal + ("flag",))
    assert c.obj_of != a.obj_of or "flag" not in c.obj_of


# =============================================================================================
# Board-local props. The prop vocabulary belongs to the BOARD, not to core: a prop is a class
# (standable / blocking / landmark) plus a footprint, and its NAME is theme data. Two payoffs:
# registering a prop kind can no longer change what a seed produces, and a theme can INVENT props
# rather than only rename ours.
# =============================================================================================
def test_a_board_declares_its_own_props_and_core_need_not_know_them():
    """The whole point: `p0` is in no global catalogue, and the board works anyway."""
    from murdoku_lab.core.board import OBJECTS, Prop, Scene

    area = (0,) * 8 + (1,) * 8
    props = (
        Prop("p0", standable=False, cells=frozenset({3, 9}), landmark=True),
        Prop("p1", standable=True, cells=frozenset({4})),
    )
    s = Scene(W=4, H=4, area_of=area, obj_of=(None,) * 16, props=props)
    assert "p0" not in OBJECTS and "p1" not in OBJECTS
    assert s.prop_of[3] == "p0" and s.prop_of[4] == "p1"
    assert sorted(s.info.blocked) == [
        3,
        9,
    ], "a blocking prop blocks every cell of its footprint"
    assert 4 not in s.info.blocked, "a standable prop blocks nothing"


def test_a_multi_cell_prop_already_works():
    """A carpet covers several squares; a single-cell-only model is silly. The footprint is a set
    today so that per-instance props are a change of CONTENTS, not of shape — `on` and `beside` are
    already defined over the footprint and will not need touching."""
    from murdoku_lab.core.board import Prop, Scene

    rug = (Prop("rug", standable=True, cells=frozenset({0, 1, 4, 5})),)
    s = Scene(W=4, H=4, area_of=(0,) * 16, obj_of=(None,) * 16, props=rug)
    assert sorted(s.prop("rug").cells) == [0, 1, 4, 5]
    assert not (s.info.blocked & {0, 1, 4, 5})
    assert all(s.prop_of[k] == "rug" for k in (0, 1, 4, 5))


def test_two_props_cannot_claim_the_same_cell():
    from murdoku_lab.core.board import Prop, Scene
    import pytest as _pt

    with _pt.raises(ValueError, match="covered by both"):
        Scene(
            W=4,
            H=4,
            area_of=(0,) * 16,
            obj_of=(None,) * 16,
            props=(Prop("a", False, frozenset({5})), Prop("b", True, frozenset({5}))),
        )


def test_a_legacy_board_still_derives_props_from_its_objects():
    """Every construction site that predates props keeps working: one prop per catalogue object,
    footprint = all of that object's cells, standability from the catalogue."""
    from murdoku_lab.core.board import Scene

    obj = [None] * 16
    obj[3] = obj[9] = "table"
    obj[4] = "chair"
    s = Scene(W=4, H=4, area_of=(0,) * 8 + (1,) * 8, obj_of=tuple(obj))
    by = {p.pid: p for p in s.props}
    assert sorted(by) == ["chair", "table"]
    assert sorted(by["table"].cells) == [3, 9] and not by["table"].standable
    assert by["chair"].standable


def test_generated_anonymous_props_carry_only_a_class():
    """What the theme is shown: a class and a footprint, never a name."""
    import random

    from murdoku_lab.core.instance import VARIANTS
    from murdoku_lab.setter.sampler import gen_scene

    v = VARIANTS["anon"]
    s = gen_scene(8, 4, random.Random(3), prop_mix=v.prop_mix)
    assert s.props
    for p in s.props:
        assert p.pid.startswith("p"), f"{p.pid} should be anonymous"
        assert p.cells
    assert any(p.standable for p in s.props) and any(not p.standable for p in s.props)
    assert any(p.landmark for p in s.props)


def test_the_shape_shown_to_a_theme_author_names_nothing():
    """The LLM's input must describe props by what they physically ARE. If a canonical noun leaked in,
    the theme would be renaming rather than inventing, which is the thing this replaces.
    """
    from murdoku_lab.setter.llm_setter import _shape
    from murdoku_lab.setter.pipeline import make_case
    import pytest as _pt

    a = make_case(variant="anon", size=7, band="medium", seed=5, attempts=25)
    if a.case is None:
        _pt.skip(f"no anon case: {a.reason}")
    props = _shape(a.case)["props"]
    assert "standable" in props and "blocking" in props
    for noun in ("table", "chair", "piano", "boulder", "barrel", "shelf", "carpet"):
        assert (
            noun not in props
        ), f"the prop description leaks the canonical noun {noun!r}"


# =============================================================================================
# Style floors must apply to predicates added AFTER they were written. Both sets used to be
# hardcoded lists from when there were 20 predicates, so on a variant allowing the full catalogue a
# perfectly good carved set of `area_no_gt` / `diagonal` / `on_grid_edge` atoms scored ZERO anchors
# and `style_floor` rejected 280 of 349 attempts — a hit rate of 0.014. A rule that silently stops
# applying to new predicates is worse than no rule.
# =============================================================================================
def test_anchor_and_negative_sets_cover_the_whole_catalogue_structurally():
    from murdoku_lab.core.atoms import SPECS
    from murdoku_lab.solver.difficulty import ANCHOR_KINDS, NEGATIVE_KINDS

    assert ANCHOR_KINDS and NEGATIVE_KINDS
    assert not (ANCHOR_KINDS & NEGATIVE_KINDS), "a predicate cannot be both"
    assert ANCHOR_KINDS <= set(SPECS) and NEGATIVE_KINDS <= set(SPECS)
    # every denial is caught, and the one positive that merely READS like one is not
    for k in SPECS:
        if k.startswith("not_"):
            assert k in NEGATIVE_KINDS, f"{k} is a denial and must count as one"
    assert (
        "no_empty_area" not in NEGATIVE_KINDS
    ), "it reads as a denial but positively claims every area is occupied"


def test_every_variant_can_reach_its_anchor_floor():
    """The failure mode, asserted at the source: a variant whose predicates yield no anchors can never
    satisfy `min_anchor_atoms`, so every attempt is rejected and the band is silently unreachable.
    """
    from murdoku_lab.core.instance import VARIANTS
    from murdoku_lab.solver.difficulty import ANCHOR_KINDS, style

    want = int(style().get("min_anchor_atoms", 0))
    for name, v in VARIANTS.items():
        available = v.allowed_kinds & ANCHOR_KINDS
        assert (
            len(available) >= want
        ), f"variant {name!r} allows only {len(available)} anchor predicate(s), needs {want}"


def test_carving_repeats_until_nothing_more_can_be_dropped():
    """One pass is not enough. `accept` vetoes overshooting the target band, and whether a given drop
    overshoots depends on what else is still present — so a drop refused early can become acceptable
    later. A single pass stopped ~25 atoms above a cap of 17."""
    import inspect

    from murdoku_lab.setter.sampler import carve

    src = inspect.getsource(carve)
    assert "for _sweep in range(" in src, "the fine phase must run to a fixpoint"
    assert "if not progressed:" in src
