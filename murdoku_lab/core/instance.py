"""`Case` — the canonical instance record, and the variant registry.

A Case is fully self-describing and JSON round-trippable: scene geometry, cast, clues, the hidden
solution, the murderer, plus (once verified) the certificate the solver produced. The theme is a
*separate* artifact referenced by `theme_id` — a Case is playable, solvable and gradable with no
theme at all.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from typing import Callable, Mapping

from .atoms import Atom, SPECS, area_members, characters_mentioned, holds_atom
from .board import Scene


@dataclass(frozen=True)
class Clue:
    """One presented sentence: a conjunction of atoms about a single holder.

    The reference game attaches 1-2 atoms per character and renders them as one sentence; we keep
    that shape because it is what makes a clue feel like a *statement* rather than a constraint
    dump. `holder == "*"` marks a general clue (a global atom about the whole scene).
    """

    atoms: tuple[Atom, ...]

    def __post_init__(self) -> None:
        if not self.atoms:
            raise ValueError("a clue needs at least one atom")
        hs = {a.holder for a in self.atoms}
        if len(hs) != 1:
            raise ValueError(f"a clue's atoms must share one holder, got {hs}")

    @property
    def holder(self) -> str:
        return self.atoms[0].holder

    def holds(
        self,
        scene: Scene,
        pl: Mapping[str, int],
        tags: Mapping[str, frozenset[int]] | None = None,
    ) -> bool:
        return all(holds_atom(a, scene, pl, tags) for a in self.atoms)

    def to_json(self) -> dict:
        return {"atoms": [a.to_json() for a in self.atoms]}

    @staticmethod
    def from_json(d: dict) -> "Clue":
        return Clue(tuple(Atom.from_json(a) for a in d["atoms"]))


# =============================================================================================
# Murderer rules — the *goal* of the puzzle, per variant. A rule maps a complete placement to the
# answer, or None when the placement makes the answer ill-defined (which the gate then rejects).
# =============================================================================================
def murderer_classic(scene: Scene, pl: Mapping[str, int], victim: str) -> str | None:
    """Faithful rule: the murderer was *alone with* the victim.

    Well-defined iff the victim's area holds exactly two characters — the victim and one suspect.
    """
    others = area_members(scene, pl, scene.area_of[pl[victim]]) - {victim}
    return next(iter(others)) if len(others) == 1 else None


def murderer_open(scene: Scene, pl: Mapping[str, int], victim: str) -> str | None:
    """`victimMode:"open"` — the alone-with rule is dropped.

    This variant treats the victim's own square as the final deduction, so the *answer* is
    the victim's location rather than a suspect. We keep the signature and return the sentinel `"?"`, and the variant declares
    `answer="victim_cell"`; graders read `Case.answer_key`.
    """
    return "?"


MURDERER_RULES: dict[str, Callable[[Scene, Mapping[str, int], str], str | None]] = {
    "classic": murderer_classic,
    "open": murderer_open,
}


# =============================================================================================
# Variants — a registry entry is pure data. A new variant must not require touching solvers.
# =============================================================================================
@dataclass(frozen=True)
class Variant:
    name: str
    sizes: tuple[int, ...]  # square board sides offered
    murderer_rule: str = "classic"
    answer: str = "murderer"  # 'murderer' | 'victim_cell' | 'placement'
    allowed_kinds: frozenset[str] = field(default_factory=lambda: frozenset(SPECS))
    max_atoms_per_clue: int = 2
    max_positional: int = 1  # cap on absolute/offset atoms (their positionalCount)
    max_instant_pins: int = 1  # cap on clues that pin a holder outright
    cast_fills_board: bool = True  # |characters| == board side  => full permutation
    victim_last_k: int = 2  # victim must be among the last k deductions (0=off)
    # Structural character tags the variant puts in play, by NAME — the tag atoms need names, not a
    # count. Was declared as an int and read by nothing; repurposed rather than left as dead weight.
    tags: tuple[str, ...] = ()
    # The props this variant's boards may contain, by NAME. Legacy: it exists because `gen_scene`
    # sampled the global catalogue with `rng.choice`, so registering a new object kind silently
    # changed every board a fixed seed produced. Pinning the palette fixed the symptom.
    #
    # `prop_mix` is the cure. A board declares its own anonymous props — "p0 is a blocking landmark",
    # "p1 is standable" — and a theme supplies the words. There is then no global list to grow, so
    # the failure mode stops existing, and a theme can INVENT props instead of only renaming ours.
    # Set it and the generator ignores `objects`.
    objects: tuple[str, ...] = ()
    prop_mix: tuple[
        tuple[str, int], ...
    ] = ()  # (class, how many distinct props), class in
    # {"blocking", "landmark", "standable"}
    notes: str = ""

    def check_atom_allowed(self, a: Atom) -> None:
        if a.kind not in self.allowed_kinds:
            raise ValueError(f"atom {a.kind!r} not allowed in variant {self.name!r}")


VARIANTS: dict[str, Variant] = {}


def register_variant(v: Variant) -> Variant:
    if v.murderer_rule not in MURDERER_RULES:
        raise ValueError(f"unknown murderer rule {v.murderer_rule!r}")
    unknown = set(v.allowed_kinds) - set(SPECS)
    if unknown:
        raise ValueError(
            f"variant {v.name!r} allows unknown atom kinds: {sorted(unknown)}"
        )
    # A variant that allows a tag predicate but declares no tags can only ever produce atoms that
    # raise at evaluation time. Catch it at registration, not at generation.
    if any(SPECS[k].needs_tags for k in v.allowed_kinds) and not v.tags:
        raise ValueError(
            f"variant {v.name!r} allows tag predicates "
            f"{sorted(k for k in v.allowed_kinds if SPECS[k].needs_tags)} but declares no tags"
        )
    VARIANTS[v.name] = v
    return v


# The reference game's own prop set for small boards, frozen. Anything added to the catalogue later
# (golf props, and whatever comes next) must not disturb these seeds.
_MANOR_OBJECTS = (
    "bed",
    "chair",
    "carpet",
    "car",  # standable
    "table",
    "tv",
    "shelf",
    "plant",
    "tree",
    "flowers",
    "shrub",
    "crate",  # blocking
    "box",
    "register",
    "palm",
    "bear",
    "statue",
    "piano",
    "boulder",
    "barrel",  # landmarks
)
_GOLF_OBJECTS = ("sand", "flag", "tee", "golf_cart", "tree", "water")


# The faithful reproduction of the reference game, and the two axes it already hints at.
_FAITHFUL = frozenset(
    {
        "in_area",
        "in_areas",
        "not_in_area",
        "on",
        "beside",
        "not_beside",
        "in_corner",
        "not_in_corner",
        "in_grid_corner",
        "abs_row",
        "abs_col",
        "only_on",
        "only_beside",
        "alone",
        "area_empty",
        "with",
        "alone_with",
        "row_offset",
        "col_offset",
        "compass",
        "other_beside",
    }
)

register_variant(
    Variant(
        name="classic",
        objects=_MANOR_OBJECTS,
        sizes=(6, 7, 8, 9),
        murderer_rule="classic",
        answer="murderer",
        allowed_kinds=_FAITHFUL,
        notes="Faithful to the reference game: one character per row and column, murderer alone with "
        "the victim, sizes 6-9. Atom set restricted to the kinds their generator emits.",
    )
)

register_variant(
    Variant(
        name="open",
        objects=_MANOR_OBJECTS,
        sizes=(6, 7, 8, 9),
        murderer_rule="open",
        answer="victim_cell",
        allowed_kinds=_FAITHFUL,
        victim_last_k=1,
        notes="Their victimMode='open': no alone-with rule; the answer is the victim's square.",
    )
)

register_variant(
    Variant(
        name="extended",
        objects=_MANOR_OBJECTS,
        sizes=(6, 7, 8, 9, 10, 11, 12),
        murderer_rule="classic",
        answer="murderer",
        # Exclude tag predicates *structurally* rather than by name: listing "tag_in_area" by hand
        # silently admitted the tag kinds added later.
        allowed_kinds=frozenset(k for k, sp in SPECS.items() if not sp.needs_tags),
        max_positional=2,
        notes="Beyond the reference game: larger boards and the full predicate catalogue, "
        "including at_door / on_edge / on_border / diagonal / adjacent_to / not_on / "
        "beside_through_wall / no_empty_area / exactly_one_on.",
    )
)


# The large-board family. Modelled on the reference game's 16x16 "Golf Course":
# numbered areas the clues do arithmetic on, a terrain layer, gendered tags, and extremes instead of
# absolute coordinates — on a board this size naming a column would give the answer away.
_COURSE = frozenset(SPECS) - {
    "abs_row",
    "abs_col",  # a raw coordinate is far too strong at this scale
    "in_grid_corner",  # four cells out of 256: effectively an answer
}

# `anon` is the same game with the prop vocabulary handed to the theme: the board declares how many
# props of each class it has and nothing about what they are. This is the shape we want everywhere;
# `classic` keeps its named palette so its calibrated seeds stay reproducible.
register_variant(
    Variant(
        name="anon",
        sizes=(6, 7, 8, 9, 10, 11, 12),
        murderer_rule="classic",
        answer="murderer",
        allowed_kinds=frozenset(k for k, sp in SPECS.items() if not sp.needs_tags),
        max_positional=2,
        prop_mix=(("blocking", 6), ("landmark", 3), ("standable", 3)),
        notes="Props are anonymous and class-only; the theme names them. No global vocabulary, so "
        "adding a prop kind cannot change what a seed produces.",
    )
)

register_variant(
    Variant(
        name="course",
        objects=_GOLF_OBJECTS,
        sizes=tuple(range(10, 19)),
        murderer_rule="classic",
        answer="murderer",
        allowed_kinds=_COURSE,
        max_positional=2,
        max_atoms_per_clue=3,
        tags=("man", "woman"),
        # With sixteen suspects, demanding the victim be in the final two deductions is a 2-in-16
        # constraint on the deduction order and rejects almost everything. Widen it with the cast.
        victim_last_k=4,
        notes="Large boards (10-18) with the full catalogue: terrain regions, area-number arithmetic, "
        "occupancy parity as a general clue, gendered tags, and compass/extreme anchors. This is "
        "the shape of the reference game's 16x16 Golf Course.",
    )
)


# =============================================================================================
# Case
# =============================================================================================
@dataclass(frozen=True)
class Case:
    scene: Scene
    characters: tuple[str, ...]  # canonical symbols, e.g. ('A','B',...,'V')
    victim: str
    clues: tuple[Clue, ...]
    solution: Mapping[str, int]  # the intended (and unique) placement
    variant: str = "classic"
    tags: Mapping[str, frozenset[int]] = field(default_factory=dict)
    theme_id: str | None = None
    seed: int | None = None
    target_band: str | None = None
    certificate: dict | None = None  # filled by murdoku_lab/solver/logic.py
    meta: dict = field(default_factory=dict)

    # -------------------------------------------------------------------------------- basics
    @property
    def vdef(self) -> Variant:
        return VARIANTS[self.variant]

    @property
    def suspects(self) -> tuple[str, ...]:
        return tuple(x for x in self.characters if x != self.victim)

    @property
    def murderer(self) -> str | None:
        return MURDERER_RULES[self.vdef.murderer_rule](
            self.scene, self.solution, self.victim
        )

    @property
    def answer_key(self):
        """What a solver must produce, per the variant's `answer` axis."""
        kind = self.vdef.answer
        if kind == "murderer":
            return self.murderer
        if kind == "victim_cell":
            return self.solution[self.victim]
        return dict(self.solution)

    @property
    def atoms(self) -> tuple[Atom, ...]:
        return tuple(a for c in self.clues for a in c.atoms)

    # ------------------------------------------------------------------------------ integrity
    def placement_legal(self, pl: Mapping[str, int]) -> bool:
        """Base constraint system only: injective on cells, rows and columns; no blocked cell."""
        if set(pl) != set(self.characters):
            return False
        cells = list(pl.values())
        if len(set(cells)) != len(cells):
            return False
        if any(k in self.scene.info.blocked for k in cells):
            return False
        rows = [self.scene.row(k) for k in cells]
        cols = [self.scene.col(k) for k in cells]
        return len(set(rows)) == len(rows) and len(set(cols)) == len(cols)

    def satisfies(self, pl: Mapping[str, int]) -> bool:
        return self.placement_legal(pl) and all(
            c.holds(self.scene, pl, self.tags) for c in self.clues
        )

    def self_check(self) -> None:
        """Cheap invariants that must hold of any well-formed Case (the gate does the deep ones)."""
        v = self.vdef
        if self.victim not in self.characters:
            raise ValueError("victim not in cast")
        if self.scene.W != self.scene.H:
            raise ValueError("registered variants are square-board only")
        if v.cast_fills_board and len(self.characters) != self.scene.W:
            raise ValueError(
                f"variant {v.name!r} needs |cast| == board side, got "
                f"{len(self.characters)} vs {self.scene.W}"
            )
        for a in self.atoms:
            v.check_atom_allowed(a)
            for x in characters_mentioned(a):
                if x != "*" and x not in self.characters:
                    raise ValueError(f"atom {a.kind} mentions unknown character {x!r}")
            if SPECS[a.kind].needs_tags and not self.tags:
                raise ValueError(f"atom {a.kind} needs tags but the case has none")
        for c in self.clues:
            if len(c.atoms) > v.max_atoms_per_clue:
                raise ValueError(
                    f"clue has {len(c.atoms)} atoms, variant allows "
                    f"{v.max_atoms_per_clue}"
                )
        if not self.satisfies(self.solution):
            raise ValueError(
                "the recorded solution does not satisfy the case's own clues"
            )
        if v.answer == "murderer" and self.murderer is None:
            raise ValueError("murderer is ill-defined in the recorded solution")

    # ------------------------------------------------------------------------------- identity
    def content_hash(self) -> str:
        """Theme-independent identity: two cases with the same math hash the same (I1)."""
        payload = {
            "scene": self.scene.to_json(),
            "characters": list(self.characters),
            "victim": self.victim,
            "variant": self.variant,
            "clues": [c.to_json() for c in self.clues],
            "tags": {x: sorted(t) for x, t in sorted(self.tags.items())},
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]

    def de_themed(self) -> "Case":
        """Strip the theme. Used by the I1 invariance test."""
        return replace(self, theme_id=None)

    # ----------------------------------------------------------------------------------- JSON
    def to_json(self) -> dict:
        return {
            "schema": "murdoku.case/1",
            "id": self.content_hash(),
            "variant": self.variant,
            "scene": self.scene.to_json(),
            "characters": list(self.characters),
            "victim": self.victim,
            "tags": {x: sorted(t) for x, t in sorted(self.tags.items())},
            "clues": [c.to_json() for c in self.clues],
            "solution": {x: int(k) for x, k in sorted(self.solution.items())},
            "answer": self.vdef.answer,
            "answer_key": self.answer_key,
            "theme_id": self.theme_id,
            "seed": self.seed,
            "target_band": self.target_band,
            "certificate": self.certificate,
            "meta": self.meta,
        }

    @staticmethod
    def from_json(d: dict) -> "Case":
        return Case(
            scene=Scene.from_json(d["scene"]),
            characters=tuple(d["characters"]),
            victim=d["victim"],
            clues=tuple(Clue.from_json(c) for c in d["clues"]),
            solution={x: int(k) for x, k in d["solution"].items()},
            variant=d.get("variant", "classic"),
            tags={x: frozenset(t) for x, t in d.get("tags", {}).items()},
            theme_id=d.get("theme_id"),
            seed=d.get("seed"),
            target_band=d.get("target_band"),
            certificate=d.get("certificate"),
            meta=d.get("meta", {}),
        )
