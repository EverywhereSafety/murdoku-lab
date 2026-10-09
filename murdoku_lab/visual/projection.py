"""An explicit public allowlist. Never serialize a Case or Theme wholesale to the client."""

from murdoku_lab.core.board import TERRAINS
from murdoku_lab.core.render import cell_label, render_atom

ROOM_COLORS = (
    "#ead4bc",
    "#d5e3c5",
    "#efe2b5",
    "#cfdfe0",
    "#eed5cf",
    "#ddd3e9",
    "#d5e6db",
    "#e5ddb5",
    "#cdd8ed",
    "#e7cbdc",
    "#dfdecf",
    "#c4ded9",
)
PERSON_COLORS = (
    "#b25d43",
    "#4e6d8d",
    "#50795d",
    "#b18a3d",
    "#8b6681",
    "#537d80",
    "#826747",
    "#6e7996",
)
ART_KINDS = frozenset(
    (
        "shelf",
        "chair",
        "table",
        "plant",
        "tree",
        "flowers",
        "carpet",
        "shrub",
        "piano",
        "bed",
        "car",
        "water",
        "sand",
        "flag",
        "tee",
        "golf_cart",
        "statue",
        "boulder",
        "barrel",
        "crate",
        "box",
        "register",
        "palm",
        "tv",
        "bear",
        "void",
    )
)


def public_observation(
    pad,
    *,
    session_id="local",
    case_id="local",
    revision=0,
    reviewed=(),
    notebook="",
    done=False,
    terminal=None,
    can_undo=False,
    can_redo=False,
    setting="The crime scene",
    eyebrow="An illustrated case",
    last_event=None,
):
    """Geometry + visible clue prose + claimed state. No oracle-derived candidates or scores
    before submission. This also accepts an existing MurdokuToolEnvironment.pad directly.
    """
    case, th = pad.case, pad.theme
    scene = case.scene
    cells = []
    for k in range(scene.n_cells):
        r, c = scene.rc(k)
        walls = []
        for name, dr, dc in (
            ("north", -1, 0),
            ("east", 0, 1),
            ("south", 1, 0),
            ("west", 0, -1),
        ):
            rr, cc = r + dr, c + dc
            if (
                not (0 <= rr < scene.H and 0 <= cc < scene.W)
                or scene.area_of[rr * scene.W + cc] != scene.area_of[k]
            ):
                walls.append(name)
        cells.append(
            {
                "cell": cell_label(case, k),
                "row": r,
                "col": c,
                "area": scene.area_of[k],
                "terrain": scene.terrain_of[k],
                "prop": scene.obj_of[k],
                "standable": scene.standable(k),
                "walls": walls,
            }
        )
    clues = []
    for i, clue in enumerate(case.clues):
        # Shorten the corner definition without adding or removing a predicate. Both the
        # browser and image observation consume exactly this same public wording.
        parts = []
        for atom in clue.atoms:
            parts.append(render_atom(atom, case, th))
        clues.append(
            {
                "id": f"clue-{i + 1}",
                "number": i + 1,
                "person": clue.holder,
                "text": " ".join(parts),
                "reviewed": f"clue-{i + 1}" in reviewed,
            }
        )
    rules = [
        "One person per row and column, including the victim.",
        "Crossed squares are blocked. All other squares may be occupied, including furniture without a cross.",
        "Beside means one square up, down, left or right, within the same area.",
        "A corner touches two adjacent area boundaries. Doors do not merge areas.",
        "Alone means no other person in the area. With means in the same area; alone with means exactly two people.",
        "Outer border means the first or last row or column of the whole grid.",
        "In front of a door/window means either of its two joined squares.",
        "Offsets compare only the named coordinate. Area numbers start at 1; zero people is an even count.",
        "Terrain is the ground layer, separate from named props that may share its label.",
    ]
    if case.vdef.murderer_rule == "classic":
        rules.append(
            "The murderer was alone with the victim: exactly two people in that area."
        )
        goal = f"Place everyone, then name the person who was alone with {th.name(case.victim)}."
    else:
        rules.append("This is an open case: there is no alone-with-the-victim rule.")
        goal = f"Place everyone, then identify the square occupied by {th.name(case.victim)}."
    return {
        "schema": "murdoku.observation/1",
        "session_id": session_id,
        "case_id": case_id,
        "revision": revision,
        "title": th.title,
        "blurb": th.blurb,
        "eyebrow": eyebrow,
        "setting": setting,
        "variant": case.variant,
        "goal_type": case.vdef.answer,
        "goal": goal,
        "rules": rules,
        "scene": {
            "width": scene.W,
            "height": scene.H,
            "cells": cells,
            "areas": [
                {
                    "id": a,
                    "number": a + 1,
                    "name": th.area(a),
                    "color": ROOM_COLORS[a % len(ROOM_COLORS)],
                }
                for a in range(scene.n_areas)
            ],
            "props": [
                {
                    "id": p.pid,
                    "name": th.obj(p.pid),
                    "art": p.pid if p.pid in ART_KINDS else "generic",
                    "asset": th.assets.get(p.pid),
                    "standable": p.standable,
                    "cells": [cell_label(case, k) for k in sorted(p.cells)],
                }
                for p in scene.props
            ],
            "terrains": [
                {"id": t, "name": th.obj(t), "standable": TERRAINS[t].standable}
                for t in sorted(set(scene.terrain_of))
            ],
            "doors": [
                [cell_label(case, k) for k in sorted(d)]
                for d in sorted(scene.doors, key=lambda pair: sorted(pair))
            ],
        },
        "people": [
            {
                "id": p,
                "name": th.name(p),
                "victim": p == case.victim,
                "portrait": i,
                "color": PERSON_COLORS[i % len(PERSON_COLORS)],
                "tags": [th.tag(t) for t in sorted(case.tags.get(p, ()), key=str)],
            }
            for i, p in enumerate(case.characters)
        ],
        "clues": clues,
        "placements": {p: cell_label(case, k) for p, k in sorted(pad.placed.items())},
        "marks": {
            p: [cell_label(case, k) for k in sorted(m)]
            for p, m in sorted(pad.marks.items())
        },
        "notebook": notebook,
        "done": done,
        "terminal": terminal if done else None,
        "can_undo": can_undo and not done,
        "can_redo": can_redo and not done,
        "last_event": last_event,
    }
