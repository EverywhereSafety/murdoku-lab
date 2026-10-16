"""The 24x24 contest board's own clue shapes: semantics, encoding and deduction must agree.

These four families came from reading the reference contest board, which states things our
vocabulary could not: an absence over a whole line, a witness at a row offset, an exclusion over
an adjacent line, and a bound rather than an exact offset. Each one is implemented three times —
as truth (`atoms.holds`), as a CP constraint (`solver/exact.py`) and as a deduction rule
(`solver/logic.py`) — so each needs checking against the others.

The board here is small enough to enumerate every legal placement, which makes the encoding check
exact rather than sampled: a disagreement of one placement is a bug, not noise.
"""

import itertools
import random

import pytest

from murdoku_lab.core.atoms import Atom, holds_atom
from murdoku_lab.core.board import Prop, Scene
from murdoku_lab.core.instance import Case, Clue
from murdoku_lab.solver.exact import enumerate_cp
from murdoku_lab.solver.logic import Deducer

N = 5
CHARS = tuple("ABCDE")
TAGS = {x: frozenset({"hat"}) if i % 2 else frozenset() for i, x in enumerate(CHARS)}


def _scene(seed=0):
    """Three horizontal bands, so every area is 4-connected, plus two distinct props."""
    rng = random.Random(seed)
    cut1, cut2 = sorted(rng.sample(range(1, N), 2))
    areas = tuple(
        0 if k // N < cut1 else (1 if k // N < cut2 else 2) for k in range(N * N)
    )
    picks = rng.sample(range(N * N), 5)
    props = (
        Prop("tombstone", False, frozenset(picks[:2])),
        Prop("chair", True, frozenset(picks[2:])),
    )
    return Scene(N, N, areas, (None,) * (N * N), props=props)


def _placements(scene):
    out = []
    for rows in itertools.permutations(range(N)):
        for cols in itertools.permutations(range(N)):
            pl = {x: rows[i] * N + cols[i] for i, x in enumerate(CHARS)}
            if all(k in scene.open_cells for k in pl.values()):
                out.append(pl)
    return out


def _case(scene, clues, solution, seed=0):
    return Case(
        scene=scene,
        characters=CHARS,
        victim=CHARS[-1],
        clues=clues,
        solution=solution,
        tags=TAGS,
        variant="course",
        seed=seed,
    )


CONTEST_ATOMS = (
    [Atom("offset_witness", "A", ("tombstone", d)) for d in (-2, -1, 1, 2)]
    + [
        Atom("offset_min", "A", ("B", axis, d))
        for axis in ("row", "column")
        for d in (-2, -1, 1, 2)
    ]
    + [Atom("no_tag_near", "A", ("hat", axis)) for axis in ("row", "column")]
    + [
        Atom("col_free_of", "A", ("tombstone",)),
        Atom("row_free_of", "A", ("tombstone",)),
        Atom("area_side", "A", ("top row",)),
        Atom("area_side", "A", ("easternmost column",)),
    ]
)


@pytest.mark.parametrize("atom", CONTEST_ATOMS, ids=lambda a: f"{a.kind}{a.args}")
def test_cp_encoding_admits_exactly_the_placements_the_atom_accepts(atom):
    """Brute force over every legal placement, then the same board through CP-SAT."""
    scene = _scene()
    placements = _placements(scene)
    accepted = [pl for pl in placements if holds_atom(atom, scene, pl, TAGS)]
    if not accepted:
        pytest.skip("atom is unsatisfiable on this board")
    case = _case(scene, (Clue((atom,)),), accepted[0])
    # The CP model also enforces the murderer rule, which the brute force above does not.
    expected = {
        tuple(sorted(pl.items()))
        for pl in accepted
        if sum(
            1 for k in pl.values() if scene.area_of[k] == scene.area_of[pl[case.victim]]
        )
        == 2
    }
    result = enumerate_cp(case, cap=None, time_limit_s=120)
    assert not result.timed_out
    assert {tuple(sorted(pl.items())) for pl in result.solutions} == expected


def _random_contest_case(seed):
    rng = random.Random(1000 + seed)
    scene = _scene(seed)
    placements = _placements(scene)
    if not placements:
        return None
    truth = rng.choice(placements)
    pool = []
    for x in CHARS:
        others = [y for y in CHARS if y != x]
        for d in (-2, -1, 1, 2):
            pool.append(Atom("offset_witness", x, ("tombstone", d)))
            pool.append(
                Atom(
                    "offset_min",
                    x,
                    (rng.choice(others), rng.choice(("row", "column")), d),
                )
            )
        for axis in ("row", "column"):
            pool.append(Atom("no_tag_near", x, ("hat", axis)))
        pool += [
            Atom("col_free_of", x, ("tombstone",)),
            Atom("row_free_of", x, ("tombstone",)),
            Atom("area_side", x, ("top row",)),
            Atom("on", x, ("chair",)),
            Atom("beside", x, ("tombstone",)),
        ]
    true_atoms = [a for a in pool if holds_atom(a, scene, truth, TAGS)]
    if not true_atoms:
        return None
    rng.shuffle(true_atoms)
    picked = true_atoms[: rng.randint(2, min(8, len(true_atoms)))]
    return _case(scene, tuple(Clue((a,)) for a in picked), truth, seed)


def test_deduction_never_removes_the_intended_placement():
    """A rule that over-prunes makes a sound puzzle unsolvable; nothing else catches that."""
    checked, used_kinds = 0, set()
    for seed in range(40):
        case = _random_contest_case(seed)
        if case is None:
            continue
        checked += 1
        used_kinds |= {a.kind for a in case.atoms}
        certificate = Deducer(case).run(include_probe=False)
        for x in case.characters:
            k = case.solution[x]
            if x in certificate.placed:
                assert certificate.placed[x] == k, (seed, x)
            else:
                # Empty domains are omitted from both certificate mappings.
                assert k in certificate.stuck.get(x, ()), (seed, x)
    assert checked >= 20
    assert {"offset_witness", "no_tag_near", "offset_min"} <= used_kinds


def test_deduction_rules_actually_fire():
    """A rule that never runs is trivially sound, so the soundness test above needs this."""
    fired = set()
    for seed in range(40):
        case = _random_contest_case(seed)
        if case is None:
            continue
        fired |= {s.kind for s in Deducer(case).run(include_probe=False).steps}
    assert {"witness", "exclusion"} <= fired


def test_logic_and_cp_agree_on_what_is_solved():
    for seed in range(40):
        case = _random_contest_case(seed)
        if case is None:
            continue
        certificate = Deducer(case).run(include_probe=False)
        if not certificate.solved:
            continue
        result = enumerate_cp(case, cap=5, time_limit_s=60)
        if result.timed_out:
            continue
        assert certificate.placed in result.solutions, seed
