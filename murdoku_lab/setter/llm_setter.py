"""The LLM half of the setter: it writes *themes*, and nothing else.

This is the whole surface area the model is given. It never sees a solution, never chooses
a clue, never touches difficulty. It is handed a shape — how many names, how many rooms, which
objects appear — and asked for words. The case is already finished and verified before a theme is
attached, so theming cannot change formal constraints. Prose still needs its own quality checks:
formal invariance alone does not prove that the presented language is consistent.

Three guarantees make that safe to automate:

  1. **Schema validation.** `Theme.validate(case)` runs before anything is written: every character
     named, enough rooms, no unknown object renamed, names distinct.
  2. **Invariance (I1).** `verify_invariance` re-derives the hash, the solution set, the
     certificate and the band from the de-themed case and requires them bit-identical. A theme that
     changed the puzzle is rejected, not shipped.
  3. **Offline default.** With no API key, `theme_for` returns a bundled theme. Every test and the
     whole benchmark run without network access; the LLM only ever adds variety.

The prompt asks for strict JSON and nothing else. Prose around the JSON is tolerated (the first
balanced object is extracted) because that is the single most common way a model breaks the format,
and a retry is cheaper than a failure.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

from murdoku_lab.core.board import OBJECTS
from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import THEME_DIR, Theme, canonical_theme
from murdoku_lab.solver.difficulty import classify
from murdoku_lab.solver.logic import certify

from .llm_client import LLMClient, LLMUnavailable

# ---------------------------------------------------------------------------------------- prompt
SYSTEM = (
    "You are a set dresser for a logic-puzzle book. You are given the SHAPE of a finished puzzle "
    "and you return only the words that dress it: character names, room names, and nouns for "
    "props. You never invent rules, clues, positions, or an answer — the puzzle is already solved "
    "and locked. Reply with a single JSON object and no other text."
)

TEMPLATE = """Dress one puzzle in the style: {style}

SHAPE
  characters      : {syms}
  the victim is   : {victim}
  public tags    : {public_tags}
  rooms to name   : {n_areas}
  props to name   : {props}
  public layout  : {layout}

Return exactly this JSON object:
{{
  "theme_id": "short_snake_case_id",
  "title": "evocative case title, under 60 characters",
  "blurb": "one sentence of setup, under 140 characters. no spoilers, no accusation.",
  "names": {{ {name_slots} }},
  "pronouns": {{ "SYMBOL": "she" | "he" | "they", ... one per character ... }},
  "areas": [ {n_areas} room names, in order ],
  "objects": {{ "<prop id>": "themed noun", ... every prop listed above ... }},
  "victim_note": "was found dead"
}}

RULES
  - Names must be distinct and must fit the style. One per symbol, all {n} of them.
    Names and pronouns must agree with any supplied public tags; neutral names and "they" are fine.
  - Rooms must be places a person can stand, distinct, and plausible in one building or setting.
  - Use the public layout to make area names and prop labels coherent with one another.
    Keep the supplied area order and prop IDs. Area numbers may be part of the puzzle's
    arithmetic and remain visible after naming. Never infer or add a character's location.
    A prop ID can cover several patches; its label must apply to all occurrences.
  - Each prop is listed with what it physically IS and nothing else. `blocking` means a person
    cannot stand on that square, so name it something bulky and immovable. `standable` means a person
    CAN stand or sit on it, so name it something low or sittable. `landmark` means blocking and
    conspicuous — the sort of thing a witness would mention. Get this wrong and the puzzle reads as
    nonsense: a suspect standing on a grand piano, or hiding behind a doormat.
  - You are inventing these props, not renaming ours. Pick whatever suits the setting.
  - victim_note must be exactly "was found dead". Do not add spatial facts such as alone,
    near an object, or in a room; those would introduce constraints outside the puzzle.
  - Nothing may hint at who the culprit is. The words carry no information.
"""

FALLBACK_STYLES = [
    "a 1930s English country house",
    "a rainy neon city precinct",
    "a research station on an ice shelf",
    "a travelling circus in winter",
    "a university library after hours",
    "a long-haul passenger train",
]


@dataclass
class ThemeResult:
    theme: Theme
    source: str  # "llm" | "bundled" | "canonical"
    style: str = ""
    attempts: int = 0
    errors: tuple[str, ...] = ()
    usage: dict | None = None

    @property
    def from_llm(self) -> bool:
        return self.source == "llm"


# ------------------------------------------------------------------------------------- plumbing
def _shape(case: Case) -> dict:
    """Everything the model is allowed to know. Note the absence of the solution and the clues.

    Props are described by CLASS, not by name: the board says "p3 is a blocking landmark covering 1
    square" and the model decides what that is. That is the whole inversion — the prop vocabulary
    belongs to the theme, so a setting is not limited to the furniture we happened to hardcode, and
    there is no global list whose growth can change what a seed produces.
    """
    syms = list(case.characters)
    s = case.scene
    used = {o for o in s.prop_of if o}
    lines = []
    for pr in sorted(s.props, key=lambda pr: pr.pid):
        if pr.pid not in used:
            continue
        cls = (
            "standable — a person can stand or sit on it"
            if pr.standable
            else (
                "blocking and conspicuous (a landmark)"
                if pr.landmark
                else "blocking — nobody can stand there"
            )
        )
        n_cells = len(pr.cells)
        span = "" if n_cells == 1 else f", covering {n_cells} squares"
        lines.append(f"    {pr.pid}: {cls}{span}")
    return {
        "syms": ", ".join(syms),
        "n": len(syms),
        "victim": case.victim,
        "public_tags": json.dumps(
            {x: sorted(getattr(case, "tags", {}).get(x, ()), key=str) for x in syms},
            ensure_ascii=False,
        ),
        "n_areas": s.n_areas,
        "props": ("\n" + "\n".join(lines)) if lines else " (none)",
        "layout": _public_layout(s),
        "name_slots": ", ".join(f'"{x}": "..."' for x in syms),
    }


def _public_layout(scene) -> str:
    """Give the dresser spatial context, never cast placements, clues or certificates."""
    if not hasattr(scene, "area_of"):
        return "(not supplied)"
    lines = []
    for area in range(scene.n_areas):
        cells = [k for k, a in enumerate(scene.area_of) if a == area]
        props = sorted(
            {scene.prop_of[k] for k in cells if scene.prop_of[k] is not None}
        )
        terrain = sorted({scene.terrain_of[k] for k in cells})
        neighbours = sorted(
            {
                scene.area_of[m] + 1
                for k in cells
                for m in scene.neighbours(k)
                if scene.area_of[m] != area
            }
        )
        lines.append(
            f"Area {area + 1}: {len(cells)} squares; prop IDs {props}; "
            f"terrain {terrain}; neighbouring areas {neighbours}"
        )
    return "\n" + "\n".join(lines)


def _extract_json(text: str) -> dict:
    """First balanced `{...}` in the reply. Models wrap JSON in prose; that is not worth a retry."""
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in reply")
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("unbalanced JSON object in reply")


def _coerce(d: dict, case: Case) -> Theme:
    """Repair what is cheap to repair, then let `validate` reject the rest.

    Deliberately narrow: we drop renames of props that are not on this board and clamp the area
    list to length, because those are formatting slips. We do not invent missing names — a theme
    that forgot a character is a real failure and must go back to the model.
    """
    note = str(d.get("victim_note") or "was found dead").strip()
    if note != "was found dead":
        raise ValueError(
            'victim_note must be neutral: "was found dead"; no extra spatial facts'
        )
    # Accept a name for any prop the BOARD declares (that is the point), and drop the rest.
    on_board = {o for o in case.scene.prop_of if o}
    renames = {
        k: str(v) for k, v in dict(d.get("objects") or {}).items() if k in on_board
    }
    areas = [str(a) for a in (d.get("areas") or [])][: case.scene.n_areas]
    t = Theme(
        theme_id=str(d.get("theme_id") or "llm_theme"),
        title=str(d.get("title") or "An Untitled Case"),
        names={str(k): str(v) for k, v in dict(d.get("names") or {}).items()},
        pronouns={str(k): str(v) for k, v in dict(d.get("pronouns") or {}).items()},
        areas=tuple(areas),
        objects=renames,
        tags={str(k): str(v) for k, v in dict(d.get("tags") or {}).items()},
        victim_note=note,
        blurb=str(d.get("blurb") or ""),
    )
    t.validate(case)
    return t


def verify_invariance(case: Case, theme: Theme) -> None:
    """I1, enforced per theme at set time rather than only in the test suite.

    A theme is a relabelling, so attaching it must leave the mathematics untouched. We re-derive
    from the de-themed case and require identity. This is what makes it safe to accept theme JSON
    from a model without reading it.
    """
    theme.validate(case)
    bare = case.de_themed()
    if bare.content_hash() != case.content_hash():
        raise ValueError("theme changed the content hash")
    a, b = certify(case), certify(bare)
    if (a.depth, a.advanced, a.cost, a.place_order) != (
        b.depth,
        b.advanced,
        b.cost,
        b.place_order,
    ):
        raise ValueError("theme changed the deduction certificate")
    if classify(a) != classify(b):
        raise ValueError("theme changed the difficulty band")


# ------------------------------------------------------------------------------------ front door
def llm_theme(
    case: Case,
    *,
    style: str,
    client: LLMClient | None = None,
    attempts: int = 3,
    temperature: float = 0.9,
    require_complete_props: bool = False,
    asset_config: dict | None = None,
) -> ThemeResult:
    """Ask the model for one theme. Raises `LLMUnavailable` if there is no usable client."""
    cl = client or LLMClient(role="setter")
    if not cl.available():
        raise LLMUnavailable("no API key configured; see config/llm.json")

    sh = _shape(case)
    prompt = TEMPLATE.format(style=style, **sh)
    errors: list[str] = []
    usage = None

    for i in range(1, attempts + 1):
        msgs = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ]
        if errors:
            msgs.append(
                {
                    "role": "user",
                    "content": f"Your previous reply was rejected: {errors[-1]}. "
                    f"Return corrected JSON only.",
                }
            )
        reply = cl.chat(msgs, temperature=temperature)
        usage = cl.usage.to_json()
        try:
            theme = _coerce(_extract_json(reply), case)
            if require_complete_props:
                missing = {o for o in case.scene.prop_of if o} - set(theme.objects)
                if missing:
                    raise ValueError(
                        "objects must preserve EXACT prop IDs as keys; missing: "
                        + ", ".join(sorted(missing))
                    )
            from murdoku_lab.setter.visual_assets import select_assets

            theme = select_assets(case, theme, client=cl, config=asset_config)
            verify_invariance(case, theme)
            return ThemeResult(theme, "llm", style, i, tuple(errors), usage)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{type(e).__name__}: {e}")

    raise LLMUnavailable(f"theme generation failed after {attempts} attempts: {errors}")


def theme_for(
    case: Case,
    *,
    style: str | None = None,
    client: LLMClient | None = None,
    seed: int = 0,
    allow_llm: bool = True,
) -> ThemeResult:
    """The one call the pipeline makes. Never raises: degrades LLM → bundled → canonical.

    Degradation is deliberate. A theme is decoration; a missing API key must not be able to stop a
    verified case from being emitted.
    """
    rng = random.Random(seed)
    style = style or rng.choice(FALLBACK_STYLES)
    errs: list[str] = []

    if allow_llm:
        try:
            return llm_theme(case, style=style, client=client)
        except Exception as e:  # noqa: BLE001
            errs.append(f"{type(e).__name__}: {e}")

    for tid in _bundled_order(case, rng):
        try:
            t = Theme.load(tid)
            verify_invariance(case, t)
            return ThemeResult(t, "bundled", style, 0, tuple(errs))
        except Exception as e:  # noqa: BLE001
            errs.append(f"{tid}: {type(e).__name__}: {e}")

    return ThemeResult(canonical_theme(case), "canonical", style, 0, tuple(errs))


def _bundled_order(case: Case, rng: random.Random) -> list[str]:
    """Shuffle the bundled themes so an offline corpus is still varied, not all one setting."""
    ids = [t for t in Theme.available() if t != "canonical"]
    rng.shuffle(ids)
    return ids


def save_theme(theme: Theme, *, directory: Path | None = None) -> Path:
    """Persist an accepted theme so it joins the bundled set — the LLM's output is a build artefact,
    reviewable in git, not a runtime dependency."""
    d = directory or THEME_DIR
    d.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9_]+", "_", theme.theme_id.lower()).strip("_") or "llm_theme"
    p = d / f"{slug}.json"
    p.write_text(json.dumps(theme.to_json(), ensure_ascii=False, indent=2) + "\n")
    return p
