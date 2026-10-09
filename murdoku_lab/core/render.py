"""Render formal cases and themes as public text observations."""

from __future__ import annotations

import re

from murdoku_lab.core.atoms import COMPASS_WORDS, SPECS, Atom
from murdoku_lab.core.board import DEFAULT_TERRAIN, OBJECTS, TERRAINS
from murdoku_lab.core.instance import Case, Clue
from murdoku_lab.core.theme import Theme, canonical_theme


def cell_label(case: Case, k: int) -> str:
    r, c = case.scene.rc(k)
    return f"{chr(ord('a') + c)}{r + 1}"


def parse_cell(case: Case, s: str) -> int | None:
    s = s.strip().lower()
    if len(s) < 2 or not s[0].isalpha():
        return None
    c = ord(s[0]) - ord("a")
    try:
        r = int(s[1:]) - 1
    except ValueError:
        return None
    if not (0 <= c < case.scene.W and 0 <= r < case.scene.H):
        return None
    return case.scene.k(r, c)


# =============================================================================================
# Clue text
# =============================================================================================
def _area_phrase(label: str) -> str:
    parts = label.split()
    numbered = (
        len(parts) == 2
        and parts[0].lower() in {"area", "hole", "room", "cell"}
        and (any(c.isdigit() for c in parts[1]) or len(parts[1]) == 1)
    )
    return label if numbered or label.lower().startswith("the ") else "the " + label


def render_atom(a: Atom, case: Case, th: Theme) -> str:
    s, spec = case.scene, SPECS[a.kind]
    who, other = th.name(a.holder), th.name(a.other) if a.other else ""

    # Short witness statements; shared geometric definitions live in TERMS below.
    # Keep every subject explicit: existential "someone else" clauses must not
    # inherit the holder's following predicate when a compound clue is rendered.
    if a.kind == "in_corner":
        return f"{who} was in a corner of their area."
    if a.kind == "not_in_corner":
        return f"{who} was not in a corner of their area."
    if a.kind == "alone":
        return f"{who} was the only person in their area."
    if a.kind == "in_area":
        return f"{who} was in {_area_phrase(th.area(a['area']))}."
    if a.kind == "not_in_area":
        return f"{who} was not in {_area_phrase(th.area(a['area']))}."
    if a.kind == "area_empty":
        return f"Nobody was in {_area_phrase(th.area(a['area']))}."
    if a.kind == "area_no_parity":
        return f"{who} was in an {a['par']}-numbered area."
    if a.kind == "on_grid_edge":
        return f"{who} stood on the outer border of the grid."
    if a.kind == "beside_terrain":
        return f"{who} was beside a {th.obj(a['ter'])} terrain square."
    if a.kind == "beside" and a["obj"] == "flowers" and th.obj("flowers") == "flowers":
        return f"{who} was beside the flowers."

    if a.kind in ("row_offset", "col_offset"):
        # "X was exactly 3 rows below Y" reads in English as implying the SAME COLUMN, and a solver
        # reading it that way found the puzzle unsolvable — the true answer has their columns
        # differing, so the same-column reading admits zero placements. The atom constrains only the
        # row difference, so the sentence has to say that outright.
        d = a["d"]
        n = abs(d)
        if a.kind == "row_offset":
            word = "below" if d > 0 else "above"
            return (
                f"{who}'s row was {n} row{'s' if n != 1 else ''} {word} {other}'s row."
            )
        word = "right" if d > 0 else "left"
        return f"{who}'s column was {n} column{'s' if n != 1 else ''} to the {word} of {other}'s column."
    if a.kind == "compass":
        return f"{who} was {COMPASS_WORDS[(a['dr'], a['dc'])]} of {other}."
    if a.kind == "in_areas":
        names = " or ".join(_area_phrase(th.area(x)) for x in a["areas"])
        return f"{who} was in {names}."
    if a.kind == "tag_in_area":
        # Was "Someone who woman was in A's room" — the tag is a noun, not a relative clause.
        return f"Someone who is a {th.tag(a['tag'])} was in {who}'s area."
    if a.kind == "on_in_areas":
        names = " or ".join(_area_phrase(th.area(x)) for x in a["areas"])
        obj = th.obj(a["obj"])
        obj = {"sand": "sand patch", "water": "water feature"}.get(obj, obj)
        return f"{who} was on a {obj} in {names}."
    if a.kind == "area_no_offset":
        d = a["d"]
        if d == 0:
            return f"{who} was in the same area as {other}."
        return (
            f"{who}'s area number was {abs(d)} "
            f"{'higher' if d > 0 else 'lower'} than {other}'s."
        )
    if a.kind == "not_area_no_offset":
        # "immediately" was emitted for every offset, so d=-2 rendered as d=-1 and the sentence
        # stated a different constraint than the atom. Round-trip verification caught it.
        d = a["d"]
        if abs(d) == 1:
            word = "immediately after" if d > 0 else "immediately before"
            return f"{who}'s area did not come {word} {other}'s."
        return (
            f"{who}'s area number was not {abs(d)} "
            f"{'higher' if d > 0 else 'lower'} than {other}'s."
        )
    if a.kind == "area_occupancy_parity":
        p = a["par"]
        return f"Each {p}-numbered area contained an {p} number of people."

    # Every declared parameter gets a slot, themed where a theme has a word for it. Building this
    # from `spec.params` rather than a fixed list is what lets a newly registered predicate render
    # without touching this function — the previous fixed dict raised KeyError on every new kind.
    fields = {"holder": who, "other": other}
    for name in spec.params:
        if name in fields:
            continue
        val = a[name]
        if name == "area":
            fields[name] = th.area(val)
        elif name == "areas":
            fields[name] = " or the ".join(th.area(x) for x in val)
        elif name == "obj":
            label = th.obj(val)
            fields[name] = {"sand": "sand patch", "water": "water feature"}.get(
                label, label
            )
        elif name == "ter":
            fields[name] = th.obj(val)  # themes may rename terrain like any other noun
        elif name == "tag":
            fields[name] = th.tag(val)
        elif name in ("row", "col"):
            fields[name] = val + 1  # 1-based for a reader
        else:
            fields[name] = val  # side / axis / par / d: plain words already
    return spec.template.format(**fields).replace("a flowers", "the flowers")


def render_clue(c: Clue, case: Case, th: Theme) -> str:
    parts = [render_atom(a, case, th) for a in c.atoms]
    if len(parts) == 1:
        return parts[0]
    # Each atom carries its own subject. Existential clauses such as
    # "Someone else in V's area ..." must not inherit V's later predicates.
    return " ".join(parts)


# =============================================================================================
# Scene text
# =============================================================================================
def render_scene(case: Case, th: Theme, *, solution: bool = False) -> str:
    s = case.scene
    at = {k: th.name(x)[:2] for x, k in case.solution.items()} if solution else {}
    # The commonest terrain is the *background* and is left unmarked, exactly as the reference game
    # leaves fairway unlabelled and paints only the sand, water and rough. Marking every cell makes a
    # 16x16 map unreadable and says nothing.
    from collections import Counter

    ground = (
        Counter(s.terrain_of).most_common(1)[0][0] if s.terrain_of else DEFAULT_TERRAIN
    )
    # A 16-wide board at 11 columns per cell is 176 characters and wraps in any terminal.
    width = 11 if s.W <= 9 else 8
    lines = ["     " + "".join(f"{chr(ord('a')+c):^{width}}" for c in range(s.W))]
    for r in range(s.H):
        row = [f"{r+1:>3}  "]
        for c in range(s.W):
            k = s.k(r, c)
            if k in at:
                token = f"[{at[k]}]"
            elif s.obj_of[k] is not None:
                o = s.obj_of[k]
                token = th.obj(o)
                token = token if len(token) <= width - 2 else token[: width - 3] + "."
                token = f"({token})" if not s.prop_standable(o) else f"<{token}>"
            elif s.terrain_of[k] != ground:
                # Terrain is a *region*, so it must be visible or the clues that reference it
                # ("beside a water square") are unanswerable. Braced to read as ground rather than
                # as an object, and marked `~` where nobody can stand.
                t = s.terrain_of[k]
                nm = th.obj(t)
                nm = nm if len(nm) <= width - 3 else nm[: width - 3]
                token = f"{{{nm}}}" if TERRAINS[t].standable else f"~{nm}~"
            else:
                token = "."
            row.append(f"{token:^{width}}")
        lines.append("".join(row))
        if r < s.H - 1:
            seg = ["     "]
            for c in range(s.W):
                a1, a2 = s.area_of[s.k(r, c)], s.area_of[s.k(r + 1, c)]
                seg.append(("=" * width) if a1 != a2 else (" " * width))
            lines.append("".join(seg))
    return "\n".join(lines)


def render_scene_compact(case: Case, th: Theme, *, solution: bool = False) -> str:
    """A compact, lossless scene view for language-model and terminal use.

    Emoji are deliberately confined to the legends: their display width and tokenisation differ
    across clients, so they must never carry unique information.  The grids themselves use stable
    ASCII codes and contain every cell exactly once.  A reader can reconstruct area membership,
    props, terrain, standability and doors from this block without interpreting wall art.
    """
    s = case.scene
    area_codes = {a: f"A{a + 1}" for a in range(s.n_areas)}
    props = sorted(s.props, key=lambda p: p.pid)
    prop_codes = {p.pid: f"P{i + 1}" for i, p in enumerate(props)}
    terrains = sorted(set(s.terrain_of))
    terrain_codes = {t: f"T{i + 1}" for i, t in enumerate(terrains)}
    at = {k: x for x, k in case.solution.items()} if solution else {}

    def grid(title: str, token) -> list[str]:
        values = [[str(token(s.k(r, c))) for c in range(s.W)] for r in range(s.H)]
        width = max(2, max(len(x) for row in values for x in row))
        lines = [
            title,
            "     " + " ".join(f"{chr(ord('a') + c):>{width}}" for c in range(s.W)),
        ]
        for r, row in enumerate(values):
            lines.append(f"{r + 1:>3}  " + " ".join(f"{x:>{width}}" for x in row))
        return lines

    def cell_feature(k: int) -> str:
        if k in at:
            return f"[{at[k]}]"
        pid = s.prop_of[k]
        if pid is not None:
            return prop_codes[pid]
        return "." if k in s.open_cells else "#"

    out = [
        "COMPACT SCENE — use coordinates to reason; emoji are redundant labels only.",
        "Each AREA/FEATURE cell gives its area and prop code. '.' is no prop; '#' is a blocked "
        "terrain cell. Exact standability is stated in the legends.",
        *grid(
            "AREA/FEATURE GRID",
            lambda k: f"{area_codes[s.area_of[k]]}/{cell_feature(k)}",
        ),
        "",
        "AREA LEGEND",
    ]
    for a in range(s.n_areas):
        out.append(f"  {area_codes[a]} = {th.area(a)}")

    out.append("\nPROP LEGEND")
    if not props:
        out.append("  (none)")
    for p in props:
        icon = "🟢" if p.standable else "⛔"
        landmark = " 📍landmark" if p.landmark else ""
        cells = " ".join(cell_label(case, k) for k in sorted(p.cells))
        out.append(
            f"  {prop_codes[p.pid]} {icon} {th.obj(p.pid)} — "
            f"{'standable' if p.standable else 'blocked'}{landmark}; cells: {cells}"
        )

    # Terrain is a separate layer because a cell can carry both terrain and a prop. A uniform floor
    # needs one sentence rather than a duplicate grid; any non-trivial terrain gets the full layer.
    if len(terrains) == 1 and terrains[0] == DEFAULT_TERRAIN:
        out.append("\nTERRAIN\n  all cells: floor 🗺 standable")
    else:
        out.extend(
            [
                "",
                *grid("TERRAIN GRID", lambda k: terrain_codes[s.terrain_of[k]]),
                "",
                "TERRAIN LEGEND",
            ]
        )
        for t in terrains:
            standable = TERRAINS[t].standable
            out.append(
                f"  {terrain_codes[t]} 🗺 {th.obj(t)} — "
                f"{'standable' if standable else 'blocked'}"
            )

    out.append("\nDOORS / WINDOWS")
    if not s.doors:
        out.append("  (none)")
    else:
        for d in sorted((tuple(sorted(x)) for x in s.doors)):
            out.append(f"  🚪 {cell_label(case, d[0])} <-> {cell_label(case, d[1])}")
    return "\n".join(out)


def render_areas(case: Case, th: Theme) -> str:
    s = case.scene
    out = []
    for a in range(s.n_areas):
        cells = " ".join(cell_label(case, k) for k in s.cells_of_area(a))
        out.append(f"  {th.area(a)}: {cells}")
    return "\n".join(out)


RULES = """RULES
  1. Every person stands on exactly one square. No two people share a row, and no two share a
     column. (With {n} people on a {W}x{H} grid, every row and every column holds exactly one.)
  2. Squares marked (...) hold something you cannot stand on. Squares marked <...> hold furniture
     you CAN stand on. A bare '.' is empty floor.
  3. The grid is divided into areas by the '=' walls; the area list below is authoritative.
  4. The victim, {victim}, is one of the {n} people and occupies a square like everyone else --
     think of it as where everyone stood at the moment of the murder.
"""

COMPACT_RULES = """RULES
  1. Every person stands on exactly one square. No two people share a row, and no two share a
     column. (With {n} people on a {W}x{H} grid, every row and every column holds exactly one.)
  2. In AREA/FEATURE, A1/A2/... are areas, P1/P2/... are props, '.' means no prop, and '#'
     means terrain makes the square unusable. The prop and terrain legends state standability.
  3. Area membership is given explicitly in every grid cell; doors/windows are listed by their two
     endpoint cells.
  4. The victim, {victim}, is one of the {n} people and occupies a square like everyone else --
     think of it as where everyone stood at the moment of the murder.
"""

TERMS = """TERMS
  Beside: one square up, down, left or right, within the same area, unless a clue says otherwise.
  Corner: a square touching two adjacent boundaries of its area, including the outer border.
  Outer border: the first or last row or column of the whole grid.
  In front of a door/window: either of the two squares joined by that opening. Areas stay separate.
  With: in the same area. Alone: no other person in that area, including the victim.
  Alone with: exactly those two people in the area.
  Offsets compare only the named row or column. Area numbers are counted from 1.
  An empty area contains zero people; zero is even.
  Terrain is the ground layer, separate from named props that may have the same label.
"""

GOAL_MURDERER = """GOAL
  {victim} {note}. The murderer is the one person who was ALONE WITH {victim} -- in the same area,
  with no third person there.
  Your answer is the WHOLE arrangement: every person and the square they stood on. Name the
  murderer as well, but the arrangement is what is judged -- with only a handful of suspects, a
  name on its own is indistinguishable from a guess.
"""

GOAL_VICTIM_CELL = """GOAL
  {victim} {note}. Your answer is the WHOLE arrangement: every person and the square they stood
  on. The square {victim} occupied is what the case turns on, but the full arrangement is judged.
"""


def render_case(
    case: Case,
    th: Theme | None = None,
    *,
    include_solution: bool = False,
    scene_format: str = "classic",
) -> str:
    th = th or canonical_theme(case)
    th.validate(case)
    if scene_format not in ("classic", "compact"):
        raise ValueError(f"unknown scene format {scene_format!r}")
    n = len(case.characters)
    goal = GOAL_MURDERER if case.vdef.answer == "murderer" else GOAL_VICTIM_CELL
    rules = COMPACT_RULES if scene_format == "compact" else RULES
    scene = (
        render_scene_compact(case, th, solution=include_solution)
        if scene_format == "compact"
        else render_scene(case, th, solution=include_solution)
    )
    cast = ", ".join(
        f"{th.name(x)}" + (" (the victim)" if x == case.victim else "")
        for x in case.characters
    )
    clues = "\n".join(
        f"  {i+1}. {render_clue(c, case, th)}" for i, c in enumerate(case.clues)
    )
    attributes = (
        (
            "ATTRIBUTES\n"
            + "\n".join(
                f"  {th.name(x)}: "
                + (
                    ", ".join(th.tag(t) for t in sorted(case.tags.get(x, ()), key=str))
                    or "no listed attributes"
                )
                for x in case.characters
            )
            + "\n"
        )
        if case.tags
        else ""
    )
    parts = [
        f"CASE: {th.title}",
        (f"\n{th.blurb}\n" if th.blurb else ""),
        rules.format(n=n, W=case.scene.W, H=case.scene.H, victim=th.name(case.victim)),
        TERMS,
        goal.format(victim=th.name(case.victim), note=th.victim_note),
        f"PEOPLE ({n})\n  {cast}\n",
        attributes,
        "SCENE\n" + scene + "\n",
        (
            ("AREAS\n" + render_areas(case, th) + "\n")
            if scene_format == "classic"
            else ""
        ),
        f"CLUES ({len(case.clues)})\n{clues}\n",
    ]
    return "\n".join(p for p in parts if p)


def render_certificate(case: Case, certificate, th: Theme | None = None) -> str:
    """Render a deterministic certificate as themed, human-readable numbered steps.

    The certificate remains the machine-checkable source. This function changes names and cell
    notation only; it never asks an LLM to invent a reason or a deduction.
    """
    th = th or canonical_theme(case)
    th.validate(case)
    icons = {1: "🔹", 2: "🔸", 3: "🧠", 4: "✅"}

    def humanise(text: str) -> str:
        text = re.sub(
            r"\br(\d+)c(\d+)\b",
            lambda m: f"{chr(ord('a') + int(m.group(2)) - 1)}{int(m.group(1))}",
            text,
        )
        for sym in sorted(case.characters, key=len, reverse=True):
            text = re.sub(rf"(?<!\w){re.escape(sym)}(?!\w)", th.name(sym), text)
        return text

    lines = []
    for i, step in enumerate(certificate.steps, 1):
        lines.append(
            f"{i:>2}. {icons.get(step.tier, '•')} "
            f"[{step.kind}, tier {step.tier}] {humanise(step.text)}"
        )
    if not certificate.solved:
        lines.append(
            f"\nStopped with {len(certificate.stuck)} unresolved character(s)."
        )
    return "\n".join(lines)
