"""The CP-SAT encoder and `atoms.holds` are independent implementations; they must agree.

This is the test that keeps `murdoku_lab/solver/exact.py`'s encoder honest against `murdoku_lab/core/atoms.py`, which is the
single source of truth for what a clue *means*. A disagreement is an encoder bug.
"""

import random

import pytest

from murdoku_lab.core.atoms import SPECS, holds_atom
from murdoku_lab.setter.sampler import (
    CHAR_SYMBOLS,
    VICTIM_SYMBOL,
    build_case,
    derive_pool,
    gen_scene,
    sample_solution,
)
from murdoku_lab.core.instance import VARIANTS
from murdoku_lab.solver.exact import enumerate_cp, enumerate_dfs


def test_dfs_rechecks_alone_with_after_later_people_are_placed():
    from murdoku_lab.core.atoms import Atom
    from murdoku_lab.core.board import Scene
    from murdoku_lab.core.instance import Case, Clue

    chars = tuple("ABCDE") + ("V",)
    scene = Scene(6, 6, tuple(c // 3 for r in range(6) for c in range(6)), (None,) * 36)
    # Full columns force three occupants into each area, so no pair can be
    # alone together. Fixed rows keep this regression small and exhaustive.
    clues = tuple(
        Clue((Atom("abs_row", person, (row,)),)) for row, person in enumerate(chars)
    )
    case = Case(
        scene,
        chars,
        "V",
        clues + (Clue((Atom("alone_with", "A", ("B",)),)),),
        {},
        variant="open",
    )
    assert enumerate_cp(case, cap=None, time_limit_s=5).count == 0
    assert enumerate_dfs(case, cap=None).count == 0


def _random_case(seed, size=5, n_atoms=6):
    rng = random.Random(seed)
    scene = gen_scene(size, max(3, size - 1), rng)
    chars = list(CHAR_SYMBOLS[: size - 1]) + [VICTIM_SYMBOL]
    pl = sample_solution(scene, chars, rng)
    if pl is None:
        return None
    pool = derive_pool(scene, chars, VICTIM_SYMBOL, pl, VARIANTS["extended"], rng)
    if not pool:
        return None
    rng.shuffle(pool)
    return build_case(scene, chars, VICTIM_SYMBOL, pl, pool[:n_atoms], "extended")


@pytest.mark.parametrize("seed", range(25))
def test_cp_and_dfs_count_the_same(seed):
    case = _random_case(seed)
    if case is None:
        pytest.skip("no placement for this scene")
    a = enumerate_cp(case, cap=None, time_limit_s=30.0)
    b = enumerate_dfs(case)
    assert (
        not a.timed_out
    ), "CP enumeration timed out; raise the limit rather than trusting it"
    assert (
        a.count == b.count
    ), f"encoder disagrees with the reference DFS: CP={a.count} DFS={b.count}"
    assert {tuple(sorted(s.items())) for s in a.solutions} == {
        tuple(sorted(s.items())) for s in b.solutions
    }


@pytest.mark.parametrize("seed", range(12))
def test_recorded_solution_is_always_a_solution(seed):
    case = _random_case(seed)
    if case is None:
        pytest.skip("no placement")
    assert case.satisfies(case.solution)


@pytest.mark.parametrize("seed", range(10))
def test_unary_mask_agrees_with_holds(seed):
    """For a unary atom, mask membership must be exactly equivalent to `holds`."""
    case = _random_case(seed, n_atoms=30)
    if case is None:
        pytest.skip("no placement")
    from murdoku_lab.core.atoms import unary_mask

    scene = case.scene
    for a in case.atoms:
        if SPECS[a.kind].arity != "unary":
            continue
        m = unary_mask(a, scene)
        for k in scene.open_cells:
            pl = dict(case.solution)
            pl[a.holder] = k
            assert holds_atom(a, scene, pl) == (
                k in m
            ), f"{a.kind} mask/holds mismatch at cell {k}"


# =============================================================================================
# `other_beside` — the last predicate in the reference generator's own vocabulary that we lacked.
# Their filter is
#     !f.some(se => se !== X && areaOf[se] === areaOf[X] && beside[se].has(obj))
# i.e. SOMEONE ELSE in my area was beside the thing: an existential over the other characters, area
# scoped, untagged. Adding it took generator-vocabulary coverage from 24/25 to 25/25.
#
# It also exposed a scheduling bug in the DFS, which is why these tests exist rather than a smoke check.
# =============================================================================================
import random as _random

import pytest as _pytest

from murdoku_lab.core.atoms import SPECS as _SPECS, Atom as _Atom
from murdoku_lab.core.instance import (
    Case as _Case,
    Clue as _Clue,
    VARIANTS as _VARIANTS,
)
from murdoku_lab.setter.sampler import (
    CHAR_SYMBOLS as _CS,
    VICTIM_SYMBOL as _VS,
    derive_pool as _pool,
    gen_scene as _gen,
    sample_solution as _sample,
)
from murdoku_lab.solver.exact import enumerate_cp as _cp, enumerate_dfs as _dfs


def test_every_global_predicate_is_deferred_to_a_complete_placement():
    """The structural fix, asserted directly.

    The DFS used to decide WHEN to test an atom from the `exclusive` flag. `other_beside` is global but
    sets neither `exclusive` nor `needs_tags`, so it was tested as soon as the holder was placed — and
    a POSITIVE existential is false on every partial placement, so it pruned every branch: the DFS
    found 0 solutions where CP-SAT found 40. Scheduling now keys off ARITY, so a newly registered
    predicate cannot reintroduce this by forgetting a flag.
    """
    import inspect

    from murdoku_lab.solver import exact

    src = inspect.getsource(exact.enumerate_dfs)
    assert (
        'SPECS[a.kind].arity == "global"' in src
    ), "the DFS must defer global atoms by arity, not by a flag a new predicate could omit"
    assert "exclusive or SPECS" not in src


@_pytest.mark.parametrize("seed", [0, 3, 7, 13])
def test_other_beside_agrees_between_the_two_solvers(seed):
    """Solution-for-solution, not just counts. A cap would let two different sets of the same size
    look equal, which is how the first version of this check reported a false agreement — both engines
    hit 40 and the first-40 differed by enumeration order.

    Constrained hard enough that the count stays well under the cap: the first version paired CAP=4000
    with a 60s CP budget over ten seeds and turned a seven-minute suite into a fourteen-minute one.
    """
    CAP = 600
    rng = _random.Random(seed)
    sc = _gen(6, 4, rng, objects=_VARIANTS["classic"].objects)
    chars = list(_CS[:5]) + [_VS]
    pl = _sample(sc, chars, rng)
    if pl is None:
        _pytest.skip("no placement on this board")
    pool = _pool(sc, chars, _VS, pl, _VARIANTS["classic"], rng)
    keep = [a for a in pool if a.kind == "other_beside"][:1]
    if not keep:
        _pytest.skip("board yields no other_beside atom")
    keep += [
        a for a in pool if a.kind in ("in_area", "beside", "on", "abs_row", "abs_col")
    ][:6]
    case = _Case(
        scene=sc,
        characters=tuple(chars),
        victim=_VS,
        clues=tuple(_Clue((a,)) for a in keep),
        solution={},
        variant="classic",
    )
    a = _cp(case, cap=CAP, time_limit_s=20).solutions
    b = _dfs(case, cap=CAP).solutions
    if len(a) >= CAP or len(b) >= CAP:
        _pytest.skip("capped; the sets are not comparable")
    assert sorted(tuple(sorted(s.items())) for s in a) == sorted(
        tuple(sorted(s.items())) for s in b
    ), f"{len(a)} vs {len(b)} solutions"


def test_we_now_cover_the_reference_generator_vocabulary():
    """Their generator's 25 atom types, mapped to ours. Extracted from the shipped bundle's own filter
    (`.t==="..."` in generator-*.js), so the list is theirs, not a guess.

    Two of theirs are aliases of one of ours: `inCorner` and `cornerRoom` have identical filter
    conditions (`!roomCorner[cell]`) and differ only in how they are worded next to a `room` atom.
    `withOnly` rejects a cell whose object IS the named one, which is `not_on`.
    """
    theirs = {
        "absCol": "abs_col",
        "absRow": "abs_row",
        "alone": "alone",
        "alonewith": "alone_with",
        "beside": "beside",
        "colOffset": "col_offset",
        "compass": "compass",
        "cornerGrid": "in_grid_corner",
        "cornerRoom": "in_corner",
        "inCorner": "in_corner",
        "genderinroom": "tag_in_area",
        "noEmptyRoom": "no_empty_area",
        "notCorner": "not_in_corner",
        "notRoom": "not_in_area",
        "notbeside": "not_beside",
        "on": "on",
        "oneOnType": "exactly_one_on",
        "onlyBeside": "only_beside",
        "onlyon": "only_on",
        "orroom": "in_areas",
        "otherbeside": "other_beside",
        "room": "in_area",
        "rowOffset": "row_offset",
        "with": "with",
        "withOnly": "not_on",
    }
    assert len(theirs) == 25
    missing = sorted({v for v in theirs.values() if v not in _SPECS})
    assert not missing, f"their generator uses predicates we lack: {missing}"
