"""The math setter: scene -> hidden solution -> true-clue pool -> carve to a target band.

Order matters and is the whole safety argument: we sample the *solution first*, then derive
clues that are true of it, then carve the clue set down. So a clue can never be false, and the
intended solution is a solution by construction. What carving establishes is that it is the *only*
one, and that a person can reach it by pure logic.

Difficulty is controlled by *where we stop carving* plus targeted repair. Carving is the
monotone knob: dropping a clue can only make the optimal deduction chain more expensive (extra
information never blocks a sound propagator), until the case goes ambiguous.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from murdoku_lab.core.atoms import SPECS, Atom, holds_atom
from murdoku_lab.core.board import (
    BLOCKING_OBJECTS,
    LANDMARKS,
    OCCUPIABLE_OBJECTS,
    OBJECTS,
    Prop,
    TERRAINS,
    Scene,
)
from murdoku_lab.core.instance import Case, Clue, MURDERER_RULES, VARIANTS, Variant
from murdoku_lab.solver.exact import unique_solution
from murdoku_lab.solver.logic import Certificate, certify

CHAR_SYMBOLS = "ABCDEFGHIJKLMNOPQRSTU"
VICTIM_SYMBOL = "V"


# =============================================================================================
# 1. Scene generation — binary space partition into areas, then objects.
# =============================================================================================
def gen_scene(
    n: int,
    n_areas: int,
    rng: random.Random,
    *,
    blocker_rate: float = 0.14,
    furniture_rate: float = 0.10,
    door_rate: float = 0.35,
    terrain: tuple[str, ...] = (),
    terrain_rate: float = 0.0,
    blob_scale: int = 3,
    objects: tuple[str, ...] = (),
    prop_mix: tuple[tuple[str, int], ...] = (),
) -> Scene:
    """A board. `terrain` turns on the region layer: instead of scattering single cells, terrain is
    grown in blobs, because that is what makes it usable as a clue anchor on a large board — a lone
    sand square localises nothing, a bunker does.
    """

    def finish(scene):
        from .scene_layout import enrich_scene

        shape = rng.random() < 0.65
        return enrich_scene(
            scene, rng, anonymous=bool(prop_mix), door_rate=door_rate, shape_areas=shape
        )

    rects = [(0, 0, n, n)]  # (r0, c0, h, w)
    guard = 0
    while len(rects) < n_areas and guard < 400:
        guard += 1
        splittable = [x for x in rects if x[2] * x[3] >= 4 and (x[2] >= 2 or x[3] >= 2)]
        if not splittable:
            break
        splittable.sort(key=lambda x: -x[2] * x[3])
        tgt = splittable[0] if rng.random() < 0.65 else rng.choice(splittable[:3])
        r0, c0, h, w = tgt
        horiz = h > w if h != w else rng.random() < 0.5
        if horiz and h >= 2:
            margin = max(2, h // 4) if h >= 4 else 1
            cut = rng.randint(margin, h - margin)
            new = [(r0, c0, cut, w), (r0 + cut, c0, h - cut, w)]
        elif w >= 2:
            margin = max(2, w // 4) if w >= 4 else 1
            cut = rng.randint(margin, w - margin)
            new = [(r0, c0, h, cut), (r0, c0 + cut, h, w - cut)]
        else:
            continue
        rects.remove(tgt)
        rects.extend(new)

    area_of = [0] * (n * n)
    for a, (r0, c0, h, w) in enumerate(rects):
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                area_of[r * n + c] = a

    obj_of: list[str | None] = [None] * (n * n)
    cells = list(range(n * n))
    rng.shuffle(cells)
    n_block = int(len(cells) * blocker_rate)
    n_furn = int(len(cells) * furniture_rate)
    if prop_mix:
        # Anonymous props: the board says how many of each class it carries and nothing about what
        # they are. Footprints are one cell each here; `Prop.cells` is a set so that per-instance,
        # multi-cell props (a carpet covers several squares) are a change of contents, not of shape.
        spec: list[tuple[str, bool, bool]] = []
        for cls, count in prop_mix:
            for _ in range(count):
                spec.append((cls, cls == "standable", cls == "landmark"))
        rng.shuffle(spec)
        n_props = min(len(spec), max(1, n_block + n_furn))
        chosen = spec[:n_props]
        picks = cells[: n_block + n_furn]
        props = []
        for i, (cls, standable, landmark) in enumerate(chosen):
            own = picks[i::n_props]
            if not own:
                continue
            props.append(
                Prop(
                    pid=f"p{i}",
                    standable=standable,
                    cells=frozenset(own),
                    landmark=landmark,
                )
            )
        terrain_of = _gen_terrain(n, rng, terrain, terrain_rate, blob_scale)
        scene = Scene(
            n,
            n,
            tuple(area_of),
            (None,) * (n * n),
            terrain_of=terrain_of,
            props=tuple(props),
        )
        joins = [
            frozenset((k, m))
            for k in range(scene.n_cells)
            for m in scene.neighbours(k)
            if m > k
            and scene.area_of[m] != scene.area_of[k]
            and k in scene.open_cells
            and m in scene.open_cells
        ]
        rng.shuffle(joins)
        doors = frozenset(joins[: max(0, int(len(joins) * door_rate))])
        return finish(
            Scene(
                n,
                n,
                tuple(area_of),
                (None,) * (n * n),
                doors,
                terrain_of=terrain_of,
                props=tuple(props),
            )
        )

    # Draw from the variant's own palette. Sampling the global catalogue would mean that adding an
    # object kind changes every board a fixed seed produces — which is exactly what happened when
    # the golf props were registered.
    allow = set(objects) if objects else None

    def pick(pool):
        cands = [o for o in pool if o != "void" and (allow is None or o in allow)]
        return rng.choice(cands) if cands else None

    for k in cells[:n_block]:
        obj_of[k] = pick(LANDMARKS if rng.random() < 0.3 else BLOCKING_OBJECTS) or pick(
            BLOCKING_OBJECTS
        )
    for k in cells[n_block : n_block + n_furn]:
        obj_of[k] = pick(OCCUPIABLE_OBJECTS)

    terrain_of = _gen_terrain(n, rng, terrain, terrain_rate, blob_scale)
    # A non-standable terrain (water) removes its cell, so do not also stack a blocker on it:
    # that wastes furniture and makes the board look arbitrary.
    for k, t in enumerate(terrain_of):
        if not TERRAINS[t].standable:
            obj_of[k] = None

    scene = Scene(n, n, tuple(area_of), tuple(obj_of), terrain_of=terrain_of)
    # doors: a sample of 4-adjacent cross-area pairs, both sides standable
    joins = []
    for k in range(scene.n_cells):
        for m in scene.neighbours(k):
            if (
                m > k
                and scene.area_of[m] != scene.area_of[k]
                and k in scene.open_cells
                and m in scene.open_cells
            ):
                joins.append(frozenset((k, m)))
    rng.shuffle(joins)
    doors = frozenset(joins[: max(0, int(len(joins) * door_rate))])
    # Rebuild with the doors. `terrain_of` must be carried through here — dropping it silently
    # produced an all-`floor` board while every terrain clue still claimed to be available.
    return finish(
        Scene(n, n, tuple(area_of), tuple(obj_of), doors, terrain_of=scene.terrain_of)
    )


# =============================================================================================
# 2. Sample a hidden solution: a permutation placement on standable cells.
# =============================================================================================
def _gen_terrain(
    n: int, rng: random.Random, kinds: tuple[str, ...], rate: float, blob_scale: int
) -> tuple[str, ...]:
    """Grow terrain in random blobs by repeated 4-adjacent expansion from seed cells."""
    if not kinds or rate <= 0:
        return ()
    base = kinds[0]
    out = [base] * (n * n)
    others = [t for t in kinds[1:]] or [base]
    target = int(n * n * rate)
    placed = 0
    guard = 0
    while placed < target and guard < 2000:
        guard += 1
        t = rng.choice(others)
        k = rng.randrange(n * n)
        size = rng.randint(blob_scale, blob_scale * 3)
        frontier, seen = [k], {k}
        while frontier and size > 0:
            cur = frontier.pop(rng.randrange(len(frontier)))
            if out[cur] == base:
                out[cur] = t
                placed += 1
                size -= 1
            r, c = divmod(cur, n)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                m = rr * n + cc
                if 0 <= rr < n and 0 <= cc < n and m not in seen:
                    seen.add(m)
                    frontier.append(m)
    return tuple(out)


def sample_solution(
    scene: Scene, chars: Sequence[str], rng: random.Random
) -> dict[str, int] | None:
    order = list(chars)
    rng.shuffle(order)
    pl: dict[str, int] = {}
    used_r: set[int] = set()
    used_c: set[int] = set()

    def rec(i: int) -> bool:
        if i == len(order):
            return True
        opts = [
            k
            for k in scene.open_cells
            if scene.row(k) not in used_r and scene.col(k) not in used_c
        ]
        rng.shuffle(opts)
        for k in opts:
            r, c = scene.row(k), scene.col(k)
            pl[order[i]] = k
            used_r.add(r)
            used_c.add(c)
            if rec(i + 1):
                return True
            del pl[order[i]]
            used_r.discard(r)
            used_c.discard(c)
        return False

    return dict(pl) if rec(0) else None


def assign_victim(
    scene: Scene,
    pl: dict[str, int],
    chars: Sequence[str],
    victim: str,
    rng: random.Random,
) -> dict[str, int] | None:
    """Relabel the cast so `victim` occupies a cell whose area holds exactly two characters.

    Characters are interchangeable before any clue exists, so swapping two symbols is free. This
    makes the classic murderer rule hold *by construction* rather than by rejection sampling —
    which is where the reference generator spends a third of its attempts.
    """
    by_area: dict[int, list[str]] = {}
    for x, k in pl.items():
        by_area.setdefault(scene.area_of[k], []).append(x)
    pairs = [xs for xs in by_area.values() if len(xs) == 2]
    if not pairs:
        return None
    chosen = rng.choice(pairs)
    new_victim = rng.choice(chosen)
    if new_victim == victim:
        return dict(pl)
    out = dict(pl)
    out[victim], out[new_victim] = pl[new_victim], pl[victim]
    return out


# =============================================================================================
# 3. Derive the pool of atoms that are TRUE of the hidden solution.
# =============================================================================================
def derive_pool(
    scene: Scene,
    chars: Sequence[str],
    victim: str,
    pl: dict[str, int],
    v: Variant,
    rng: random.Random,
    tags: dict[str, frozenset[str]] | None = None,
) -> list[Atom]:
    ok = v.allowed_kinds
    tags = tags or {}
    pool: list[Atom] = []

    def add(kind: str, holder: str, args: tuple = ()) -> None:
        if kind not in ok:
            return
        a = Atom(kind, holder, args)
        if holds_atom(a, scene, pl, tags):
            pool.append(a)

    objs_present = sorted(
        {o for o in scene.obj_of if o}
    )  # sorted: seeds must reproduce
    for x in chars:
        k = pl[x]
        add("in_area", x, (scene.area_of[k],))
        add("abs_row", x, (scene.row(k),))
        add("abs_col", x, (scene.col(k),))
        if scene.obj_of[k]:
            add("on", x, (scene.obj_of[k],))
            add("only_on", x, (scene.obj_of[k],))
        for o in sorted(scene.info.beside[k]):
            add("beside", x, (o,))
            add("only_beside", x, (o,))
        for o in [o for o in objs_present if o not in scene.info.beside[k]]:
            add("not_beside", x, (o,))
        for o in [o for o in objs_present if o != scene.obj_of[k]]:
            add("not_on", x, (o,))
        # terrain: a region anchor, which is what actually localises anyone on a large board
        add("in_terrain", x, (scene.terrain_of[k],))
        for t in sorted(scene.info.beside_terrain[k]):
            add("beside_terrain", x, (t,))
        for t in sorted({tt for tt in scene.terrain_of} - {scene.terrain_of[k]}):
            add("not_in_terrain", x, (t,))
        # area-number arithmetic and extremes
        add("area_no_parity", x, ("even" if scene.area_no(k) % 2 == 0 else "odd",))
        for side in ("north", "south", "west", "east"):
            add("on_extreme", x, (side,))
        for axis in ("row", "column"):
            add("not_on_extreme_axis", x, (axis,))
        # The object under x, qualified by a small set of areas including the true one.
        # The `in ok` guard is load-bearing: consuming `rng` for a kind the variant forbids shifts
        # every later draw, which silently changed what a fixed seed produced for `classic`.
        if scene.obj_of[k] and "on_in_areas" in ok:
            pool_areas = sorted(
                {
                    scene.area_of[k],
                    *rng.sample(range(scene.n_areas), min(2, scene.n_areas)),
                }
            )
            add("on_in_areas", x, (scene.obj_of[k], tuple(pool_areas)))
        # tag x object, e.g. "the only man on a golf tee"
        for tg in sorted(tags.get(x, frozenset())):
            if scene.obj_of[k]:
                add("only_tag_on", x, (tg, scene.obj_of[k]))
        for tg in sorted({t for ts in tags.values() for t in ts}):
            for o in objs_present:
                add("tag_in_area_on", x, (tg, o))
        # "someone else in my area was beside a ..." — the reference generator's `otherbeside`
        for o in objs_present:
            add("other_beside", x, (o,))
        add("in_corner", x)
        add("not_in_corner", x)
        add("in_grid_corner", x)
        add("against_wall", x)
        add("on_grid_edge", x)
        add("at_door", x)
        add("alone", x)
        for a2 in range(scene.n_areas):
            if a2 != scene.area_of[k]:
                add("not_in_area", x, (a2,))
        # a disjunction over the true area plus one decoy
        others = [a2 for a2 in range(scene.n_areas) if a2 != scene.area_of[k]]
        if others:
            add("in_areas", x, (tuple(sorted((scene.area_of[k], rng.choice(others)))),))
        for y in chars:
            if y == x:
                continue
            add("with", x, (y,))
            add("not_with", x, (y,))
            add("alone_with", x, (y,))
            add("adjacent_to", x, (y,))
            add("diagonal", x, (y,))
            add("row_offset", x, (y, scene.row(pl[x]) - scene.row(pl[y])))
            add("col_offset", x, (y, scene.col(pl[x]) - scene.col(pl[y])))
            sg = lambda t: (t > 0) - (t < 0)
            add(
                "compass",
                x,
                (
                    y,
                    sg(scene.row(pl[x]) - scene.row(pl[y])),
                    sg(scene.col(pl[x]) - scene.col(pl[y])),
                ),
            )
            add("area_no_gt", x, (y,))
            add("area_no_lt", x, (y,))
            # d == 0 is just "same area", which `with` already says far more clearly, and it
            # rendered as "0 lower than M's". Skip the degenerate case rather than render around it.
            if scene.area_no(pl[x]) != scene.area_no(pl[y]):
                add(
                    "area_no_offset",
                    x,
                    (y, scene.area_no(pl[x]) - scene.area_no(pl[y])),
                )
            for d in (-1, 1):
                add("not_area_no_offset", x, (y, d))
    for a2 in range(scene.n_areas):
        add("area_empty", chars[0], (a2,))
    for o in objs_present:
        add("exactly_one_on", chars[0], (o,))
    add("no_empty_area", chars[0])
    # general clues: shown in their own panel, about nobody in particular
    for par in ("even", "odd"):
        add("area_occupancy_parity", chars[0], (par,))
    return pool


# =============================================================================================
# 4. Build a Case from a set of atoms (grouping atoms per holder into clue sentences).
# =============================================================================================
def build_case(
    scene: Scene,
    chars: Sequence[str],
    victim: str,
    pl: dict[str, int],
    atoms: Iterable[Atom],
    variant: str,
    rng: random.Random | None = None,
    **kw,
) -> Case:
    v = VARIANTS[variant]
    # Scene-wide facts ("nobody was in the Study") read as their own statement; conjoining them
    # onto a person's sentence produces nonsense like "A was north of B, and nobody was in X".
    from .quality import SCENE_WIDE_KINDS

    by: dict[str, list[Atom]] = {}
    generals: list[Atom] = []
    for a in atoms:
        (
            generals if a.kind in SCENE_WIDE_KINDS else by.setdefault(a.holder, [])
        ).append(a)
    clues: list[Clue] = []
    for holder, group in by.items():
        for i in range(0, len(group), v.max_atoms_per_clue):
            clues.append(Clue(tuple(group[i : i + v.max_atoms_per_clue])))
    clues.extend(Clue((a,)) for a in generals)
    return Case(
        scene=scene,
        characters=tuple(chars),
        victim=victim,
        clues=tuple(clues),
        solution=dict(pl),
        variant=variant,
        **kw,
    )


# =============================================================================================
# 5. Carve: shrink the clue set while the case stays well-posed. The monotone difficulty knob.
# =============================================================================================
# Higher priority == dropped earlier. Strong, pinning, absolute clues go first: keeping the weak
# negative/relational ones is what forces a solver onto the advanced techniques.
# Higher priority == dropped earlier. The lever is *pinning power*, not polarity: shed the clues
# that collapse a person to one square, and keep the weak ones that force real chaining. Negations
# sit in the MIDDLE, not at the bottom — parking them last is what produced unreadable
# all-negation puzzles, since carving then never touched them.
DROP_PRIORITY = {
    # strongest: pins a person outright
    "on": 9,
    "only_on": 9,
    "at_door": 9,
    "in_grid_corner": 8,
    "beside": 8,
    "only_beside": 8,
    "abs_row": 7,
    "abs_col": 7,
    # strong: cuts the board down hard
    "in_area": 6,
    "alone_with": 6,
    "alone": 5,
    "area_empty": 5,
    "exactly_one_on": 5,
    # negations: weak individually, but must be shed at a comparable rate or they take over
    "not_beside": 4,
    "not_on": 4,
    "not_in_area": 4,
    "not_with": 4,
    "not_in_corner": 4,
    # weak positives: cheap to read, force chaining — these are what we want to survive
    "with": 3,
    "in_corner": 3,
    "in_areas": 3,
    "row_offset": 2,
    "col_offset": 2,
    "adjacent_to": 2,
    "no_empty_area": 2,
    "against_wall": 1,
    "on_grid_edge": 1,
    "compass": 1,
    "diagonal": 1,
    "beside_through_wall": 1,
    "tag_in_area": 3,
    # --- large-board kinds (variant `course`). Carving drops the highest priority first, so a LOW
    # number is what survives into the emitted puzzle. These are ranked low deliberately: terrain
    # regions, hole numbers and gender are the clue types that give the reference game's 16x16 its
    # character, and left at the default of 5 they were shed before the final set was reached.
    "on_in_areas": 8,
    "only_tag_on": 8,  # pin outright: an object AND a small area set
    "area_no_offset": 5,  # exact ordinal distance: strong
    "not_in_terrain": 4,
    "not_area_no_offset": 4,
    "on_extreme": 4,
    "area_no_parity": 2,
    "tag_in_area_on": 1,
    "other_beside": 2,
    "not_on_extreme_axis": 1,
    # 0 = shed last. Terrain regions and hole-number comparisons are what give the reference game's
    # large boards their character, so they must outlast the generic weak positives (`on_edge`,
    # `diagonal`, ...) that sit at 1. Safe to rank below everything because no small-board variant
    # allows these kinds, so `classic` output is untouched.
    "beside_terrain": 0,
    "in_terrain": 0,
    "area_no_gt": 0,
    "area_no_lt": 0,
    "area_occupancy_parity": 0,  # the reference game ships this as a general clue
}


def drop_priority(a: Atom) -> int:
    return DROP_PRIORITY.get(a.kind, 5)


# Atoms that can collapse a holder to a handful of cells on their own. Which of these are allowed
# into the pool is the primary difficulty lever (see murdoku_lab/resources/difficulty_bands.json:pool_bias).
STRONG_KINDS = frozenset(
    {
        "on",
        "only_on",
        "at_door",
        "in_grid_corner",
        "beside",
        "only_beside",
        "abs_row",
        "abs_col",
        "in_area",
        "alone_with",
        "alone",
        "on_in_areas",
        "only_tag_on",
    }
)


def bias_pool(
    pool: list[Atom],
    band: str,
    chars: Sequence[str],
    rng: random.Random,
    *,
    max_pool: int | None = None,
) -> list[Atom]:
    """Enforce the positional cap on pool *membership*, before carving.

    Doing it here rather than rejecting afterwards matters: every subset of a cap-respecting pool
    respects the cap, so carving can never produce a violation. Band shaping is NOT done by
    removing information from the pool -- that just makes cases ill-posed. It is done by the drop
    order during carving (`drop_priority`) and by `harden()` below.
    """
    from murdoku_lab.solver.difficulty import caps

    cap = caps(band)
    from murdoku_lab.solver.difficulty import NEGATIVE_KINDS

    max_pos = int(cap.get("max_positional", 99))
    max_neg = int(_cfg_style().get("max_negatives_per_char", 4))

    # Negations are derived combinatorially (every object x every character), so the raw pool is
    # dominated by them. Thin them per character: they are weak clues, so losing most costs no
    # well-posedness, and it keeps any carved subset readable.
    kept: list[Atom] = []
    neg_by: dict[str, list[Atom]] = {}
    for a in pool:
        if a.kind in NEGATIVE_KINDS:
            neg_by.setdefault(a.holder, []).append(a)
        else:
            kept.append(a)
    for holder, xs in neg_by.items():
        rng.shuffle(xs)
        kept.extend(xs[:max_neg])

    # global positional budget, applied to POOL MEMBERSHIP so no carved subset can violate it
    pos_idx = [i for i, a in enumerate(kept) if SPECS[a.kind].positional]
    rng.shuffle(pos_idx)
    keep_pos = set(pos_idx[:max_pos])
    out = [
        a for i, a in enumerate(kept) if not SPECS[a.kind].positional or i in keep_pos
    ]
    rng.shuffle(out)
    return _cap_pool(out, chars, rng, max_pool) if max_pool else out


def _cap_pool(
    pool: list[Atom], chars: Sequence[str], rng: random.Random, limit: int
) -> list[Atom]:
    """Bound the pool size while keeping every character represented.

    Carving costs one exact-uniqueness solve per candidate drop, so a pool that grows as
    O(cast^2) makes a 16x16 board hours of work for no benefit: the reference game's own large
    boards ship ~16 clues, not 1300. Truncating at random is not good enough, because a character
    who loses all of their atoms can never be pinned and the case is simply not well-posed. So
    deal round-robin by holder and stop at the limit.
    """
    if len(pool) <= limit:
        return pool
    by: dict[str, list[Atom]] = {}
    for a in pool:
        by.setdefault(a.holder, []).append(a)
    # Keep the INFORMATIVE atoms. Dealing at random loses the pinning ones, and a pool without them
    # simply has no unique solution — measured: a random 480-atom cap of a 2758-atom 16x16 pool left
    # 7 characters unresolved. Rank by the same strength measure carving uses, strongest first, and
    # let carving decide what to give back.
    for xs in by.values():
        xs.sort(key=lambda a: (-drop_priority(a), rng.random()))
    order = sorted(by)  # sorted: a seed must reproduce the pool exactly
    rng.shuffle(order)
    out: list[Atom] = []
    i = 0
    while len(out) < limit and any(by[h] for h in order):
        h = order[i % len(order)]
        if by[h]:
            out.append(by[h].pop(0))  # pop(0): strongest first
        i += 1
    rng.shuffle(out)
    return out


def _cfg_style() -> dict:
    from murdoku_lab.solver.difficulty import style

    return style()


@dataclass
class CarveResult:
    atoms: list[Atom]
    certificate: Certificate
    rounds: int
    dropped: int


def well_posed(
    scene: Scene,
    chars,
    victim,
    pl,
    atoms,
    variant: str,
    *,
    tags: dict | None = None,
    time_limit_s: float = 10.0,
) -> Certificate | None:
    """Unique solution (proved) AND reachable by pure logic. Returns the certificate or None."""
    case = build_case(scene, chars, victim, pl, atoms, variant, tags=tags or {})
    sol = unique_solution(case, time_limit_s=time_limit_s)
    if sol is None or sol != dict(pl):
        return None
    cert = certify(case)
    if not cert.solved or cert.placed != dict(pl):
        return None
    if VARIANTS[variant].answer == "murderer" and case.murderer is None:
        return None
    return cert


def carve(
    scene: Scene,
    chars,
    victim,
    pl,
    pool: list[Atom],
    variant: str,
    rng: random.Random,
    *,
    accept: Callable[[list[Atom], Certificate], bool] | None = None,
    tags: dict | None = None,
    coarse_threshold: int = 300,
    time_limit_s: float = 10.0,
) -> CarveResult | None:
    """Drop atoms one at a time, keeping every drop that preserves well-posedness.

    `accept(atoms, cert)` vetoes a drop *after* re-verification. Because carving can only raise
    difficulty, vetoing any drop that overshoots the target band targets that band **from above**:
    we stop while the case is still over-determined for the harder bands, and carve to exhaustion
    for the hardest. An irredundant set is the hardest case attainable for this solution.
    """
    atoms = list(pool)
    cert = well_posed(
        scene, chars, victim, pl, atoms, variant, tags=tags, time_limit_s=time_limit_s
    )
    if cert is None:
        return None
    order = sorted(
        range(len(atoms)), key=lambda i: (-drop_priority(atoms[i]), rng.random())
    )
    dropped = 0
    rounds = 0

    # ---- coarse phase: drop atoms in BLOCKS before touching them one at a time.
    # One exact-uniqueness solve per candidate drop makes the atom-at-a-time pass O(pool), which is
    # fine for a 6x6 pool of ~60 and hopeless for a 16x16 pool of ~1250. Capping the pool instead
    # does not work: the information needed for uniqueness is spread thin across it, and a
    # strength-ranked 720-atom cap of a 1238-atom pool still left four characters unresolved.
    # Halving-style block removal gets to the same place in O(k log n) solves, and the fine pass
    # below still guarantees irredundancy. Engaged only above a threshold, so small boards — and
    # therefore every `classic` seed — carve exactly as they did before.
    if len(atoms) > coarse_threshold:
        step = max(1, len(atoms) // 4)
        while step > 1:
            i = 0
            ordered = sorted(atoms, key=lambda a: (-drop_priority(a), rng.random()))
            while i < len(ordered):
                block = [a for a in ordered[i : i + step] if a in atoms]
                if not block:
                    i += step
                    continue
                rounds += 1
                keep = [a for a in atoms if a not in block]
                if not keep:
                    i += step
                    continue
                c2 = well_posed(
                    scene,
                    chars,
                    victim,
                    pl,
                    keep,
                    variant,
                    tags=tags,
                    time_limit_s=time_limit_s,
                )
                if c2 is not None and (accept is None or accept(keep, c2)):
                    atoms, cert = keep, c2
                    dropped += len(block)
                i += step
            step //= 2
        order = sorted(
            range(len(atoms)), key=lambda i: (-drop_priority(atoms[i]), rng.random())
        )

    # ---- fine phase, run to a FIXPOINT rather than one pass over the atoms.
    # A drop refused now can become acceptable later: `accept` vetoes overshooting the target band, and
    # whether a particular drop overshoots depends on what else is still present. A single pass
    # therefore stops well above the style caps — on 7x7 anonymous boards it left ~25 atoms against a
    # cap of 17, and `style_floor` rejected 280 of 349 attempts, a hit rate of 0.014. Repeating until
    # nothing more can go costs a few more solves and is the difference between a usable yield and not.
    # Bounded by a total solve budget, not by a sweep count. Sweeping to a true fixpoint costs
    # O(sweeps x atoms) exact solves, which is fine on a 60-atom 6x6 pool and ruinous on the ~1250 a
    # 16x16 produces — it turned a seven-minute test suite into one that had not finished in eleven.
    # The budget scales with the pool, so small boards still reach a fixpoint and large ones stop
    # somewhere useful instead of not stopping.
    # Measured from HERE, not from the original pool. The coarse phase has already cut a 16x16
    # board from ~1250 atoms to a few dozen, so sizing the budget off the pool gave 5000 rounds of
    # exact solving and a single attempt stopped finishing at all. Sizing it off what is actually
    # left keeps the fine phase proportional to the work remaining: small boards still reach a true
    # fixpoint, large ones stay in the cost class they were in before sweeping was added.
    # Sweeping exists to fix YIELD on small boards: one pass left ~25 atoms against a style cap of 17
    # and `style_floor` rejected 280 of 349 attempts. On a board whose pool needed the coarse phase at
    # all, the fine pass is already the expensive part and sweeping it tripled a 16x16 attempt for no
    # benefit — those pools are large enough that one pass gets well under the cap. So sweep where it
    # helps and do not where it only costs.
    max_sweeps = 1 if len(pool) > coarse_threshold else 12
    budget = rounds + max(60, 4 * len(atoms))
    for _sweep in range(max_sweeps):
        if rounds >= budget:
            break
        progressed = False
        order = sorted(
            range(len(atoms)), key=lambda i: (-drop_priority(atoms[i]), rng.random())
        )
        for target in [atoms[i] for i in order]:
            if rounds >= budget:
                break
            rounds += 1
            if target not in atoms:
                continue
            trial = [a for a in atoms if a is not target]
            c2 = well_posed(
                scene,
                chars,
                victim,
                pl,
                trial,
                variant,
                tags=tags,
                time_limit_s=time_limit_s,
            )
            if c2 is None:
                continue
            if accept is not None and not accept(trial, c2):
                continue
            atoms, cert = trial, c2
            dropped += 1
            progressed = True
        if not progressed:
            break
    return CarveResult(atoms, cert, rounds, dropped)


def harden(
    scene: Scene,
    chars,
    victim,
    pl,
    atoms: list[Atom],
    pool: list[Atom],
    variant: str,
    rng: random.Random,
    *,
    target_index: int,
    band_of,
    budget: int = 80,
    accept: Callable[[list[Atom], Certificate], bool] | None = None,
    tags: dict | None = None,
    time_limit_s: float = 10.0,
) -> tuple[list[Atom], Certificate] | None:
    """Raise difficulty by *swapping* a strong clue for a weak one, keeping well-posedness.

    Carving alone bottoms out at an irredundant set, which is often still easy: whichever strong,
    pinning clues remain necessary keep the chain shallow. The move that actually raises difficulty
    is substitution -- drop a strong clue and pay for it with one or more weak ones. Each accepted
    swap is verified well-posed, and rejected outright if it would *lower* the band, so difficulty
    is monotone along the search path.
    """
    cur = well_posed(
        scene, chars, victim, pl, atoms, variant, tags=tags, time_limit_s=time_limit_s
    )
    if cur is None:
        return None
    best = (list(atoms), cur)
    spare = [a for a in pool if a not in atoms]
    for _ in range(budget):
        cur_atoms, cur_cert = best
        if band_of(cur_cert) is not None and band_of(cur_cert) >= target_index:
            break
        strong = [a for a in cur_atoms if a.kind in STRONG_KINDS]
        if not strong or not spare:
            break
        out_a = rng.choice(strong)
        weak = [a for a in spare if a.kind not in STRONG_KINDS]
        if not weak:
            break
        rng.shuffle(weak)
        for in_a in weak[:6]:
            trial = [a for a in cur_atoms if a is not out_a] + [in_a]
            c2 = well_posed(
                scene,
                chars,
                victim,
                pl,
                trial,
                variant,
                tags=tags,
                time_limit_s=time_limit_s,
            )
            if c2 is None:
                continue
            if accept is not None and not accept(trial, c2):
                continue
            b_new, b_old = band_of(c2), band_of(cur_cert)
            if b_new is None or (b_old is not None and b_new < b_old):
                continue  # never accept a move that makes the case easier
            best = (trial, c2)
            spare.remove(in_a)
            spare.append(out_a)
            break
        else:
            # no productive swap for this strong clue; retire it from consideration
            strong.remove(out_a)
            if not strong:
                break
    return best
