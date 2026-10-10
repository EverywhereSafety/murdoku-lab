"""The clue predicate algebra — a closed, typed, *data-driven* catalogue.

Every clue is an `Atom`: a `kind`, the character it speaks about (`holder`), and positional
`args`. A kind is declared once as an `AtomSpec` in `SPECS`; adding a predicate means adding a
spec, never editing a solver. Each spec carries three things that must agree:

  1. `holds(...)`  — ground truth: does this atom hold of a *complete* placement? The oracle.
  2. `mask(...)`   — the unary candidate set: cells the holder could occupy considering this atom
                     alone. `None` for atoms that are not unary (pair / global).
  3. an NL slot    — `template`, rendered by a Theme. Surface only; never consulted by logic.

`holds` is the single source of truth. The CP-SAT encoder (`murdoku_lab/solver/exact.py`) is a *second*
implementation, and `tests/test_encoding_agreement.py` cross-checks it against `holds` on random
placements. Any disagreement is a bug in the encoder, never in `holds`.

Flags on a spec drive the setter, not the logic: `positional` (absolute coordinates — capped, they
make cases cheap), `pinning` (can collapse a holder to one cell on its own), `relational` (needs a
second character), `needs_tags` (reads structural character tags).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from .board import Scene

# A placement maps character symbol -> flat cell id, and is *complete* when `holds` is called.
Placement = Mapping[str, int]


@dataclass(frozen=True)
class Atom:
    """One clue fragment about `holder`. Immutable and hashable so states can be memoized."""

    kind: str
    holder: str
    args: tuple = ()

    @property
    def spec(self) -> "AtomSpec":
        return SPECS[self.kind]

    def __getitem__(self, name: str):
        return self.args[self.spec.params.index(name)]

    def get(self, name: str, default=None):
        return (
            self.args[self.spec.params.index(name)]
            if name in self.spec.params
            else default
        )

    @property
    def other(self) -> str | None:
        """The second character, for relational atoms."""
        return self["other"] if "other" in self.spec.params else None

    def to_json(self) -> dict:
        return {"kind": self.kind, "holder": self.holder, "args": list(self.args)}

    @staticmethod
    def from_json(d: dict) -> "Atom":
        return Atom(
            ALIASES.get(d["kind"], d["kind"]),
            d["holder"],
            tuple(tuple(a) if isinstance(a, list) else a for a in d.get("args", ())),
        )


@dataclass(frozen=True)
class AtomSpec:
    kind: str
    params: tuple[str, ...]
    arity: str  # 'unary' | 'pair' | 'global'
    template: str  # NL slot; {holder} {other} {area} {obj} {row} {col} {d} {tag}
    holds: Callable[[Atom, Scene, Placement], bool]
    mask: Callable[[Atom, Scene], frozenset[int]] | None = None
    positional: bool = False
    pinning: bool = False
    relational: bool = False
    needs_tags: bool = False
    exclusive: bool = False  # constrains characters *other* than the holder
    tier: int = 1  # reasoning tier this atom typically forces (setter hint)


SPECS: dict[str, AtomSpec] = {}


def _spec(**kw) -> None:
    s = AtomSpec(**kw)
    SPECS[s.kind] = s


def area_members(scene: Scene, pl: Placement, area: int) -> set[str]:
    return {x for x, k in pl.items() if scene.area_of[k] == area}


# =============================================================================================
# UNARY — a predicate on the holder's own cell.  `mask` is exact: the holder's cell must be in it.
# =============================================================================================
_spec(
    kind="in_area",
    params=("area",),
    arity="unary",
    tier=1,
    pinning=False,
    template="{holder}在{area}里。",
    holds=lambda a, s, pl: s.area_of[pl[a.holder]] == a["area"],
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.area_of[k] == a["area"]),
)

_spec(
    kind="in_areas",
    params=("areas",),
    arity="unary",
    tier=2,
    template="{holder}在以下区域之一：{areas}。",
    holds=lambda a, s, pl: s.area_of[pl[a.holder]] in a["areas"],
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.area_of[k] in a["areas"]),
)

_spec(
    kind="not_in_area",
    params=("area",),
    arity="unary",
    tier=2,
    template="{holder}不在{area}里。",
    holds=lambda a, s, pl: s.area_of[pl[a.holder]] != a["area"],
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.area_of[k] != a["area"]),
)

_spec(
    kind="on",
    params=("obj",),
    arity="unary",
    tier=1,
    pinning=True,
    template="{holder}在某{obj}上。",
    holds=lambda a, s, pl: s.obj_of[pl[a.holder]] == a["obj"],
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.obj_of[k] == a["obj"]),
)

_spec(
    kind="not_on",
    params=("obj",),
    arity="unary",
    tier=2,
    template="{holder}不在{obj}上。",
    holds=lambda a, s, pl: s.obj_of[pl[a.holder]] != a["obj"],
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.obj_of[k] != a["obj"]),
)

_spec(
    kind="beside",
    params=("obj",),
    arity="unary",
    tier=1,
    pinning=True,
    template="{holder}在某{obj}旁边。",
    holds=lambda a, s, pl: a["obj"] in s.info.beside[pl[a.holder]],
    mask=lambda a, s: s.cells_beside(a["obj"]),
)

_spec(
    kind="not_beside",
    params=("obj",),
    arity="unary",
    tier=2,
    template="{holder}不在{obj}旁边。",
    holds=lambda a, s, pl: a["obj"] not in s.info.beside[pl[a.holder]],
    mask=lambda a, s: frozenset(s.open_cells - s.cells_beside(a["obj"])),
)

_spec(
    kind="beside_through_wall",
    params=("obj",),
    arity="unary",
    tier=2,
    template="{holder}在某{obj}旁边（隔着一道墙也算）。",
    holds=lambda a, s, pl: a["obj"] in s.info.beside_any[pl[a.holder]],
    mask=lambda a, s: s.cells_beside(a["obj"], same_area=False),
)

# "a corner of their area" was read by a careful solver as a corner of the whole GRID, and the two
# readings differ materially — one board admitted 1 placement under ours and 3 under theirs, another 0.
# Say what a corner is: the cell where two of the area's own walls meet.
_spec(
    kind="in_corner",
    params=(),
    arity="unary",
    tier=1,
    template="{holder}站在所处区域的墙角——该区域两面相邻的墙交汇的格子。（不一定是整个棋盘的角。）",
    holds=lambda a, s, pl: pl[a.holder] in s.info.room_corner,
    mask=lambda a, s: frozenset(s.open_cells & s.info.room_corner),
)

_spec(
    kind="not_in_corner",
    params=(),
    arity="unary",
    tier=2,
    template="{holder}没有站在所处区域的墙角——没有该区域两面相邻的墙交汇的格子。",
    holds=lambda a, s, pl: pl[a.holder] not in s.info.room_corner,
    mask=lambda a, s: frozenset(s.open_cells - s.info.room_corner),
)

_spec(
    kind="in_grid_corner",
    params=(),
    arity="unary",
    tier=1,
    pinning=True,
    template="{holder}站在整个棋盘四个角之一。",
    holds=lambda a, s, pl: pl[a.holder] in s.info.grid_corner,
    mask=lambda a, s: frozenset(s.open_cells & s.info.grid_corner),
)

# These two were named the wrong way round for a reader's intuition — `on_edge` sounded like the grid
# edge while actually meaning "touching any wall", and `on_border` meant the grid boundary. Round-trip
# verification caught a careful reader inverting BOTH of them, masks differing by exactly the 38 cells
# that separate the nested sets. Renamed to say what they mean; the old names still parse (ALIASES).
_spec(
    kind="against_wall",
    params=(),
    arity="unary",
    tier=2,
    template="{holder}所处格子的四面中至少有一面是墙（区域间的墙或棋盘外边界）。",
    holds=lambda a, s, pl: pl[a.holder] in s.info.edge,
    mask=lambda a, s: frozenset(s.open_cells & s.info.edge),
)

_spec(
    kind="on_grid_edge",
    params=(),
    arity="unary",
    tier=2,
    template="{holder}站在棋盘的第一行或最后一行，或第一列或最后一列。",
    holds=lambda a, s, pl: pl[a.holder] in s.info.border,
    mask=lambda a, s: frozenset(s.open_cells & s.info.border),
)

_spec(
    kind="at_door",
    params=(),
    arity="unary",
    tier=1,
    pinning=True,
    template="{holder}在门或窗前面。",
    holds=lambda a, s, pl: pl[a.holder] in s.info.door_cells,
    mask=lambda a, s: frozenset(s.open_cells & s.info.door_cells),
)

_spec(
    kind="abs_row",
    params=("row",),
    arity="unary",
    tier=1,
    positional=True,
    template="{holder}在第{row}行。",
    holds=lambda a, s, pl: s.row(pl[a.holder]) == a["row"],
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.row(k) == a["row"]),
)

_spec(
    kind="abs_col",
    params=("col",),
    arity="unary",
    tier=1,
    positional=True,
    template="{holder}在第{col}列。",
    holds=lambda a, s, pl: s.col(pl[a.holder]) == a["col"],
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.col(k) == a["col"]),
)


# =============================================================================================
# EXCLUSIVE — the holder satisfies something *and no one else does*. High information density.
# =============================================================================================
def _only_on_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    tgt = a["obj"]
    return s.obj_of[pl[a.holder]] == tgt and all(
        s.obj_of[k] != tgt for x, k in pl.items() if x != a.holder
    )


_spec(
    kind="only_on",
    params=("obj",),
    arity="global",
    tier=2,
    pinning=True,
    exclusive=True,
    template="{holder}是唯一在某{obj}上的{cast_noun}。",
    holds=_only_on_holds,
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.obj_of[k] == a["obj"]),
)


def _only_beside_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    tgt = a["obj"]
    return tgt in s.info.beside[pl[a.holder]] and all(
        tgt not in s.info.beside[k] for x, k in pl.items() if x != a.holder
    )


_spec(
    kind="only_beside",
    params=("obj",),
    arity="global",
    tier=2,
    exclusive=True,
    template="{holder}是唯一在某{obj}旁边的{cast_noun}。",
    holds=_only_beside_holds,
    mask=lambda a, s: s.cells_beside(a["obj"]),
)


def _alone_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    return area_members(s, pl, s.area_of[pl[a.holder]]) == {a.holder}


_spec(
    kind="alone",
    params=(),
    arity="global",
    tier=2,
    exclusive=True,
    template="{holder}是独自一只——所在区域里没有别的{cast_noun}，受害者也不在。",
    holds=_alone_holds,
    mask=None,
)


def _area_empty_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    return not area_members(s, pl, a["area"])


_spec(
    kind="area_empty",
    params=("area",),
    arity="global",
    tier=2,
    exclusive=True,
    template="{area}里一只{cast_noun}都没有。",
    holds=_area_empty_holds,
    mask=None,
)


def _no_empty_area_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    return len({s.area_of[k] for k in pl.values()}) == s.n_areas


_spec(
    kind="no_empty_area",
    params=(),
    arity="global",
    tier=3,
    exclusive=True,
    template="每个区域都至少有一只{cast_noun}。",
    holds=_no_empty_area_holds,
    mask=None,
)


def _exactly_one_on_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    return sum(1 for k in pl.values() if s.obj_of[k] == a["obj"]) == 1


_spec(
    kind="exactly_one_on",
    params=("obj",),
    arity="global",
    tier=3,
    exclusive=True,
    template="恰好一只{cast_noun}在某{obj}上。",
    holds=_exactly_one_on_holds,
    mask=None,
)

# =============================================================================================
# PAIR — relates the holder to another character. No unary mask; propagated jointly.
# =============================================================================================
_spec(
    kind="with",
    params=("other",),
    arity="pair",
    tier=2,
    relational=True,
    template="{holder}和{other}在同一个区域。",
    holds=lambda a, s, pl: s.area_of[pl[a.holder]] == s.area_of[pl[a["other"]]],
    mask=None,
)

_spec(
    kind="not_with",
    params=("other",),
    arity="pair",
    tier=2,
    relational=True,
    template="{holder}和{other}不在同一个区域。",
    holds=lambda a, s, pl: s.area_of[pl[a.holder]] != s.area_of[pl[a["other"]]],
    mask=None,
)


def _alone_with_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    ar = s.area_of[pl[a.holder]]
    return s.area_of[pl[a["other"]]] == ar and area_members(s, pl, ar) == {
        a.holder,
        a["other"],
    }


_spec(
    kind="alone_with",
    params=("other",),
    arity="pair",
    tier=2,
    relational=True,
    exclusive=True,
    template="{holder}和{other}单独在一起——那个区域里只有他们两只{cast_noun}。",
    holds=_alone_with_holds,
    mask=None,
)

_spec(
    kind="row_offset",
    params=("other", "d"),
    arity="pair",
    tier=2,
    relational=True,
    positional=True,
    template="{holder}正好在{other}下方 {d} 行。",
    holds=lambda a, s, pl: s.row(pl[a.holder]) - s.row(pl[a["other"]]) == a["d"],
    mask=None,
)

_spec(
    kind="col_offset",
    params=("other", "d"),
    arity="pair",
    tier=2,
    relational=True,
    positional=True,
    template="{holder}正好在{other}右侧 {d} 列。",
    holds=lambda a, s, pl: s.col(pl[a.holder]) - s.col(pl[a["other"]]) == a["d"],
    mask=None,
)


def _sgn(x: int) -> int:
    return (x > 0) - (x < 0)


_spec(
    kind="compass",
    params=("other", "dr", "dc"),
    arity="pair",
    tier=2,
    relational=True,
    positional=True,
    template="{holder}在{other}的{compass_word}方向。",
    holds=lambda a, s, pl: (
        _sgn(s.row(pl[a.holder]) - s.row(pl[a["other"]])) == a["dr"]
        and _sgn(s.col(pl[a.holder]) - s.col(pl[a["other"]])) == a["dc"]
    ),
    mask=None,
)

_spec(
    kind="diagonal",
    params=("other",),
    arity="pair",
    tier=3,
    relational=True,
    template="{holder}和{other}在对角线上对齐。",
    holds=lambda a, s, pl: abs(s.row(pl[a.holder]) - s.row(pl[a["other"]]))
    == abs(s.col(pl[a.holder]) - s.col(pl[a["other"]])),
    mask=None,
)

_spec(
    kind="adjacent_to",
    params=("other",),
    arity="pair",
    tier=2,
    relational=True,
    template="{holder}紧挨着{other}。",
    holds=lambda a, s, pl: pl[a["other"]] in s.neighbours(pl[a.holder]),
    mask=None,
)


# =============================================================================================
# TAGS — structural character attributes (the "a man was in that room" family).
# Tags are assigned by the *math* (part of the Case); the Theme only supplies a word for them,
# so invariant I1 still holds.
# =============================================================================================
def _tag_in_area_holds(
    a: Atom, s: Scene, pl: Placement, tags: Mapping[str, frozenset[int]]
) -> bool:
    ar = s.area_of[pl[a.holder]]
    return any(
        a["tag"] in tags.get(x, frozenset())
        for x in area_members(s, pl, ar)
        if x != a.holder
    )


_spec(
    kind="tag_in_area",
    params=("tag",),
    arity="global",
    tier=2,
    needs_tags=True,
    template="有一只{tag}在{holder}所在区域里。",
    holds=lambda a, s, pl: (_ for _ in ()).throw(
        NotImplementedError("tag_in_area requires tags; call holds_atom(..., tags=...)")
    ),
    mask=None,
)


# =============================================================================================
# TERRAIN — region properties, not objects. Read off the reference game's large boards, where a
# single chair cannot localise anything but "beside a water square" can.
# =============================================================================================
# The words matter here. `sand` and `water` exist BOTH as props and as terrain in our model, so
# "A was on sand" is genuinely ambiguous — round-trip verification flagged all three terrain
# predicates for exactly this. Terrain sentences now say "ground", which a prop sentence never does.
_spec(
    kind="in_terrain",
    params=("ter",),
    arity="unary",
    tier=1,
    template="{holder}站在{ter}地面上。",
    holds=lambda a, s, pl: s.terrain_of[pl[a.holder]] == a["ter"],
    mask=lambda a, s: frozenset(s.info.cells_of_terrain.get(a["ter"], frozenset())),
)

_spec(
    kind="not_in_terrain",
    params=("ter",),
    arity="unary",
    tier=2,
    template="{holder}没有站在{ter}地面上。",
    holds=lambda a, s, pl: s.terrain_of[pl[a.holder]] != a["ter"],
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.terrain_of[k] != a["ter"]),
)

_spec(
    kind="beside_terrain",
    params=("ter",),
    arity="unary",
    tier=1,
    pinning=False,
    template="{holder}在某{ter}地面的格子旁边。",
    holds=lambda a, s, pl: a["ter"] in s.info.beside_terrain[pl[a.holder]],
    mask=lambda a, s: frozenset(
        k for k in s.open_cells if a["ter"] in s.info.beside_terrain[k]
    ),
)


# =============================================================================================
# AREA ORDINALS — arithmetic on the *human* area number. The reference game's larger boards number
# their areas ("HOLE 3") and then reason about the numbers: "a higher hole number than Harry",
# "the hole immediately before Naomi's". `Scene.area_no` is 1-based for exactly this reason.
# =============================================================================================
_spec(
    kind="area_no_parity",
    params=("par",),
    arity="unary",
    tier=2,
    template="{holder}所在区域的编号是{par}（区域按下文从 1 开始编号）。",
    holds=lambda a, s, pl: (s.area_no(pl[a.holder]) % 2)
    == (0 if a["par"] == "even" else 1),
    mask=lambda a, s: frozenset(
        k
        for k in s.open_cells
        if (s.area_no(k) % 2) == (0 if a["par"] == "even" else 1)
    ),
)

_spec(
    kind="area_no_gt",
    params=("other",),
    arity="pair",
    tier=2,
    relational=True,
    template="{holder}在比{other}编号更大的区域。",
    holds=lambda a, s, pl: s.area_no(pl[a.holder]) > s.area_no(pl[a["other"]]),
    mask=None,
)

_spec(
    kind="area_no_lt",
    params=("other",),
    arity="pair",
    tier=2,
    relational=True,
    template="{holder}在比{other}编号更小的区域。",
    holds=lambda a, s, pl: s.area_no(pl[a.holder]) < s.area_no(pl[a["other"]]),
    mask=None,
)

_spec(
    kind="area_no_offset",
    params=("other", "d"),
    arity="pair",
    tier=3,
    relational=True,
    template="{holder}所在区域的编号与{other}相差 {d}。",
    holds=lambda a, s, pl: s.area_no(pl[a.holder]) - s.area_no(pl[a["other"]])
    == a["d"],
    mask=None,
)

_spec(
    kind="not_area_no_offset",
    params=("other", "d"),
    arity="pair",
    tier=2,
    relational=True,
    template="{holder}所在区域的编号与{other}不相差 {d}。",
    holds=lambda a, s, pl: s.area_no(pl[a.holder]) - s.area_no(pl[a["other"]])
    != a["d"],
    mask=None,
)


# =============================================================================================
# EXTREMES — "the northmost row", "not in the first or in the last column". Distinct from
# `abs_row`/`abs_col`: naming an extreme leaks far less than naming a coordinate, which is why the
# reference game uses it freely on boards where an absolute index would give the answer away.
# =============================================================================================
_EXTREME = {
    "north": lambda s, k: s.row(k) == 0,
    "south": lambda s, k: s.row(k) == s.H - 1,
    "west": lambda s, k: s.col(k) == 0,
    "east": lambda s, k: s.col(k) == s.W - 1,
}

_spec(
    kind="on_extreme",
    params=("side",),
    arity="unary",
    tier=1,
    pinning=False,
    template="{holder}在场景最{side}的一行或一列。",
    holds=lambda a, s, pl: _EXTREME[a["side"]](s, pl[a.holder]),
    mask=lambda a, s: frozenset(k for k in s.open_cells if _EXTREME[a["side"]](s, k)),
)

_spec(
    kind="not_on_extreme_axis",
    params=("axis",),
    arity="unary",
    tier=2,
    template="{holder}既不在第一{axis}也不在最后一{axis}。",
    holds=lambda a, s, pl: not _extreme_axis(s, pl[a.holder], a["axis"]),
    mask=lambda a, s: frozenset(
        k for k in s.open_cells if not _extreme_axis(s, k, a["axis"])
    ),
)


def _extreme_axis(s: Scene, k: int, axis: str) -> bool:
    return (
        (s.col(k) in (0, s.W - 1)) if axis == "column" else (s.row(k) in (0, s.H - 1))
    )


# =============================================================================================
# OBJECT x AREA — "the golf tee on either Hole 6, 7 or 8", "the flag for Hole 3, 4 or 5". On a
# large board the same object kind recurs in every area, so naming the kind alone says little;
# qualifying it by a set of areas is what makes it a usable clue.
# =============================================================================================
_spec(
    kind="on_in_areas",
    params=("obj", "areas"),
    arity="unary",
    tier=2,
    pinning=True,
    template="{holder}在以下区域之一的{obj}上。",
    holds=lambda a, s, pl: (
        s.obj_of[pl[a.holder]] == a["obj"] and s.area_of[pl[a.holder]] in a["areas"]
    ),
    mask=lambda a, s: frozenset(
        k
        for k in s.open_cells
        if s.obj_of[k] == a["obj"] and s.area_of[k] in a["areas"]
    ),
)


# =============================================================================================
# TAGS x OBJECT — structural character tags (the reference game uses gender). These read the cast's
# tag map, so they route through `holds_atom`, never `spec.holds`.
# =============================================================================================
def _only_tag_on_holds(
    a: Atom, s: Scene, pl: Placement, tags: Mapping[str, frozenset[int]]
) -> bool:
    """The holder is the only tag-bearer standing on `obj`."""
    tag, obj = a["tag"], a["obj"]
    if s.obj_of[pl[a.holder]] != obj or tag not in tags.get(a.holder, frozenset()):
        return False
    return not any(
        x != a.holder and s.obj_of[k] == obj and tag in tags.get(x, frozenset())
        for x, k in pl.items()
    )


def _tag_in_area_on_holds(
    a: Atom, s: Scene, pl: Placement, tags: Mapping[str, frozenset[int]]
) -> bool:
    """Someone tagged `tag` was on `obj` inside the holder's area (not the holder themselves)."""
    tag, obj, area = a["tag"], a["obj"], s.area_of[pl[a.holder]]
    return any(
        x != a.holder
        and s.area_of[k] == area
        and s.obj_of[k] == obj
        and tag in tags.get(x, frozenset())
        for x, k in pl.items()
    )


_spec(
    kind="only_tag_on",
    params=("tag", "obj"),
    arity="global",
    tier=2,
    needs_tags=True,
    exclusive=True,
    pinning=True,
    template="{holder}是唯一在某{obj}上的{tag}。",
    holds=lambda a, s, pl: (_ for _ in ()).throw(
        NotImplementedError("only_tag_on needs tags; call holds_atom(..., tags=...)")
    ),
    mask=lambda a, s: frozenset(k for k in s.open_cells if s.obj_of[k] == a["obj"]),
)

_spec(
    kind="tag_in_area_on",
    params=("tag", "obj"),
    arity="global",
    tier=2,
    needs_tags=True,
    template="在{holder}所在区域里，有一只{tag}在某{obj}上。",
    holds=lambda a, s, pl: (_ for _ in ()).throw(
        NotImplementedError("tag_in_area_on needs tags; call holds_atom(..., tags=...)")
    ),
    mask=None,
)


def _other_beside_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    area = s.area_of[pl[a.holder]]
    return any(
        x != a.holder and s.area_of[k] == area and a["obj"] in s.info.beside[k]
        for x, k in pl.items()
    )


# The last predicate in the reference generator's own vocabulary that we lacked. Their filter reads
#   !f.some(se => se !== X && areaOf[se] === areaOf[X] && beside[se].has(obj))
# i.e. SOMEONE ELSE in my area was beside the thing — an existential over the other characters, area
# scoped, and untagged. `tag_in_area_on` is the tagged, on-the-object cousin; this is neither.
_spec(
    kind="other_beside",
    params=("obj",),
    arity="global",
    tier=2,
    template="{holder}所在区域里有另一只{cast_noun}在某{obj}旁边。",
    holds=_other_beside_holds,
    mask=None,
)


# =============================================================================================
# GENERAL CLUES — true of the whole board, about nobody in particular. The reference game shows
# these in their own panel above the suspects ("Even-numbered holes have an even number of
# occupants (this includes zero occupants)"). The holder field is carried but never rendered.
# =============================================================================================
def _occupancy_parity_holds(a: Atom, s: Scene, pl: Placement) -> bool:
    want = 0 if a["par"] == "even" else 1
    for area in range(s.n_areas):
        if (area + 1) % 2 != want:
            continue
        if len(area_members(s, pl, area)) % 2 != want:
            return False
    return True


_spec(
    kind="area_occupancy_parity",
    params=("par",),
    arity="global",
    tier=3,
    exclusive=True,
    template="每个编号为{par}的区域里都有偶数只{cast_noun}（0 算偶数）。",
    holds=_occupancy_parity_holds,
    mask=None,
)


# =============================================================================================
# Evaluation front door
# =============================================================================================
def holds_atom(
    a: Atom,
    scene: Scene,
    pl: Placement,
    tags: Mapping[str, frozenset[int]] | None = None,
) -> bool:
    """Ground truth for one atom against a complete placement."""
    spec = SPECS[a.kind]
    if spec.needs_tags:
        ev = _TAG_EVALUATORS.get(a.kind)
        if ev is None:
            raise NotImplementedError(f"no tag evaluator for {a.kind}")
        return ev(a, scene, pl, tags or {})
    return spec.holds(a, scene, pl)


_TAG_EVALUATORS: dict[str, Callable] = {
    "tag_in_area": lambda a, s, pl, t: _tag_in_area_holds(a, s, pl, t),
    "only_tag_on": _only_tag_on_holds,
    "tag_in_area_on": _tag_in_area_on_holds,
}


def unary_mask(a: Atom, scene: Scene) -> frozenset[int] | None:
    spec = SPECS[a.kind]
    return None if spec.mask is None else spec.mask(a, scene)


def characters_mentioned(a: Atom) -> tuple[str, ...]:
    o = a.other
    return (a.holder,) if o is None else (a.holder, o)


# Old kind names, so records and configs written before the rename still load.
ALIASES = {"on_edge": "against_wall", "on_border": "on_grid_edge"}


def canonical_kind(kind: str) -> str:
    return ALIASES.get(kind, kind)


COMPASS_WORDS = {
    (-1, -1): "西北",
    (-1, 0): "北",
    (-1, 1): "东北",
    (0, -1): "西",
    (0, 1): "东",
    (1, -1): "西南",
    (1, 0): "南",
    (1, 1): "东南",
}
