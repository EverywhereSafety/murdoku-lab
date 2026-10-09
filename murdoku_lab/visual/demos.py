"""Small authored cases for the viewer. Private solutions never enter the public projection.

These are UI fixtures, not calibrated benchmark samples or official Murdoku cases.
Authored fixtures used by the playable interface and solver tests.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import re

from murdoku_lab.core.atoms import Atom
from murdoku_lab.core.board import Scene
from murdoku_lab.core.instance import Case, Clue
from murdoku_lab.core.theme import Theme, canonical_theme


@dataclass(frozen=True)
class Entry:
    slug: str
    case: Case
    theme: Theme
    eyebrow: str = "An original illustrated case"
    setting: str = "The crime scene"
    description: str = "Read the statements. Reconstruct the evening."


def glasshouse(*, open_case=False):
    # An irregular room partition and a four-square rug exercise real footprints.
    rows = [
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 1, 1, 1],
        [0, 0, 2, 2, 1, 1],
        [3, 3, 2, 2, 4, 4],
        [3, 3, 2, 2, 4, 4],
        [3, 3, 3, 4, 4, 4],
    ]
    props = {
        "a1": "shelf",
        "b1": "chair",
        "c1": "table",
        "c2": "table",
        "d1": "plant",
        "f1": "tree",
        "e2": "flowers",
        "f3": "plant",
        "c4": "carpet",
        "d4": "carpet",
        "c5": "carpet",
        "d5": "carpet",
        "a4": "piano",
        "b5": "chair",
        "a6": "plant",
        "e4": "table",
        "f4": "table",
        "f5": "chair",
        "e6": "shrub",
    }

    def k(label):
        return (int(label[1:]) - 1) * 6 + ord(label[0]) - 97

    objects = [None] * 36
    for label, obj in props.items():
        objects[k(label)] = obj
    doors = frozenset(
        frozenset((k(a), k(b)))
        for a, b in (
            ("b3", "c3"),
            ("d3", "e3"),
            ("b4", "c4"),
            ("d5", "e5"),
        )
    )
    scene = Scene(
        6,
        6,
        tuple(a for row in rows for a in row),
        tuple(objects),
        doors,
        terrain_of=tuple("tile" if a == 4 else "floor" for row in rows for a in row),
    )
    clues = (
        Clue((Atom("on", "A", ("chair",)), Atom("in_area", "A", (0,)))),
        Clue((Atom("beside", "B", ("flowers",)), Atom("in_corner", "B"))),
        Clue((Atom("on", "C", ("carpet",)),)),
        Clue((Atom("on", "D", ("chair",)), Atom("in_area", "D", (4,)))),
        Clue((Atom("beside", "E", ("shrub",)),)),
        Clue((Atom("beside", "V", ("shelf",)),)),
    )
    solution = {
        p: k(c) for p, c in dict(A="b1", B="e3", C="c4", D="f5", E="d6", V="a2").items()
    }
    case = Case(
        scene,
        tuple(solution),
        "V",
        clues,
        solution,
        variant="open" if open_case else "classic",
    )
    theme = Theme(
        theme_id="glasshouse-flat-v1",
        title="The Last Known Place" if open_case else "The Glasshouse Affair",
        names={
            "A": "Ada",
            "B": "Basil",
            "C": "Cleo",
            "D": "Dorian",
            "E": "Esme",
            "V": "Victor",
        },
        areas=("Study", "Conservatory", "Hall", "Drawing room", "Terrace"),
        objects={"shelf": "bookshelf", "carpet": "rug", "shrub": "rose bush"},
        blurb="Six guests. A quiet house. One story that doesn't quite add up.",
    )
    case.self_check()
    theme.validate(case)
    return Entry(
        "last-place" if open_case else "glasshouse",
        case,
        theme,
        (
            "Case 03 · A different question"
            if open_case
            else "Case 01 · An evening at Alderwick"
        ),
        "Alderwick House",
        theme.blurb,
    )


def lily_pond():
    # Eight people, four outdoor areas, water/sand terrain and multiple-square props.
    # Spatial clues are deliberately simple: this case tests the rendering and interface.
    n = 8
    areas = tuple(
        (0 if c < 4 else 1) if r < 4 else (2 if c < 4 else 3)
        for r in range(n)
        for c in range(n)
    )
    ground = ["fairway"] * (n * n)
    objects = [None] * (n * n)

    def k(label):
        return (int(label[1:]) - 1) * n + ord(label[0]) - 97

    for label in ("f1", "g1", "f2", "g2", "g3"):
        ground[k(label)] = "water"
    for label in ("a6", "a7", "b6", "b7"):
        ground[k(label)] = "sand"
    for label in ("e6", "f6", "e7", "f7", "g7"):
        ground[k(label)] = "rough"
    for label, obj in {
        "a1": "tree",
        "c1": "flowers",
        "d3": "tree",
        "e1": "palm",
        "h3": "flowers",
        "b4": "statue",
        "c6": "boulder",
        "d8": "tree",
        "g5": "table",
        "h5": "table",
        "f8": "shrub",
        "a5": "flag",
        "b1": "chair",
        "d2": "chair",
        "f3": "chair",
        "h4": "chair",
        "g6": "chair",
        "e7": "chair",
        "c8": "chair",
    }.items():
        objects[k(label)] = obj
    positions = dict(A="b1", B="d2", C="f3", D="h4", E="g6", F="e7", G="c8", V="a5")
    # Every non-victim sits on a chair; their row order pins the ordered set of chairs.
    # The victim's flag occupies the remaining row and column. No raw solution coordinates
    # are sent to the viewer. The general murderer rule then determines the verdict.
    clues = []
    previous = None
    for p in positions:
        if p == "V":
            clues.append(Clue((Atom("on", p, ("flag",)),)))
            continue
        atoms = [Atom("on", p, ("chair",))]
        if previous:
            dr = 1
            dc = (ord(positions[p][0]) > ord(positions[previous][0])) * 2 - 1
            atoms.append(Atom("compass", p, (previous, dr, dc)))
        clues.append(Clue(tuple(atoms)))
        previous = p
    scene = Scene(
        n,
        n,
        areas,
        tuple(objects),
        terrain_of=tuple(ground),
        doors=frozenset((frozenset((k("d4"), k("e4"))), frozenset((k("d7"), k("e7"))))),
    )
    case = Case(
        scene,
        tuple(positions),
        "V",
        tuple(clues),
        {p: k(c) for p, c in positions.items()},
        variant="extended",
    )
    theme = Theme(
        "lily-pond-flat-v1",
        "A Ripple in the Garden",
        {
            "A": "Ada",
            "B": "Basil",
            "C": "Cleo",
            "D": "Dorian",
            "E": "Esme",
            "F": "Felix",
            "G": "Grace",
            "V": "Victor",
        },
        areas=("Orchard", "Lily pond", "Sand garden", "Tea lawn"),
        objects={"chair": "garden chair", "flag": "garden flag"},
        blurb="A garden party, interrupted. Follow the chairs around the grounds.",
    )
    case.self_check()
    theme.validate(case)
    return Entry(
        "lily-pond",
        case,
        theme,
        "Case 02 · Beyond the house",
        "Alderwick Gardens",
        theme.blurb,
    )


def catalogue(record_path: str | None = None):
    entries = [glasshouse(), lily_pond(), glasshouse(open_case=True), estate()]
    if record_path:
        path = Path(record_path)
        records = (
            [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            if path.suffix == ".jsonl"
            else [json.loads(path.read_text())]
        )
        for i, row in enumerate(records):
            payload = row.get("murdoku_case", row.get("case", row))
            case = Case.from_json(payload)
            case.self_check()
            td = row.get("murdoku_theme", row.get("theme"))
            theme = Theme.from_json(td) if td else canonical_theme(case)
            theme.validate(case)
            slug = row.get("visual_case_id", f"import-{i + 1}")
            if not isinstance(slug, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9_-]{0,120}", slug
            ):
                raise ValueError("invalid visual_case_id")
            if any(entry.slug == slug for entry in entries):
                raise ValueError(f"duplicate visual_case_id: {slug}")
            entries.append(
                Entry(
                    slug,
                    case,
                    theme,
                    f"Imported case {i + 1}",
                    "Imported scene",
                    theme.blurb,
                )
            )
    return {entry.slug: entry for entry in entries}


def _estate_scale_v1():
    """16x16 scale example. Chair order makes it solvable; this is not a hard benchmark."""
    n = 16
    columns = [0, 1, 8, 9, 10, 11, 12, 13, 2, 3, 4, 5, 6, 7, 14, 15]
    people = tuple("ABCDEFGHIJKLMNO") + ("V",)
    names = (
        "Ada",
        "Basil",
        "Cleo",
        "Dorian",
        "Esme",
        "Felix",
        "Grace",
        "Hugo",
        "Iris",
        "Jules",
        "Kit",
        "Luca",
        "Mabel",
        "Noah",
        "Otis",
        "Victor",
    )
    positions = {p: r * n + c for r, (p, c) in enumerate(zip(people, columns))}
    areas = tuple(
        (0 if c < 8 else 1) if r < 8 else (2 if c < 8 else 3)
        for r in range(n)
        for c in range(n)
    )
    ground = ["fairway"] * (n * n)
    objects = [None] * (n * n)
    for p, k in positions.items():
        objects[k] = "flag" if p == "V" else "chair"
    for r, c in ((2, 3), (4, 6), (6, 2), (9, 12), (11, 14), (14, 1), (13, 10)):
        objects[r * n + c] = "tree"
    for r, c in ((9, 9), (9, 10), (10, 9), (10, 10)):
        objects[r * n + c] = "table"
    for r in range(4):
        for c in (14, 15):
            ground[r * n + c] = "water"
    for r in (11, 12, 13):
        for c in (0, 1):
            ground[r * n + c] = "sand"
    for r in (12, 13, 14):
        for c in (10, 11, 12):
            ground[r * n + c] = "rough"
    scene = Scene(n, n, areas, tuple(objects), terrain_of=tuple(ground))
    clues = []
    for i, p in enumerate(people):
        atoms = [Atom("on", p, ("flag" if p == "V" else "chair",))]
        if 0 < i < len(people) - 1:
            atoms.append(
                Atom(
                    "compass",
                    p,
                    (people[i - 1], 1, 1 if columns[i] > columns[i - 1] else -1),
                )
            )
        clues.append(Clue(tuple(atoms)))
    case = Case(scene, people, "V", tuple(clues), positions, variant="course")
    theme = Theme(
        "estate-flat-v1",
        "Across the Estate",
        dict(zip(people, names)),
        areas=("West orchard", "Water garden", "South meadow", "East lawn"),
        objects={"chair": "garden chair", "flag": "garden flag"},
        blurb="A wider scene: sixteen people, four areas, and one connected map.",
    )
    case.self_check()
    theme.validate(case)
    return Entry(
        "estate",
        case,
        theme,
        "Case 04 · A scale example",
        "The Alderwick Estate",
        "A 16 × 16 layout and harness example. Use zoom to inspect the scene.",
    )


def estate():
    """Authored 16x16 manor and gardens, with mixed spatial and relational clues."""
    record = json.loads((Path(__file__).parent / "cases/estate.json").read_text())
    case = Case.from_json(record["murdoku_case"])
    theme = Theme.from_json(record["murdoku_theme"])
    case.self_check()
    theme.validate(case)
    return Entry(
        "estate",
        case,
        theme,
        "Case 04 · Alibis across Alderwick",
        "Alderwick House & Grounds",
        "Eleven connected spaces, a courtyard fountain, a pond and overlapping alibis.",
    )
