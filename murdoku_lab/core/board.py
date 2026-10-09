"""Scene geometry — the *field*, shared by every variant and every theme.

A Scene is pure structure: a W x H grid, a partition into areas, an object per cell, and
door/window links. Names live in a Theme and never reach this module: areas and objects are
referred to by integer id / canonical symbol here, so `Scene` is exactly the object whose
solution set must be theme-invariant (invariant I1).

Derived per-cell facts (`CellInfo`) are computed once and cached, because every atom's
semantics and every propagator reads them in a hot loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property


# ---------------------------------------------------------------------------------------------
# Objects. `occupiable` is load-bearing: it is the one physical fact that prunes cells.
# Faithful to the reference game: table/tv/shelf/plant/tree/flowers block a square; bed, chair,
# carpet and car do not.
# ---------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ObjectKind:
    name: str
    occupiable: bool
    landmark: bool = (
        False  # visually salient => a good `beside` anchor; cosmetic weight only
    )


_OBJ = [
    # occupiable furniture — a person can stand/sit on it
    ObjectKind("bed", True),
    ObjectKind("chair", True),
    ObjectKind("carpet", True),
    ObjectKind("car", True),
    # blockers
    ObjectKind("table", False),
    ObjectKind("tv", False),
    ObjectKind("shelf", False),
    ObjectKind("plant", False),
    ObjectKind("tree", False),
    ObjectKind("flowers", False),
    ObjectKind("shrub", False),
    ObjectKind("crate", False),
    ObjectKind("box", False),
    ObjectKind("register", False),
    ObjectKind("palm", False),
    ObjectKind("bear", False),
    # Golf-course props, taken from the reference bundle's own object catalogue, which encodes
    # `c(id, "Name", occupiable, svg)` — so these flags are theirs, not a guess:
    #   24|Sand|1|obj_sand   58|Flag|1|obj_hole   78|Tee|1|obj_tee   71|Golf Cart|1   72|Water|0
    # Note what this settles: their large boards model sand and water as OBJECTS with an occupiable
    # flag, not as a terrain layer. "beside a water square" is `beside(water)` and "within a sand
    # pit" is `on(sand)` — both already in the algebra. The fairway/rough green shading in their UI
    # is decoration and no clue ever refers to it.
    ObjectKind("sand", True),
    ObjectKind("flag", True),
    ObjectKind("tee", True),
    ObjectKind("golf_cart", True),
    ObjectKind("water", False),
    # blocking landmarks — heavy, unmistakable, ideal anchors
    ObjectKind("statue", False, landmark=True),
    ObjectKind("piano", False, landmark=True),
    ObjectKind("boulder", False, landmark=True),
    ObjectKind("barrel", False, landmark=True),
    # `void` is not an object but an unusable cell (courtyard hole, water, wall block)
    ObjectKind("void", False),
]
OBJECTS: dict[str, ObjectKind] = {o.name: o for o in _OBJ}


# ---------------------------------------------------------------------------------------------
# Terrain. A *region* property of a cell, orthogonal to the object standing on it, read off the
# reference game's larger boards: "she was beside a water square", "she was within a sand pit"
# Terrain covers many contiguous cells, so it makes a good anchor on a
# board too big for single-object landmarks to localise anything.
#
# `standable=False` terrain removes the cell exactly like a blocking object does — a water hazard
# is not somewhere a suspect stood.
# ---------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class TerrainKind:
    name: str
    standable: bool


_TERRAIN = [
    TerrainKind("floor", True),  # the default: unremarkable ground
    TerrainKind("fairway", True),  # mown grass
    TerrainKind("rough", True),  # long grass
    TerrainKind(
        "sand", True
    ),  # bunker — you can stand in it, hence a usable clue anchor
    TerrainKind("water", False),  # hazard — nobody stood here
    TerrainKind("tile", True),
    TerrainKind("rug", True),
]
TERRAINS: dict[str, TerrainKind] = {t.name: t for t in _TERRAIN}
STANDABLE_TERRAIN = tuple(t.name for t in _TERRAIN if t.standable)
BLOCKING_TERRAIN = tuple(t.name for t in _TERRAIN if not t.standable)
DEFAULT_TERRAIN = "floor"
OCCUPIABLE_OBJECTS = tuple(o.name for o in _OBJ if o.occupiable)
BLOCKING_OBJECTS = tuple(o.name for o in _OBJ if not o.occupiable)
LANDMARKS = tuple(o.name for o in _OBJ if o.landmark)


def register_object(name: str, occupiable: bool, landmark: bool = False) -> ObjectKind:
    """Add a prop kind at runtime, for importing boards authored elsewhere.

    The reference game ships 144 props and we model 26 by hand; the importer registers the rest so a
    published board can be rebuilt without every clue predicate having to know about mammoths. Safe
    to call repeatedly, and a second call that *disagrees* about standability is an error rather than
    a silent overwrite — that flag decides whether a square is playable.

    This cannot disturb generation: variants draw props from their own pinned palette
    (`Variant.objects`), precisely so that registering a kind cannot change what a seed produces.
    """
    global OCCUPIABLE_OBJECTS, BLOCKING_OBJECTS, LANDMARKS
    existing = OBJECTS.get(name)
    if existing is not None:
        if existing.occupiable != occupiable:
            raise ValueError(
                f"object {name!r} already registered with occupiable={existing.occupiable}, "
                f"refusing to redefine it as {occupiable}"
            )
        return existing
    kind = ObjectKind(name, occupiable, landmark)
    OBJECTS[name] = kind
    if occupiable:
        OCCUPIABLE_OBJECTS = OCCUPIABLE_OBJECTS + (name,)
    else:
        BLOCKING_OBJECTS = BLOCKING_OBJECTS + (name,)
    if landmark:
        LANDMARKS = LANDMARKS + (name,)
    return kind


# ---------------------------------------------------------------------------------------------
# Props. A prop is a THING ON THIS BOARD, not a member of a global vocabulary.
#
# The mathematics knows two facts about a prop: whether a person can stand on it, and which cells it
# covers. Its NAME is theme data — "p2" is a blocking landmark, and whether that reads as a grand
# piano or a giant sugar cube is the theme's business. That inversion is the point:
#
#   * the global catalogue used to live in this file, so ADDING a prop kind changed what
#     `rng.choice(BLOCKING_OBJECTS)` returned and silently altered every board a fixed seed produced.
#     Registering the golf props collapsed all four difficulty bands to `easy`. With the vocabulary
#     owned by the board there is no global list to grow, so that failure mode stops existing.
#   * a theme can INVENT props rather than only rename ours, so it is not limited to the ~26 pieces
#     of furniture we happened to hardcode.
#
# `cells` is a footprint, and in generated boards today it is one cell per prop of a kind. It is a
# set rather than a single cell because that is the whole difference between this design and
# per-instance props: a carpet covers several squares, and `on`/`beside` as defined below already
# mean the right thing for a footprint of any size, so that change will be semantics-free.
@dataclass(frozen=True)
class Prop:
    pid: str  # board-local id; the theme supplies the display name
    standable: bool  # the one physical fact that prunes cells
    cells: frozenset[int]  # footprint
    landmark: bool = False  # salient enough to anchor a clue; cosmetic weight

    def __post_init__(self) -> None:
        if not self.pid:
            raise ValueError("a prop needs an id")
        if not self.cells:
            raise ValueError(f"prop {self.pid!r} covers no cells")


@dataclass(frozen=True)
class CellInfo:
    """Per-cell derived geometry. Indices are flat cell ids `k = r * W + c`."""

    blocked: frozenset[int]  # non-occupiable: nobody may stand here
    beside: tuple[frozenset[str], ...]  # objects 4-adjacent to k *within k's own area*
    beside_any: tuple[
        frozenset[str], ...
    ]  # objects 4-adjacent to k, ignoring area walls
    room_corner: frozenset[int]  # a vertical wall AND a horizontal wall meet at k
    grid_corner: frozenset[int]  # the 4 corners of the whole grid
    edge: frozenset[int]  # k touches at least one wall (area or outer)
    border: frozenset[int]  # k lies on the outer grid boundary
    door_cells: frozenset[int]  # k is one of the two cells a door/window joins
    walls: tuple[int, ...]  # number of walls touching k (0..4)
    beside_terrain: tuple[
        frozenset[str], ...
    ]  # terrains 4-adjacent to k, within k's own area
    beside_terrain_any: tuple[frozenset[str], ...]  # ... ignoring area walls
    cells_of_terrain: dict[str, frozenset[int]]  # standable cells per terrain name


@dataclass(frozen=True)
class Scene:
    """The crime scene: geometry only, no names, no cast.

    `area_of[k]` is the area id of cell k; areas must be a partition of all cells into
    non-empty, 4-connected regions (validated).  `obj_of[k]` is an object name or None.
    `doors` are unordered pairs of 4-adjacent cells in *different* areas, i.e. a passage;
    the reference game's "in front (of)" predicate means "one of the two cells a door joins".
    """

    W: int
    H: int
    area_of: tuple[int, ...]
    obj_of: tuple[str | None, ...]
    doors: frozenset[frozenset[int]] = field(default_factory=frozenset)
    # Defaulted to all-`floor` so every existing Scene, test and record stays valid: a board with
    # no terrain layer behaves exactly as before.
    terrain_of: tuple[str, ...] = ()
    # Areas are 4-connected by default, and our generator only ever makes connected ones. The
    # reference game's hand-authored boards are not all like that: three of its published puzzles
    # give one area two separate patches. Nothing in the rules requires contiguity — "in the same
    # area" is set membership — so the check is a quality guard for generated boards, not a law, and
    # imported boards are allowed to opt out. Kept explicit rather than dropped, so a generator bug
    # that produces a scattered room still fails loudly.
    allow_disconnected_areas: bool = False
    # The board's own prop vocabulary. Left empty and it is derived from `obj_of` against the
    # convenience catalogue below, so every existing construction site keeps working; pass it and
    # `obj_of` is derived from the footprints instead, and the catalogue is not consulted at all.
    #
    # Declared LAST on purpose: several callers construct a Scene positionally, and inserting a field
    # in the middle silently bound `doors` to `props`.
    props: tuple[Prop, ...] = ()

    # ------------------------------------------------------------------ construction helpers
    def __post_init__(self) -> None:
        n = self.W * self.H
        if not (3 <= self.W <= 24 and 3 <= self.H <= 24):
            raise ValueError(
                f"grid out of spec: {self.W}x{self.H} (each side must be 3..24)"
            )
        if self.props:
            # props are authoritative: rebuild obj_of from the footprints
            seen: dict[int, str] = {}
            for pr in self.props:
                for k in pr.cells:
                    if not (0 <= k < n):
                        raise ValueError(
                            f"prop {pr.pid!r} covers cell {k} outside the grid"
                        )
                    if k in seen:
                        raise ValueError(
                            f"cell {k} is covered by both {seen[k]!r} and {pr.pid!r}"
                        )
                    seen[k] = pr.pid
            object.__setattr__(self, "obj_of", tuple(seen.get(k) for k in range(n)))
        elif self.obj_of:
            # legacy input: one prop per distinct catalogue object, footprint = all its cells
            by: dict[str, set[int]] = {}
            for k, o in enumerate(self.obj_of):
                if o is not None:
                    by.setdefault(o, set()).add(k)
            object.__setattr__(
                self,
                "props",
                tuple(
                    Prop(
                        pid=o,
                        standable=OBJECTS[o].occupiable if o in OBJECTS else False,
                        cells=frozenset(ks),
                        landmark=o in OBJECTS and OBJECTS[o].landmark,
                    )
                    for o, ks in sorted(by.items())
                ),
            )
        if len(self.area_of) != n or len(self.obj_of) != n:
            raise ValueError("area_of / obj_of must have W*H entries")
        if not self.terrain_of:
            object.__setattr__(self, "terrain_of", (DEFAULT_TERRAIN,) * n)
        if len(self.terrain_of) != n:
            raise ValueError("terrain_of must have W*H entries")
        for t in self.terrain_of:
            if t not in TERRAINS:
                raise ValueError(f"unknown terrain {t!r}")
        # A cell's prop must be one the BOARD declares. Membership of the global catalogue is no
        # longer required — that requirement is exactly what made the vocabulary global, and a pid
        # like "p0" is meant not to be in it. Legacy boards with no `props` are still checked against
        # the catalogue, since that is where their standability comes from.
        known = self.prop_by_id if self.props else None
        for o in self.obj_of:
            if o is None:
                continue
            if known is not None:
                if o not in known:
                    raise ValueError(
                        f"cell holds prop {o!r}, which this board does not declare"
                    )
            elif o not in OBJECTS:
                raise ValueError(f"unknown object {o!r} and no props declared")
        if set(self.area_of) != set(range(self.n_areas)):
            raise ValueError("area ids must be contiguous 0..n_areas-1")
        if not self.allow_disconnected_areas:
            for a in range(self.n_areas):
                if not self._connected(self.cells_of_area(a)):
                    raise ValueError(
                        f"area {a} is not 4-connected. Generated boards must be; pass "
                        f"allow_disconnected_areas=True to import a hand-authored one."
                    )
        for d in self.doors:
            if len(d) != 2:
                raise ValueError("a door joins exactly two cells")
            u, v = tuple(d)
            if v not in self.neighbours(u):
                raise ValueError("a door joins 4-adjacent cells")

    # ------------------------------------------------------------------------------ geometry
    @property
    def n_cells(self) -> int:
        return self.W * self.H

    @cached_property
    def n_areas(self) -> int:
        return max(self.area_of) + 1

    def rc(self, k: int) -> tuple[int, int]:
        return divmod(k, self.W)

    def k(self, r: int, c: int) -> int:
        return r * self.W + c

    def row(self, k: int) -> int:
        return k // self.W

    def col(self, k: int) -> int:
        return k % self.W

    def neighbours(self, k: int) -> tuple[int, ...]:
        r, c = self.rc(k)
        out = []
        if r > 0:
            out.append(k - self.W)
        if r < self.H - 1:
            out.append(k + self.W)
        if c > 0:
            out.append(k - 1)
        if c < self.W - 1:
            out.append(k + 1)
        return tuple(out)

    @cached_property
    def area_components(self) -> dict[int, int]:
        """How many separate patches each area is in. 1 for every generated board."""
        out = {}
        for a in range(self.n_areas):
            cells = set(self.cells_of_area(a))
            n = 0
            while cells:
                n += 1
                stack = [next(iter(cells))]
                cells.discard(stack[0])
                while stack:
                    k = stack.pop()
                    for m in self.neighbours(k):
                        if m in cells:
                            cells.discard(m)
                            stack.append(m)
            out[a] = n
        return out

    @cached_property
    def prop_by_id(self) -> dict[str, Prop]:
        return {p.pid: p for p in self.props}

    @property
    def prop_of(self) -> tuple[str | None, ...]:
        """Per-cell prop id. The same tuple as `obj_of`; the name says what it now holds."""
        return self.obj_of

    def prop(self, pid: str) -> Prop:
        return self.prop_by_id[pid]

    def prop_standable(self, pid: str | None) -> bool:
        if pid is None:
            return True
        pr = self.prop_by_id.get(pid)
        if pr is not None:
            return pr.standable
        return OBJECTS[pid].occupiable if pid in OBJECTS else False

    def area_no(self, k: int) -> int:
        """The *human* number of the area holding k, 1-based.

        Clue predicates do arithmetic on this — "a higher hole number than Harry", "the hole
        immediately before Naomi's" — so the 1-based numbering is part of the model, not a
        rendering detail. Area ids stay 0-based internally.
        """
        return self.area_of[k] + 1

    def standable(self, k: int) -> bool:
        return (
            self.prop_standable(self.obj_of[k])
            and TERRAINS[self.terrain_of[k]].standable
        )

    def cells_of_area(self, a: int) -> tuple[int, ...]:
        return tuple(k for k in range(self.n_cells) if self.area_of[k] == a)

    def _connected(self, cells: tuple[int, ...]) -> bool:
        if not cells:
            return False
        want, seen, stack = set(cells), {cells[0]}, [cells[0]]
        while stack:
            k = stack.pop()
            for m in self.neighbours(k):
                if m in want and m not in seen:
                    seen.add(m)
                    stack.append(m)
        return seen == want

    def cells_with_object(self, obj: str) -> frozenset[int]:
        return frozenset(k for k in range(self.n_cells) if self.obj_of[k] == obj)

    # -------------------------------------------------------------------------- derived facts
    @cached_property
    def info(self) -> CellInfo:
        n, W, H = self.n_cells, self.W, self.H
        blocked, beside, beside_any = set(), [], []
        bter, bter_any = [], []
        per_terrain: dict[str, set[int]] = {t: set() for t in TERRAINS}
        rcorner, gcorner, edge, border, walls = set(), set(), set(), set(), []
        door_cells = frozenset(k for d in self.doors for k in d)

        for k in range(n):
            o = self.obj_of[k]
            if o is not None and not self.prop_standable(o):
                blocked.add(k)
            if not TERRAINS[self.terrain_of[k]].standable:
                blocked.add(k)  # a water hazard removes the cell exactly like a blocker
            r, c = self.rc(k)
            same, anyb = set(), set()
            tsame, tany = set(), set()
            for m in self.neighbours(k):
                mo, mt = self.obj_of[m], self.terrain_of[m]
                tany.add(mt)
                if self.area_of[m] == self.area_of[k]:
                    tsame.add(mt)
                if mo is None:
                    continue
                anyb.add(mo)
                if self.area_of[m] == self.area_of[k]:
                    same.add(mo)
            beside.append(frozenset(same))
            beside_any.append(frozenset(anyb))
            bter.append(frozenset(tsame))
            bter_any.append(frozenset(tany))

            # a "wall" is the outer grid boundary or a boundary to a different area
            up = r == 0 or self.area_of[k - W] != self.area_of[k]
            down = r == H - 1 or self.area_of[k + W] != self.area_of[k]
            left = c == 0 or self.area_of[k - 1] != self.area_of[k]
            right = c == W - 1 or self.area_of[k + 1] != self.area_of[k]
            nw = sum((up, down, left, right))
            walls.append(nw)
            if nw:
                edge.add(k)
            if (up or down) and (left or right):
                rcorner.add(k)  # two walls meet: a corner of the area
            if r in (0, H - 1) or c in (0, W - 1):
                border.add(k)
            if r in (0, H - 1) and c in (0, W - 1):
                gcorner.add(k)

        # Only standable cells are recorded per terrain: an atom saying "she was in the sand" can
        # only ever be satisfied somewhere a person could actually be.
        for k in range(n):
            if k not in blocked:
                per_terrain[self.terrain_of[k]].add(k)

        return CellInfo(
            blocked=frozenset(blocked),
            beside=tuple(beside),
            beside_any=tuple(beside_any),
            room_corner=frozenset(rcorner),
            grid_corner=frozenset(gcorner),
            edge=frozenset(edge),
            border=frozenset(border),
            door_cells=door_cells,
            walls=tuple(walls),
            beside_terrain=tuple(bter),
            beside_terrain_any=tuple(bter_any),
            cells_of_terrain={t: frozenset(v) for t, v in per_terrain.items()},
        )

    @cached_property
    def open_cells(self) -> frozenset[int]:
        """Cells a character may stand on at all (before any clue)."""
        return frozenset(range(self.n_cells)) - self.info.blocked

    def cells_beside(self, obj: str, *, same_area: bool = True) -> frozenset[int]:
        b = self.info.beside if same_area else self.info.beside_any
        return frozenset(k for k in self.open_cells if obj in b[k])

    # ---------------------------------------------------------------------------- feasibility
    def max_characters(self) -> int:
        """Upper bound on cast size: a maximum matching of open cells across rows/columns.

        Placement is injective on rows *and* columns, so a cast of size m fits only if the
        bipartite graph rows-vs-columns restricted to open cells has a matching of size m.
        """
        import networkx as nx

        g = nx.Graph()
        for k in self.open_cells:
            r, c = self.rc(k)
            g.add_edge(("r", r), ("c", c))
        if not g:
            return 0
        return len(nx.max_weight_matching(g, maxcardinality=True))

    def to_json(self) -> dict:
        return {
            "W": self.W,
            "H": self.H,
            "area_of": list(self.area_of),
            "obj_of": list(self.obj_of),
            "props": [
                {
                    "pid": p.pid,
                    "standable": p.standable,
                    "cells": sorted(p.cells),
                    "landmark": p.landmark,
                }
                for p in sorted(self.props, key=lambda p: p.pid)
            ],
            "terrain_of": list(self.terrain_of),
            "allow_disconnected_areas": self.allow_disconnected_areas,
            "doors": sorted(sorted(d) for d in self.doors),
        }

    @staticmethod
    def from_json(d: dict) -> "Scene":
        return Scene(
            W=int(d["W"]),
            H=int(d["H"]),
            area_of=tuple(int(a) for a in d["area_of"]),
            obj_of=tuple(d["obj_of"]),
            props=tuple(
                Prop(
                    pid=r["pid"],
                    standable=bool(r["standable"]),
                    cells=frozenset(r["cells"]),
                    landmark=bool(r.get("landmark", False)),
                )
                for r in d.get("props", ())
            ),
            terrain_of=tuple(d.get("terrain_of", ())),
            allow_disconnected_areas=bool(d.get("allow_disconnected_areas", False)),
            doors=frozenset(frozenset(p) for p in d.get("doors", [])),
        )

    def ascii(self, placement: dict[str, int] | None = None) -> str:
        """Deliberately minimal rendering (visualization stays thin, per the brief).

        Props show as their INDEX, not a name prefix: "p10"[:2] == "p1", so truncating collided two
        different props on the map. Uppercase blocks, lowercase is standable. Only this debug view is
        affected — the solver-facing map uses theme names.
        """
        placement = placement or {}
        at = {k: sym for sym, k in placement.items()}
        w = max(2, max((len(v) for v in at.values()), default=1))
        idx = {
            pr.pid: i for i, pr in enumerate(sorted(self.props, key=lambda pr: pr.pid))
        }
        out = []
        for r in range(self.H):
            cells = []
            for c in range(self.W):
                k = self.k(r, c)
                pid = self.obj_of[k]
                if k in at:
                    tok = at[k]
                elif pid is not None:
                    tag = f"{idx[pid]:02d}" if pid in idx else pid[:2]
                    tok = tag.upper() if not self.prop_standable(pid) else tag.lower()
                else:
                    tok = "."
                cells.append(tok.rjust(w))
            out.append(" ".join(cells))
            if r < self.H - 1:
                seg = []
                for c in range(self.W):
                    a1, a2 = self.area_of[self.k(r, c)], self.area_of[self.k(r + 1, c)]
                    seg.append(("-" * w) if a1 != a2 else (" " * w))
                out.append(" ".join(seg))
        return "\n".join(out)
