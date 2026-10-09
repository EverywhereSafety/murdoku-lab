"""The human-style deduction engine: candidate propagation with a ranked technique ladder.

This is the instrument that *measures* difficulty. It never guesses: it applies the cheapest
applicable technique, records the step, and repeats. If it runs out of techniques before the
placement is determined, the case is **not** pure-logic solvable and the gate rejects it — we do
not fall back to search and call the case solved.

Every rule here must be *sound*: it may only discard a cell that appears in no solution. Each
technique documents its soundness argument. Rules that assume every row/column is occupied are
guarded on `variant.cast_fills_board`.

Two products:
  * `certify(case)` — the canonical certificate: deterministic, cheapest-technique-first.
  * `optimal_certificate(case)` (murdoku_lab/solver/optimal.py) — the provably min-cost chain, budgeted.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from itertools import combinations
from typing import Callable, Iterable, Mapping

from murdoku_lab.core.atoms import SPECS, Atom
from murdoku_lab.core.board import Scene
from murdoku_lab.core.instance import Case
from .exact import candidate_masks

# Technique tiers. The cost model for "how hard is this step for a person".
# 1 = look at one clue / one line.  2 = combine a clue with the placed set.
# 3 = reason about a *set* of characters at once (subsets, blocking).  4 = closing moves.
TIER_COST = {1: 1.0, 2: 2.0, 3: 5.0, 4: 3.0}
ADVANCED_KINDS = frozenset(
    {
        "naked_subset",
        "hidden_subset",
        "xblock",
        "last",
        "parity",
        "counting",
        "matching",
        "area_projection",
        "probe",
    }
)


@dataclass
class Step:
    kind: str
    tier: int
    text: str
    placed: tuple[str, int] | None = None
    removed: int = 0

    def to_json(self) -> dict:
        d = {
            "kind": self.kind,
            "tier": self.tier,
            "text": self.text,
            "removed": self.removed,
        }
        if self.placed:
            d["placed"] = [self.placed[0], self.placed[1]]
        return d


@dataclass
class State:
    """Mutable deduction state: per-character candidate cells, plus what is already pinned."""

    scene: Scene
    cand: dict[str, set[int]]
    placed: dict[str, int] = field(default_factory=dict)

    def key(self) -> tuple:
        return tuple(sorted((x, tuple(sorted(c))) for x, c in self.cand.items()))

    def clone(self) -> "State":
        return State(
            self.scene, {x: set(c) for x, c in self.cand.items()}, dict(self.placed)
        )

    @property
    def solved(self) -> bool:
        return all(len(c) == 1 for c in self.cand.values())

    @property
    def dead(self) -> bool:
        return any(not c for c in self.cand.values())

    @property
    def width(self) -> int:
        """How much a person must hold in their head: total live candidates."""
        return sum(len(c) for c in self.cand.values())

    def rows_of(self, x: str) -> set[int]:
        return {self.scene.row(k) for k in self.cand[x]}

    def cols_of(self, x: str) -> set[int]:
        return {self.scene.col(k) for k in self.cand[x]}

    def areas_of(self, x: str) -> set[int]:
        return {self.scene.area_of[k] for k in self.cand[x]}


@dataclass
class Certificate:
    solved: bool
    steps: list[Step]
    placed: dict[str, int]
    place_order: list[str]
    stuck: dict[str, list[int]] = field(default_factory=dict)
    max_width: int = 0

    # ------------------------------------------------------------- the difficulty vector
    @property
    def tier_hist(self) -> dict[int, int]:
        h: dict[int, int] = {}
        for s in self.steps:
            h[s.tier] = h.get(s.tier, 0) + 1
        return h

    @property
    def tier_max(self) -> int:
        return max((s.tier for s in self.steps), default=0)

    @property
    def depth(self) -> int:
        return len(self.steps)

    @property
    def advanced(self) -> int:
        """Steps of an advanced kind — the reference generator's difficulty proxy."""
        return sum(1 for s in self.steps if s.kind in ADVANCED_KINDS)

    @property
    def cost(self) -> float:
        return sum(TIER_COST[s.tier] for s in self.steps)

    @property
    def bottleneck(self) -> Step | None:
        """The hardest step; removing its enabling clue is what breaks the chain."""
        return max(self.steps, key=lambda s: (s.tier, s.removed), default=None)

    def to_json(self) -> dict:
        return {
            "solved": self.solved,
            "depth": self.depth,
            "tier_max": self.tier_max,
            "tier_hist": {str(k): v for k, v in sorted(self.tier_hist.items())},
            "advanced": self.advanced,
            "cost": round(self.cost, 3),
            "max_width": self.max_width,
            "guess_free": self.solved,
            "place_order": list(self.place_order),
            "bottleneck": self.bottleneck.to_json() if self.bottleneck else None,
            "steps": [s.to_json() for s in self.steps],
        }


# =============================================================================================
# Engine
# =============================================================================================
class Deducer:
    def __init__(self, case: Case):
        self.case = case
        self.scene = case.scene
        self.v = case.vdef
        self.chars = list(case.characters)
        self.atoms = list(case.atoms)
        self.tags = dict(case.tags)
        self.fills = (
            self.v.cast_fills_board and len(self.chars) == self.scene.H == self.scene.W
        )

    # ------------------------------------------------------------------------ initialisation
    def initial(self) -> tuple[State, Step]:
        cand = {x: set(m) for x, m in candidate_masks(self.case).items()}
        st = State(self.scene, cand)
        blocked = len(self.scene.info.blocked)
        return st, Step(
            "setup",
            1,
            f"Mark the cells each clue allows. {blocked} cell(s) are unusable "
            f"(a table, shelf, plant or the like stands there); "
            f"{st.width} candidate placements remain across {len(self.chars)} people.",
        )

    # ---------------------------------------------------------------------------- primitives
    def _place(self, st: State, x: str, k: int) -> int:
        """Pin x to k and clear its row and column for everyone else. Returns cells removed."""
        st.cand[x] = {k}
        st.placed[x] = k
        r, c = self.scene.row(k), self.scene.col(k)
        n = 0
        for z in self.chars:
            if z == x:
                continue
            gone = {
                m
                for m in st.cand[z]
                if m == k or self.scene.row(m) == r or self.scene.col(m) == c
            }
            n += len(gone)
            st.cand[z] -= gone
        return n

    # =========================================================================================
    # TIER 1 — read one clue, or one line
    # =========================================================================================
    def t_single(self, st: State) -> Step | None:
        """A character with exactly one candidate must be there. (Trivially sound.)"""
        for x in self.chars:
            if len(st.cand[x]) == 1 and x not in st.placed:
                k = next(iter(st.cand[x]))
                n = self._place(st, x, k)
                return Step(
                    "single",
                    1,
                    f"Only one square is still possible for {x}: {self._cell(k)}. "
                    f"Row {self.scene.row(k)+1} and column {self.scene.col(k)+1} "
                    f"are now closed to everyone else.",
                    placed=(x, k),
                    removed=n,
                )
        return None

    def t_line(self, st: State) -> Step | None:
        """If exactly one character can occupy a row (or column), they occupy it.

        Sound only when every row/column is occupied, i.e. the cast fills the board.
        """
        if not self.fills:
            return None
        for axis, size, of in (
            ("row", self.scene.H, self.scene.row),
            ("column", self.scene.W, self.scene.col),
        ):
            for i in range(size):
                who = [x for x in self.chars if any(of(k) == i for k in st.cand[x])]
                if len(who) == 1:
                    x = who[0]
                    keep = {k for k in st.cand[x] if of(k) == i}
                    if keep != st.cand[x]:
                        n = len(st.cand[x]) - len(keep)
                        st.cand[x] = keep
                        return Step(
                            "line",
                            1,
                            f"{x} is the only person who can be in {axis} {i+1}, and "
                            f"every {axis} holds someone — so {x} is there.",
                            removed=n,
                        )
        return None

    def t_exclusive(self, st: State) -> Step | None:
        """Direct consequences of exclusive atoms that need no placement yet.

        `only_on(obj)` / `only_beside(obj)`: nobody else may be on/beside that object.
        `area_empty(a)`: nobody may be in area a.  Both are immediate and sound.
        """
        for a in self.atoms:
            if a.kind == "only_tag_on":
                # `only_on` restricted to the tag-bearers: no OTHER character carrying the tag may
                # stand on the object. The holder's own cells come from the atom's mask.
                tgt = set(self.scene.cells_with_object(a["obj"]))
                tag = a["tag"]
                n = 0
                for z in self.chars:
                    if z == a.holder or tag not in self.tags.get(z, frozenset()):
                        continue
                    gone = st.cand[z] & tgt
                    n += len(gone)
                    st.cand[z] -= gone
                if n:
                    return Step(
                        "exclusive",
                        1,
                        f"{a.holder} was the only {tag} on a {a['obj']} — every other "
                        f"{tag} is cleared off those {len(tgt)} square(s) "
                        f"({n} candidate(s)).",
                        removed=n,
                    )
            elif a.kind in ("only_on", "only_beside"):
                tgt = (
                    self.scene.cells_with_object(a["obj"])
                    if a.kind == "only_on"
                    else self.scene.cells_beside(a["obj"])
                )
                n = 0
                for z in self.chars:
                    if z == a.holder:
                        continue
                    gone = st.cand[z] & tgt
                    n += len(gone)
                    st.cand[z] -= gone
                if n:
                    word = "on" if a.kind == "only_on" else "beside"
                    return Step(
                        "exclusive",
                        1,
                        f"{a.holder} was the only person {word} a {a['obj']} — every "
                        f"other person is wiped off those {len(tgt)} square(s) "
                        f"({n} candidate(s) cleared).",
                        removed=n,
                    )
            elif a.kind == "area_empty":
                tgt = set(self.scene.cells_of_area(a["area"]))
                n = 0
                for z in self.chars:
                    gone = st.cand[z] & tgt
                    n += len(gone)
                    st.cand[z] -= gone
                if n:
                    return Step(
                        "exclusive",
                        1,
                        f"Area {a['area']} held nobody: {n} candidate(s) cleared.",
                        removed=n,
                    )
        return None

    # =========================================================================================
    # TIER 2 — combine a clue with what is already known
    # =========================================================================================
    def t_pairwise(self, st: State) -> Step | None:
        """Arc consistency on relational atoms: drop any cell with no partner cell.

        Sound: if no cell of the partner's candidate set can satisfy the relation together with
        cell k, then no solution places the holder at k.
        """
        for a in self.atoms:
            spec = SPECS[a.kind]
            if spec.arity != "pair":
                continue
            x, y = a.holder, a["other"]
            rel = self._relation(a)
            nx = {k for k in st.cand[x] if any(rel(k, m) for m in st.cand[y])}
            ny = {m for m in st.cand[y] if any(rel(k, m) for k in st.cand[x])}
            n = (len(st.cand[x]) - len(nx)) + (len(st.cand[y]) - len(ny))
            if n:
                st.cand[x], st.cand[y] = nx, ny
                return Step(
                    "relational",
                    2,
                    f"Cross-checking the clue linking {x} and {y} ({a.kind}) removes "
                    f"{n} candidate(s).",
                    removed=n,
                )
        return None

    def t_area(self, st: State) -> Step | None:
        """Area-level reasoning for `alone` / `alone_with`.

        If the holder's area is pinned down, everyone excluded from it loses those cells; and if
        another character is confined to that area, the holder cannot be there. Both sound.
        """
        for a in self.atoms:
            if a.kind not in ("alone", "alone_with"):
                continue
            x = a.holder
            keep = {x} if a.kind == "alone" else {x, a["other"]}
            ax = st.areas_of(x)
            if len(ax) == 1:
                ar = next(iter(ax))
                tgt = set(self.scene.cells_of_area(ar))
                n = 0
                for z in self.chars:
                    if z in keep:
                        continue
                    gone = st.cand[z] & tgt
                    n += len(gone)
                    st.cand[z] -= gone
                if n:
                    who = "alone" if a.kind == "alone" else f"alone with {a['other']}"
                    return Step(
                        "alone",
                        2,
                        f"{x} was {who} and can only be in area {ar}, so nobody else "
                        f"can be there: {n} candidate(s) cleared.",
                        removed=n,
                    )
            # converse: a third party confined to an area evicts the holder from it
            n = 0
            for z in self.chars:
                if z in keep:
                    continue
                az = st.areas_of(z)
                if len(az) == 1:
                    ar = next(iter(az))
                    gone = {k for k in st.cand[x] if self.scene.area_of[k] == ar}
                    n += len(gone)
                    st.cand[x] -= gone
                    if a.kind == "alone_with":
                        o = a["other"]
                        g2 = {k for k in st.cand[o] if self.scene.area_of[k] == ar}
                        n += len(g2)
                        st.cand[o] -= g2
            if n:
                return Step(
                    "alone",
                    2,
                    f"Someone else is pinned to an area {x} would have had to itself — "
                    f"{n} candidate(s) cleared.",
                    removed=n,
                )
        return None

    # =========================================================================================
    # TIER 3 — reason about a set of characters at once (the "advanced" techniques)
    # =========================================================================================
    def t_naked_subset(self, st: State, max_k: int = 3) -> Step | None:
        """k characters confined to k rows (or columns) own those lines exclusively.

        Sound: each of the k characters occupies one of those k lines, and each line holds at
        most one person, so the k lines are consumed and no one else may use them.
        """
        for axis, of in (("row", self.scene.row), ("column", self.scene.col)):
            live = [x for x in self.chars if len(st.cand[x]) > 1]
            for k in range(2, min(max_k, len(live)) + 1):
                for grp in combinations(live, k):
                    lines = set()
                    for x in grp:
                        lines |= {of(c) for c in st.cand[x]}
                    if len(lines) != k:
                        continue
                    n = 0
                    for z in self.chars:
                        if z in grp:
                            continue
                        gone = {c for c in st.cand[z] if of(c) in lines}
                        n += len(gone)
                        st.cand[z] -= gone
                    if n:
                        return Step(
                            "naked_subset",
                            3,
                            f"{', '.join(grp)} are confined to {axis}s "
                            f"{sorted(i+1 for i in lines)} — between them they use all "
                            f"{k}, so no one else can: {n} candidate(s) cleared.",
                            removed=n,
                        )
        return None

    def t_hidden_subset(self, st: State, max_k: int = 3) -> Step | None:
        """k lines that only k characters can occupy confine those characters to those lines.

        Sound only when every line is occupied (cast fills the board).
        """
        if not self.fills:
            return None
        for axis, size, of in (
            ("row", self.scene.H, self.scene.row),
            ("column", self.scene.W, self.scene.col),
        ):
            for k in range(2, min(max_k, size) + 1):
                for lines in combinations(range(size), k):
                    who = {
                        x for x in self.chars if any(of(c) in lines for c in st.cand[x])
                    }
                    if len(who) != k:
                        continue
                    n = 0
                    for x in who:
                        gone = {c for c in st.cand[x] if of(c) not in lines}
                        n += len(gone)
                        st.cand[x] -= gone
                    if n:
                        return Step(
                            "hidden_subset",
                            3,
                            f"{axis.capitalize()}s {[i+1 for i in lines]} can only be "
                            f"filled by {', '.join(sorted(who))}, so those {k} people "
                            f"are confined there: {n} candidate(s) cleared.",
                            removed=n,
                        )
        return None

    def t_xblock(self, st: State) -> Step | None:
        """If putting z on cell k would leave someone else with nowhere to go, z is not on k.

        This generalises the reference game's rectangle rule ("if a person can only occupy two
        squares, no one else can occupy the other two corners of the rectangle"). Sound: it is a
        one-step forward check.
        """
        for z in self.chars:
            if len(st.cand[z]) <= 1:
                continue
            for k in sorted(st.cand[z]):
                r, c = self.scene.row(k), self.scene.col(k)
                for x in self.chars:
                    if x == z:
                        continue
                    rest = {
                        m
                        for m in st.cand[x]
                        if m != k and self.scene.row(m) != r and self.scene.col(m) != c
                    }
                    if not rest:
                        st.cand[z].discard(k)
                        return Step(
                            "xblock",
                            3,
                            f"{z} cannot be at {self._cell(k)}: that would leave {x} "
                            f"with no square at all.",
                            removed=1,
                        )
        return None

    # =========================================================================================
    # TIER 4 — closing moves
    # =========================================================================================
    def t_last(self, st: State) -> Step | None:
        """One character left undetermined: they take the one free row/column intersection."""
        live = [x for x in self.chars if len(st.cand[x]) > 1]
        if len(live) != 1 or not self.fills:
            return None
        x = live[0]
        used_r = {self.scene.row(k) for z, k in st.placed.items() if z != x}
        used_c = {self.scene.col(k) for z, k in st.placed.items() if z != x}
        keep = {
            k
            for k in st.cand[x]
            if self.scene.row(k) not in used_r and self.scene.col(k) not in used_c
        }
        if len(keep) == 1 and keep != st.cand[x]:
            n = len(st.cand[x]) - 1
            st.cand[x] = keep
            return Step(
                "last",
                4,
                f"Everyone else is placed, so {x} takes the only row and column left.",
                removed=n,
            )
        return None

    # ------------------------------------------------------------------------------- helpers
    def _cell(self, k: int) -> str:
        r, c = self.scene.rc(k)
        return f"r{r+1}c{c+1}"

    def _relation(self, a: Atom) -> Callable[[int, int], bool]:
        """The pair relation of a relational atom, as a raw cell-pair predicate.

        The explicit cases below are fast paths, nothing more. Anything not listed falls through to
        `spec.holds` — the definition — so registering a new pair predicate can never leave the
        deduction engine raising `NotImplementedError` on a case the setter happily produced. That
        failure mode cost us a whole class of bugs when the dispatch merely raised.
        """
        s, kind = self.scene, a.kind
        if kind == "with":
            return lambda k, m: s.area_of[k] == s.area_of[m]
        if kind == "not_with":
            return lambda k, m: s.area_of[k] != s.area_of[m]
        if kind == "alone_with":
            return lambda k, m: s.area_of[k] == s.area_of[m]
        if kind == "row_offset":
            d = a["d"]
            return lambda k, m: s.row(k) - s.row(m) == d
        if kind == "col_offset":
            d = a["d"]
            return lambda k, m: s.col(k) - s.col(m) == d
        if kind == "compass":
            dr, dc = a["dr"], a["dc"]
            sg = lambda v: (v > 0) - (v < 0)
            return (
                lambda k, m: sg(s.row(k) - s.row(m)) == dr
                and sg(s.col(k) - s.col(m)) == dc
            )
        if kind == "diagonal":
            return lambda k, m: abs(s.row(k) - s.row(m)) == abs(s.col(k) - s.col(m))
        if kind == "adjacent_to":
            return lambda k, m: m in s.neighbours(k)
        if kind == "area_no_gt":
            return lambda k, m: s.area_no(k) > s.area_no(m)
        if kind == "area_no_lt":
            return lambda k, m: s.area_no(k) < s.area_no(m)
        if kind in ("area_no_offset", "not_area_no_offset"):
            d, eq = a["d"], kind == "area_no_offset"
            return lambda k, m: ((s.area_no(k) - s.area_no(m)) == d) is eq

        # Generic fallback: a pair atom's truth depends only on the two cells, so `holds` gives the
        # relation directly. Slower than a closure over ints, always correct.
        holder, other, spec = a.holder, a["other"], SPECS[kind]
        return lambda k, m: spec.holds(a, s, {holder: k, other: m})

    # ---------------------------------------------------------------------------- the ladder
    # -------------------------------------------------------------------------- counting rules
    def _area_split(self, st: State, area: int) -> tuple[list[str], list[str]]:
        """(definitely in `area`, possibly in `area`). A character is *definitely* in when every
        candidate it has left lies inside the area, and *possibly* in when some but not all do.
        """
        cells = set(self.scene.cells_of_area(area))
        sure, maybe = [], []
        for x in self.chars:
            c = st.cand[x]
            if not c:
                continue
            if c <= cells:
                sure.append(x)
            elif c & cells:
                maybe.append(x)
        return sure, maybe

    def _area_capacity(self, area: int) -> int:
        """Upper bound on how many people an area can hold.

        Placement is injective on rows *and* on columns, so an area can hold at most as many people
        as it spans distinct rows, and at most as many as it spans distinct columns.
        """
        cells = [
            k for k in self.scene.cells_of_area(area) if k in self.scene.open_cells
        ]
        if not cells:
            return 0
        return min(
            len({self.scene.row(k) for k in cells}),
            len({self.scene.col(k) for k in cells}),
        )

    def t_parity(self, st: State) -> Step | None:
        """Occupancy parity per area, bounded by the area's capacity.

        The reference game ships this as a general clue ("Even-numbered holes have an even number of
        occupants"). Reasoning about it is what their expert boards turn on.

        Let `lo` be the characters already confined to the area, `hi` the ones that could still be
        there, and `cap` the most it can physically hold. The true occupancy lies in
        `[lo, min(hi, cap)]` and must match the required parity, which leaves a set of feasible
        counts. Two sound conclusions follow:

          * if `lo` is already the largest feasible count, nobody else can be in the area;
          * if `hi` is the smallest feasible count, everybody who could be there must be.

        Both only ever discard cells that appear in no solution. The earlier version of this rule
        fired only when exactly one character was undecided, which on a 16-person board is almost
        never true at the point where the help is needed.
        """
        for a in self.atoms:
            if a.kind != "area_occupancy_parity":
                continue
            want = 0 if a["par"] == "even" else 1
            for area in range(self.scene.n_areas):
                if (area + 1) % 2 != want:
                    continue
                sure, maybe = self._area_split(st, area)
                if not maybe:
                    continue
                cells = set(self.scene.cells_of_area(area))
                lo, hi = len(sure), len(sure) + len(maybe)
                cap = self._area_capacity(area)
                feasible = [t for t in range(lo, min(hi, cap) + 1) if t % 2 == want]
                if not feasible:
                    continue  # contradiction; the search will notice elsewhere
                lowest, highest = min(feasible), max(feasible)

                if lo == highest:  # the area is already as full as parity permits
                    n = 0
                    for z in maybe:
                        gone = st.cand[z] & cells
                        n += len(gone)
                        st.cand[z] -= gone
                    if n:
                        return Step(
                            "parity",
                            3,
                            f"Area {area + 1} must hold an {a['par']} number of people and "
                            f"already has {lo} (it can hold at most {cap}), so none of "
                            f"{', '.join(maybe)} can be there ({n} candidate(s) cleared).",
                            removed=n,
                        )
                elif hi == lowest:  # everyone who could be there has to be
                    n = 0
                    for z in maybe:
                        gone = st.cand[z] - cells
                        n += len(gone)
                        st.cand[z] -= gone
                    if n:
                        return Step(
                            "parity",
                            3,
                            f"Area {area + 1} must hold an {a['par']} number of people, "
                            f"needs at least {lowest}, and only {hi} can reach it — so "
                            f"{', '.join(maybe)} are all inside "
                            f"({n} candidate(s) cleared).",
                            removed=n,
                        )
        return None

    def t_counting(self, st: State) -> Step | None:
        """`exactly_one_on(obj)` and `no_empty_area` — pigeonhole counting over the whole cast.

        Sound in both directions: if a character is already confined to the target set then nobody
        else can be there; and if only one character can reach a set that must be occupied, that
        character has to be the occupant.
        """
        for a in self.atoms:
            if a.kind == "exactly_one_on":
                tgt = set(self.scene.cells_with_object(a["obj"]))
                inside = [x for x in self.chars if st.cand[x] and st.cand[x] <= tgt]
                touching = [x for x in self.chars if st.cand[x] & tgt]
                if inside:
                    n = 0
                    for z in self.chars:
                        if z in inside:
                            continue
                        gone = st.cand[z] & tgt
                        n += len(gone)
                        st.cand[z] -= gone
                    if n:
                        return Step(
                            "counting",
                            3,
                            f"Exactly one person stood on a {a['obj']}, and "
                            f"{inside[0]} is already confined to those squares — everyone "
                            f"else is cleared off them ({n} candidate(s)).",
                            removed=n,
                        )
                elif len(touching) == 1:
                    x = touching[0]
                    gone = st.cand[x] - tgt
                    if gone:
                        st.cand[x] -= gone
                        return Step(
                            "counting",
                            3,
                            f"Exactly one person stood on a {a['obj']} and only {x} can "
                            f"reach one, so {x} is there ({len(gone)} cleared).",
                            removed=len(gone),
                        )
            elif a.kind == "no_empty_area":
                for area in range(self.scene.n_areas):
                    cells = set(self.scene.cells_of_area(area))
                    if not cells & set(self.scene.open_cells):
                        continue
                    touching = [x for x in self.chars if st.cand[x] & cells]
                    if len(touching) == 1:
                        x = touching[0]
                        gone = st.cand[x] - cells
                        if gone:
                            st.cand[x] -= gone
                            return Step(
                                "counting",
                                3,
                                f"No area was empty and only {x} can still be in area "
                                f"{area + 1}, so {x} is there ({len(gone)} cleared).",
                                removed=len(gone),
                            )
        return None

    def t_tag(self, st: State) -> Step | None:
        """`tag_in_area` / `tag_in_area_on` — someone carrying a tag shares the holder's area.

        Two sound directions. The holder can only stand in an area some tag-bearer can still reach
        (with the object, where the atom names one). And once the holder's area is pinned down, if
        only one tag-bearer can satisfy it, that character is confined to the qualifying cells.
        """
        for a in self.atoms:
            if a.kind not in ("tag_in_area", "tag_in_area_on", "other_beside"):
                continue
            tag = a.get("tag")
            obj = a.get("obj")
            beside_mode = a.kind == "other_beside"
            tagged = [
                z
                for z in self.chars
                if z != a.holder
                and (tag is None or tag in self.tags.get(z, frozenset()))
            ]
            if not tagged:
                continue

            def qualifying(z: str, area: int) -> set[int]:
                cells = set(self.scene.cells_of_area(area))
                out = st.cand[z] & cells
                if obj is None:
                    return out
                if beside_mode:
                    return {k for k in out if obj in self.scene.info.beside[k]}
                return {k for k in out if self.scene.obj_of[k] == obj}

            # (a) prune the holder: keep only areas some tag-bearer can still satisfy
            ok_areas = {
                area
                for area in range(self.scene.n_areas)
                if any(qualifying(z, area) for z in tagged)
            }
            gone = {
                k for k in st.cand[a.holder] if self.scene.area_of[k] not in ok_areas
            }
            if gone:
                st.cand[a.holder] -= gone
                what = (
                    "someone beside a " + str(obj)
                    if beside_mode
                    else (f"a {tag} on a {obj}" if obj else f"someone {tag}")
                )
                return Step(
                    "tagshare",
                    2,
                    f"{a.holder} shared an area with {what}, so areas where that is no "
                    f"longer possible are ruled out ({len(gone)} candidate(s) cleared).",
                    removed=len(gone),
                )

            # (b) holder's area pinned and only one tag-bearer can satisfy it
            areas = {self.scene.area_of[k] for k in st.cand[a.holder]}
            if len(areas) == 1:
                area = next(iter(areas))
                able = [z for z in tagged if qualifying(z, area)]
                if len(able) == 1:
                    z = able[0]
                    keep = qualifying(z, area)
                    dropped = st.cand[z] - keep
                    if dropped:
                        st.cand[z] = keep
                        what = (
                            "beside a " + str(obj)
                            if beside_mode
                            else (f"on a {obj}" if obj else "there")
                        )
                        return Step(
                            "tagshare",
                            2,
                            f"{a.holder} is in area {area + 1} and only {z} can be the "
                            f"one {what}, so {z} is confined to it "
                            f"({len(dropped)} cleared).",
                            removed=len(dropped),
                        )
        return None

    def _lines_of(self, st: State, axis: str) -> dict[str, set[int]]:
        """Which rows (or columns) each character can still occupy."""
        f = self.scene.row if axis == "row" else self.scene.col
        return {x: {f(k) for k in st.cand[x]} for x in self.chars}

    def t_matching(self, st: State) -> Step | None:
        """All-different propagation on rows and columns (a Hall-type argument).

        Exactly one character stands in each row and each column, so the character-to-row assignment
        is a perfect matching. A candidate is therefore impossible unless *some* perfect matching
        uses it — a cell in row r is only reachable for x if the remaining characters can still be
        distributed over the remaining rows. Removing candidates that no perfect matching can use is
        sound, and it is the technique these boards actually turn on: without it the engine sees
        sixteen characters with a hundred-odd candidates each and no single row or column narrow
        enough for the simpler rules to bite.

        This is the classical filtering for an all-different constraint. Implemented directly: force
        the pair, then ask whether the rest can still be matched. At sixteen characters that is a
        few hundred cheap matchings, and the clarity is worth more than Regin's SCC refinement.
        """
        import networkx as nx

        for axis in ("row", "column"):
            lines = self._lines_of(st, axis)
            f = self.scene.row if axis == "row" else self.scene.col
            n = len(self.chars)

            def max_matching(exclude_char=None, exclude_line=None) -> int:
                g = nx.Graph()
                left = []
                for x in self.chars:
                    if x == exclude_char:
                        continue
                    ls = lines[x] - (
                        {exclude_line} if exclude_line is not None else set()
                    )
                    if not ls:
                        return -1  # a character with nowhere to go
                    left.append(("c", x))
                    for ln in ls:
                        g.add_edge(("c", x), ("l", ln))
                if not left:
                    return 0
                m = nx.bipartite.maximum_matching(
                    g, top_nodes=[v for v in left if v in g]
                )
                return len(m) // 2

            base = max_matching()
            if base < n:
                return None  # already infeasible; other rules will see it

            for x in self.chars:
                bad_lines = set()
                for ln in sorted(lines[x]):
                    # force x onto line `ln`: the other n-1 characters must fill the other lines
                    if max_matching(exclude_char=x, exclude_line=ln) < n - 1:
                        bad_lines.add(ln)
                if bad_lines:
                    gone = {k for k in st.cand[x] if f(k) in bad_lines}
                    if gone:
                        st.cand[x] -= gone
                        names = ", ".join(str(b + 1) for b in sorted(bad_lines))
                        return Step(
                            "matching",
                            3,
                            f"{x} cannot take {axis} {names}: doing so would leave the "
                            f"others unable to fill one {axis} each "
                            f"({len(gone)} candidate(s) cleared).",
                            removed=len(gone),
                        )
        return None

    # ------------------------------------------------------------------- area-level projection
    def _area_domains(self, st: State) -> dict[str, set[int]]:
        return {x: {self.scene.area_of[k] for k in st.cand[x]} for x in self.chars}

    def t_area_projection(self, st: State) -> Step | None:
        """Reason about *which area* each character is in, then map the conclusion back to cells.

        This is how a person attacks a large board: before worrying about squares, you work out who
        is in which hole, using the ordering chain over hole numbers, the per-hole occupancy parity,
        and how many people a hole can physically hold. None of our other techniques can see that
        structure — they all reason cell by cell, and on a 16x16 board every character's candidates
        span every row and column, so even all-different propagation finds nothing to remove.

        **Propagation only, never search.** That restraint is deliberate and load-bearing: a
        technique that searched the projected problem would be a second exact solver wearing a
        human's clothes, would crack every puzzle in one step, and would flatten the difficulty
        measurement it is supposed to feed. What is implemented is arc consistency on the area-level
        constraints plus counting bounds, run to a fixpoint — the reasoning, not the enumeration.

        Sound because every rule below only discards an area that no solution can place the
        character in, and a cell is only removed when its area has been discarded.
        """
        s = self.scene
        n_areas, n_chars = s.n_areas, len(self.chars)
        dom = self._area_domains(st)
        if any(not d for d in dom.values()):
            return None

        cap = {a: self._area_capacity(a) for a in range(n_areas)}
        parity: dict[int, int] = {}  # area -> required parity of its occupancy
        for a in self.atoms:
            if a.kind == "area_occupancy_parity":
                want = 0 if a["par"] == "even" else 1
                for ar in range(n_areas):
                    if (ar + 1) % 2 == want:
                        parity[ar] = want
        need_all = any(a.kind == "no_empty_area" for a in self.atoms)

        def feasible(area: int, lo: int, hi: int) -> list[int]:
            hi = min(hi, cap[area])
            vals = list(range(lo, hi + 1))
            if area in parity:
                vals = [v for v in vals if v % 2 == parity[area]]
            if need_all:
                vals = [v for v in vals if v >= 1]
            return vals

        changed = True
        guard = 0
        while changed and guard < 60:
            changed = False
            guard += 1

            # ---- unary and pairwise constraints, projected onto areas ---------------------------
            for a in self.atoms:
                k, h = a.kind, a.holder
                if h not in dom:
                    continue
                before = len(dom[h])
                if k == "in_area":
                    dom[h] &= {a["area"]}
                elif k == "in_areas":
                    dom[h] &= set(a["areas"])
                elif k == "not_in_area":
                    dom[h] -= {a["area"]}
                elif k == "area_no_parity":
                    want = 0 if a["par"] == "even" else 1
                    dom[h] = {x for x in dom[h] if (x + 1) % 2 == want}
                elif k == "area_empty":
                    for z in self.chars:
                        dom[z] -= {a["area"]}
                elif k in ("with", "alone_with"):
                    o = a["other"]
                    common = dom[h] & dom[o]
                    if common != dom[h] or common != dom[o]:
                        dom[h] = set(common)
                        dom[o] = set(common)
                        changed = True
                elif k == "not_with":
                    o = a["other"]
                    if len(dom[o]) == 1:
                        dom[h] -= dom[o]
                    if len(dom[h]) == 1:
                        dom[o] -= dom[h]
                elif k == "area_no_gt":
                    o = a["other"]
                    dom[h] = {x for x in dom[h] if x > min(dom[o])}
                    dom[o] = (
                        {y for y in dom[o] if y < max(dom[h])} if dom[h] else dom[o]
                    )
                elif k == "area_no_lt":
                    o = a["other"]
                    dom[h] = {x for x in dom[h] if x < max(dom[o])}
                    dom[o] = (
                        {y for y in dom[o] if y > min(dom[h])} if dom[h] else dom[o]
                    )
                elif k == "area_no_offset":
                    o, d = a["other"], a["d"]
                    dom[h] = {x for x in dom[h] if (x - d) in dom[o]}
                    dom[o] = {y for y in dom[o] if (y + d) in dom[h]}
                elif k in ("tag_in_area", "tag_in_area_on"):
                    tag = a["tag"]
                    able = {
                        ar
                        for z in self.chars
                        if z != h and tag in self.tags.get(z, frozenset())
                        for ar in dom[z]
                    }
                    dom[h] &= able
                if len(dom[h]) != before:
                    changed = True
                if any(not d for d in dom.values()):
                    return None  # contradiction; leave it to the caller

            # ---- `alone` / `alone_with`: a pinned loner empties their area for everyone else -----
            for a in self.atoms:
                if a.kind not in ("alone", "alone_with"):
                    continue
                keep = {a.holder} | ({a["other"]} if a.kind == "alone_with" else set())
                if len(dom[a.holder]) != 1:
                    continue
                ar = next(iter(dom[a.holder]))
                for z in self.chars:
                    if z in keep or ar not in dom[z]:
                        continue
                    dom[z] -= {ar}
                    changed = True

            # ---- counting: capacity, parity, and the fact that all n characters are placed ------
            sure = {
                ar: [x for x in self.chars if dom[x] == {ar}] for ar in range(n_areas)
            }
            maybe = {
                ar: [x for x in self.chars if ar in dom[x] and len(dom[x]) > 1]
                for ar in range(n_areas)
            }
            lo = {ar: len(sure[ar]) for ar in range(n_areas)}
            hi = {ar: min(cap[ar], lo[ar] + len(maybe[ar])) for ar in range(n_areas)}
            for ar in range(n_areas):
                f = feasible(ar, lo[ar], hi[ar])
                if f:
                    lo[ar], hi[ar] = max(lo[ar], min(f)), min(hi[ar], max(f))

            total_hi = sum(hi.values())
            total_lo = sum(lo.values())
            for ar in range(n_areas):
                # every character is somewhere, so this area must absorb whatever the others cannot
                floor = max(lo[ar], n_chars - (total_hi - hi[ar]))
                ceil = min(hi[ar], n_chars - (total_lo - lo[ar]))
                f = feasible(ar, floor, ceil)
                if not f:
                    continue
                if lo[ar] == max(f) and maybe[ar]:
                    for z in maybe[ar]:
                        dom[z] -= {ar}
                        changed = True
                elif lo[ar] + len(maybe[ar]) == min(f) and maybe[ar]:
                    for z in maybe[ar]:
                        if dom[z] != {ar}:
                            dom[z] = {ar}
                            changed = True
            if any(not d for d in dom.values()):
                return None

        # ---- map the conclusion back onto cells --------------------------------------------------
        removed = 0
        who: list[str] = []
        for x in self.chars:
            gone = {k for k in st.cand[x] if s.area_of[k] not in dom[x]}
            if gone:
                st.cand[x] -= gone
                removed += len(gone)
                who.append(x)
        if not removed:
            return None
        return Step(
            "area_projection",
            3,
            f"Working out which area each person can be in — from the area-number "
            f"comparisons, the occupancy parity, and how many each area can hold — rules out "
            f"areas for {', '.join(who)} ({removed} candidate(s) cleared).",
            removed=removed,
        )

    # ------------------------------------------------------------------------- singleton probing
    # Which rules run inside a probe. Deliberately the cheap ones only. Including `t_xblock` made
    # probes strictly stronger and completely impractical: on a 16x16 board one pass over ~800
    # candidates did not finish in five minutes, because xblock is itself O(characters x cells) and
    # runs once per probe. A technique nobody can afford to run is not a technique.
    CHEAP_PROBE = ("t_single", "t_line", "t_exclusive", "t_pairwise", "t_area")

    def _propagate_cheap(self, st: State, limit: int = 200) -> bool:
        """Run only the cheap techniques to a fixpoint. Returns False if the state became dead."""
        fns = [getattr(self, n) for n in self.CHEAP_PROBE]
        for _ in range(limit):
            if st.dead:
                return False
            for fn in fns:
                if fn(st) is not None:
                    break
            else:
                return not st.dead
        return not st.dead

    # Probing costs one propagation per candidate cell, so its cost grows with the board. On a 16x16
    # board with ~3000 live candidates a single `certify()` became minutes, which is unusable inside
    # `carve` (thousands of calls) and stalled a translation run outright. Bounded by candidate count
    # rather than by board size, because that is what the cost actually tracks.
    PROBE_MAX_WIDTH = 400

    def t_probe(self, st: State, budget: int = 2500) -> Step | None:
        """Suppose a person stood here; if that alone breaks the puzzle, they did not.

        This is what a solver does out loud on a hard board — "if she's on that flag then nobody can
        take row 4, so she isn't" — and it is the technique the reference game's expert boards need.
        `xblock` already does the shallowest version of it, testing only whether one assignment
        immediately empties somebody's candidate set. This propagates the cheap rules to a fixpoint
        first, so contradictions several links down the chain are found too.

        Sound: a cell is discarded only when *assuming* it, plus rules that are themselves sound,
        derives that some character has nowhere to stand. No solution can contain such a cell.

        Still not search: one assignment is tried at a time and never nested, so this cannot
        enumerate its way to an answer the way the exact solver does. `budget` caps the probes per
        invocation, and the characters with the fewest candidates are probed first — they are both
        the cheapest to test and the likeliest to yield a contradiction.
        """
        if st.width > self.PROBE_MAX_WIDTH:
            return None  # too wide to probe affordably; see PROBE_MAX_WIDTH
        spent = 0
        order = sorted(
            (x for x in self.chars if len(st.cand[x]) > 1),
            key=lambda x: len(st.cand[x]),
        )
        for x in order:
            dead_cells = set()
            for k in sorted(st.cand[x]):
                if spent >= budget:
                    break
                spent += 1
                trial = st.clone()
                self._place(trial, x, k)
                if not self._propagate_cheap(trial):
                    dead_cells.add(k)
            if dead_cells:
                st.cand[x] -= dead_cells
                where = ", ".join(self._cell(k) for k in sorted(dead_cells)[:4])
                more = (
                    "" if len(dead_cells) <= 4 else f" and {len(dead_cells) - 4} more"
                )
                return Step(
                    "probe",
                    3,
                    f"{x} cannot be at {where}{more}: placing them there leaves someone "
                    f"else with no square at all ({len(dead_cells)} candidate(s) cleared).",
                    removed=len(dead_cells),
                )
            if spent >= budget:
                break
        return None

    def techniques(
        self, *, include_probe: bool = True
    ) -> list[tuple[str, int, Callable[[State], Step | None]]]:
        """Cheapest first. Order *is* the cost model: the engine never reaches for a tier-3
        technique while a tier-1 one still applies, which is what makes the certificate a fair
        proxy for how a person would actually solve it."""
        out = [
            ("single", 1, self.t_single),
            ("line", 1, self.t_line),
            ("exclusive", 1, self.t_exclusive),
            ("relational", 2, self.t_pairwise),
            ("alone", 2, self.t_area),
            ("tagshare", 2, self.t_tag),
            ("last", 4, self.t_last),
            ("naked_subset", 3, self.t_naked_subset),
            ("hidden_subset", 3, self.t_hidden_subset),
            ("xblock", 3, self.t_xblock),
            ("matching", 3, self.t_matching),
            ("area_projection", 3, self.t_area_projection),
            # Counting arguments. Without these the engine simply ignores the general clues, which
            # is what left it unable to crack the reference game's own expert boards: six global
            # predicates were enforced by the CP encoder and invisible to the deduction.
            ("parity", 3, self.t_parity),
            ("counting", 3, self.t_counting),
        ]
        if include_probe:
            out.insert(-2, ("probe", 3, self.t_probe))
        return out

    # ------------------------------------------------------------------------------- solve it
    def run(self, max_steps: int = 4000, *, include_probe: bool = True) -> Certificate:
        st, setup = self.initial()
        steps = [setup]
        order: list[str] = []
        max_width = st.width
        ladder = self.techniques(include_probe=include_probe)

        while not st.solved and len(steps) < max_steps:
            if st.dead:
                break
            progressed = False
            for _name, _tier, fn in ladder:
                step = fn(st)
                if step is not None:
                    steps.append(step)
                    if step.placed:
                        order.append(step.placed[0])
                    max_width = max(max_width, st.width)
                    progressed = True
                    break
            if not progressed:
                break

        # promote any singletons the last technique produced into placements
        for x in self.chars:
            if len(st.cand[x]) == 1 and x not in st.placed:
                k = next(iter(st.cand[x]))
                self._place(st, x, k)
                steps.append(
                    Step("verdict", 1, f"{x} is at {self._cell(k)}.", placed=(x, k))
                )
                order.append(x)

        solved = st.solved and not st.dead
        return Certificate(
            solved=solved,
            steps=steps,
            placed={
                x: next(iter(st.cand[x])) for x in self.chars if len(st.cand[x]) == 1
            },
            place_order=order,
            stuck={x: sorted(c) for x, c in st.cand.items() if len(c) > 1},
            max_width=max_width,
        )


def certify(case: Case, *, include_probe: bool = True) -> Certificate:
    """The canonical certificate for a case: deterministic, cheapest-technique-first."""
    return Deducer(case).run(include_probe=include_probe)
