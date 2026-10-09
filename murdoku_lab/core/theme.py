"""Themes — the LLM's entire surface area.

A Theme maps canonical symbols to words: characters -> names, area ids -> room names, object ids ->
nouns, tag ids -> descriptions. Nothing here can change a solution: `apply` is a relabelling, and
`tests/test_theme_invariance.py` asserts that a themed and de-themed case produce the identical
content hash, solution set, certificate and band (invariant I1).

Themes are *data*, validated on load. An LLM writes them; the schema check and the invariance test
are what make that safe.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .board import OBJECTS
from .instance import Case

THEME_DIR = Path(__file__).resolve().parent.parent / "setter" / "themes"


@dataclass(frozen=True)
class Theme:
    theme_id: str
    title: str
    names: dict[str, str]  # character symbol -> display name
    pronouns: dict[str, str] = field(default_factory=dict)  # symbol -> they/she/he
    areas: tuple[str, ...] = ()  # area id -> room name
    objects: dict[str, str] = field(
        default_factory=dict
    )  # canonical object -> themed noun
    tags: dict[str, str] = field(default_factory=dict)  # tag id (str) -> description
    victim_note: str = "was found dead"
    blurb: str = ""
    assets: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------------------ validation
    def validate(self, case: Case | None = None) -> None:
        if self.assets and case is not None:
            from murdoku_lab.visual.asset_catalog import validate_selection

            validate_selection(case, self.assets)
        if not self.theme_id or not self.title:
            raise ValueError("theme needs an id and a title")
        # A theme may name any prop the BOARD declares, which is the point of board-local props: the
        # vocabulary is the theme's, not ours. Only a rename of something neither the board nor the
        # catalogue knows is an error, and that is checked against the case when one is supplied.
        if case is not None:
            known = set(case.scene.prop_by_id) | set(OBJECTS)
            unknown = [o for o in self.objects if o not in known]
            if unknown:
                raise ValueError(
                    f"theme names props this board does not have: {sorted(unknown)}"
                )
        if case is not None:
            missing = set(case.characters) - set(self.names)
            if missing:
                raise ValueError(
                    f"theme {self.theme_id!r} has no name for {sorted(missing)}"
                )
            if len(self.areas) < case.scene.n_areas:
                raise ValueError(
                    f"theme {self.theme_id!r} names {len(self.areas)} areas, scene has "
                    f"{case.scene.n_areas}"
                )
            if len(set(self.names[x] for x in case.characters)) != len(case.characters):
                raise ValueError("character names must be distinct within a case")

    # ------------------------------------------------------------------------------- accessors
    def name(self, sym: str) -> str:
        return self.names.get(sym, sym)

    def area(self, aid: int) -> str:
        return self.areas[aid] if aid < len(self.areas) else f"Area {aid + 1}"

    def obj(self, o: str | None) -> str:
        return "" if o is None else self.objects.get(o, o)

    def tag(self, t) -> str:
        """A theme's word for a structural tag, else the tag itself.

        The fallback is the raw tag, not a `tag {t}` placeholder: tags are now words like "man" and
        "woman", so the placeholder rendered clues as "the only tag man on a chair".
        """
        return self.tags.get(str(t), str(t))

    # ------------------------------------------------------------------------------------ JSON
    def to_json(self) -> dict:
        return {
            "theme_id": self.theme_id,
            "title": self.title,
            "names": self.names,
            "pronouns": self.pronouns,
            "areas": list(self.areas),
            "objects": self.objects,
            "tags": self.tags,
            "victim_note": self.victim_note,
            "blurb": self.blurb,
            "assets": self.assets,
        }

    @staticmethod
    def from_json(d: dict) -> "Theme":
        return Theme(
            theme_id=d["theme_id"],
            title=d["title"],
            names=dict(d["names"]),
            pronouns=dict(d.get("pronouns", {})),
            areas=tuple(d.get("areas", ())),
            objects=dict(d.get("objects", {})),
            tags=dict(d.get("tags", {})),
            victim_note=d.get("victim_note", "was found dead"),
            blurb=d.get("blurb", ""),
            assets=dict(d.get("assets", {})),
        )

    @staticmethod
    def load(theme_id: str) -> "Theme":
        return Theme.from_json(json.loads((THEME_DIR / f"{theme_id}.json").read_text()))

    @staticmethod
    def available() -> list[str]:
        return sorted(p.stem for p in THEME_DIR.glob("*.json"))


def canonical_theme(case: Case) -> Theme:
    """The identity theme: every symbol stands for itself. The de-themed reference rendering."""
    # The title must not carry the content hash: it is internal metadata, and the canonical theme is
    # what the solver-facing statement uses when no theme is attached. A leak audit caught it.
    return Theme(
        theme_id="canonical",
        title="An Untitled Case",
        names={x: x for x in case.characters},
        areas=tuple(f"Area {i + 1}" for i in range(case.scene.n_areas)),
        victim_note="was found dead",
    )
