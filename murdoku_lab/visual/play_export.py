"""Static case bundles for the player app: `murdoku.play_case/1`.

    python -m murdoku_lab.visual.play_export
    python -m murdoku_lab.visual.play_export --records outputs/showcase/cases.jsonl

Writes web/public/cases/: `index.json` (the case library), and per case `<id>.json` (the
bundle), `<id>.day.svg` / `<id>.night.svg` (the static casebook scene: floors, walls, furniture,
plaques, frame) and `<id>.thumb.svg` (the same scene at library-card size: about 7 KB once a
host gzips it, a tenth of a PNG). The player draws people, notes and coordinates on top of the
scene and never loads Python.

A bundle holds the public observation and a sealed secret (solution, verdict, epilogue, hints;
see seal.py). Nothing in the public part is derived from the solution.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.render import cell_label
from murdoku_lab.core.theme import Theme
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.visual import demos
from murdoku_lab.visual.art import STATIC_LAYERS, casebook, portraits, thumbnail_svg
from murdoku_lab.visual.projection import public_observation
from murdoku_lab.visual.seal import seal


def hint_data(case):
    """What the player's hints need, all derived from the clues: the order in which pure
    deduction places people (the first person in it that the player has not placed is always
    deducible from the clues and everyone before them), each person's squares allowed by their
    own statements, and, per person and square, the statement that rules the square out.
    """
    from murdoku_lab.core.atoms import SPECS, unary_mask
    from murdoku_lab.solver.exact import candidate_masks
    from murdoku_lab.solver.logic import certify

    scene = case.scene
    order = list(certify(case).place_order)
    order += [p for p in case.characters if p not in order]
    candidates = {
        p: [cell_label(case, k) for k in sorted(cells)]
        for p, cells in candidate_masks(case).items()
    }
    forbid = {p: {} for p in case.characters}
    for number, clue in enumerate(case.clues, start=1):
        for atom in clue.atoms:
            spec = SPECS[atom.kind]
            if spec.arity == "unary" or (
                spec.arity == "global" and spec.mask is not None
            ):
                allowed = unary_mask(atom, scene)
                if allowed is None:
                    continue
                for k in sorted(set(scene.open_cells) - set(allowed)):
                    forbid[atom.holder].setdefault(cell_label(case, k), number)
    return {"order": order, "candidates": candidates, "forbid": forbid}


SCHEMA = "murdoku.play_case/1"
LIBRARY = "murdoku.play_library/1"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "web" / "public" / "cases"
BANDS = {"easy": "Easy", "medium": "Medium", "hard": "Hard", "expert": "Expert"}
# Rough solving time in minutes by board size, refined once players time real cases.
MINUTES = {5: (2, 4), 6: (3, 7), 7: (5, 10), 8: (8, 15), 9: (12, 25)}
# Beyond 9×9 (the 16×16 and 24×24 classics) a case is a marathon of many sittings.
MARATHON = (8 * 60, 48 * 60)
SESSION_FIELDS = (
    "session_id",
    "revision",
    "notebook",
    "done",
    "terminal",
    "can_undo",
    "can_redo",
    "last_event",
    "placements",
    "marks",
)


def _difficulty(case):
    band = case.target_band
    size = case.scene.W
    if size > max(MINUTES):
        lo, hi = MARATHON
    else:
        lo, hi = MINUTES.get(size, (15, 40))
        if band == "hard":
            lo, hi = round(lo * 1.4), round(hi * 1.5)
        elif band == "easy":
            lo, hi = max(1, round(lo * 0.7)), round(hi * 0.8)
    return {"band": band, "label": BANDS.get(band, "Classic"), "minutes": [lo, hi]}


def bundle(case, theme, *, case_id, kind, setting, eyebrow, salt=""):
    """One case for the player: public facts in the clear, answers sealed."""
    obs = public_observation(
        Scratchpad(case, theme), case_id=case_id, setting=setting, eyebrow=eyebrow
    )
    public = {k: v for k, v in obs.items() if k not in SESSION_FIELDS}
    for person in public["people"]:
        state = "victim" if person["victim"] else None
        person["face"] = portraits.look_inner(portraits.roster()[person["look"]], state)
    solution = {p: cell_label(case, k) for p, k in sorted(case.solution.items())}
    victim_area = case.scene.area_of[case.solution[case.victim]]
    secret = {
        "goal_type": case.vdef.answer,
        "solution": solution,
        "victim_cell": solution[case.victim],
        "victim_area": victim_area,
        "murderer": case.murderer if case.vdef.answer == "murderer" else None,
        "epilogue": None,
        "hints": hint_data(case),
    }
    if theme.setting_id and secret["murderer"]:
        from murdoku_lab.setter import settings

        secret["epilogue"] = settings.epilogue(
            theme, case, secret["murderer"], victim_area
        )
    visual = theme.visual or {}
    meta = {
        "title": theme.title,
        "blurb": theme.blurb,
        "eyebrow": eyebrow,
        "setting": {"id": theme.setting_id or None, "name": setting},
        "size": f"{case.scene.W}×{case.scene.H}",
        "width": case.scene.W,
        "height": case.scene.H,
        "people": len(case.characters),
        "rooms": case.scene.n_areas,
        "difficulty": _difficulty(case),
        "accent": visual.get("accent"),
        "frame": visual.get("frame", "manor"),
    }
    return {
        "schema": SCHEMA,
        "id": case_id,
        "kind": kind,
        "locale": "en",
        "content_hash": case.content_hash(),
        "meta": meta,
        "public": public,
        "scene": {"day": f"{case_id}.day.svg", "night": f"{case_id}.night.svg"},
        "thumb": f"{case_id}.thumb.svg",
        "share": None,
        "ai_results": None,
        "secret": seal(secret, case_id, salt),
    }


TUTORIAL = ROOT / "content" / "tutorial" / "tutorial.json"


def entries(records=None):
    """(case_id, kind, case, theme, setting name, eyebrow): the training case
    (scripts/build_tutorial.py), the classics (restyled where setter/restyles/ says so) and any
    dressed records."""
    if TUTORIAL.exists():
        row = json.loads(TUTORIAL.read_text())
        yield (
            "tutorial",
            "tutorial",
            Case.from_json(row["murdoku_case"]),
            Theme.from_json(row["murdoku_theme"]),
            "Training case",
            "Your first case",
        )
    from murdoku_lab.setter import settings

    # A classic with a restyle spec keeps its own words and gets a setting pack's look.
    styles = settings.restyles()
    for entry in demos.catalogue().values():
        theme = entry.theme
        if entry.slug in styles:
            theme = settings.restyle(entry.case, theme, styles[entry.slug])
        yield entry.slug, "classic", entry.case, theme, entry.setting, entry.eyebrow
    if not records:
        return

    for line in Path(records).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        case = Case.from_json(row["murdoku_case"])
        theme = Theme.from_json(row["murdoku_theme"])
        case_id = (
            row.get("visual_case_id")
            or hashlib.sha256(
                f"{case.content_hash()}|{theme.theme_id}".encode()
            ).hexdigest()[:12]
        )
        pack = settings.load(theme.setting_id) if theme.setting_id else {}
        yield (
            case_id,
            "themed",
            case,
            theme,
            pack.get("name", "The crime scene"),
            pack.get("eyebrow", "An illustrated case"),
        )


def export(out=OUT, records=None, *, thumbs=True):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    library, seen = [], set()
    for case_id, kind, case, theme, setting, eyebrow in entries(records):
        if case_id in seen:
            raise ValueError(f"duplicate case id {case_id!r}")
        seen.add(case_id)
        data = bundle(
            case, theme, case_id=case_id, kind=kind, setting=setting, eyebrow=eyebrow
        )
        (out / f"{case_id}.json").write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        )
        obs = public_observation(Scratchpad(case, theme))
        for mode in ("day", "night"):
            (out / f"{case_id}.{mode}.svg").write_text(
                casebook.scene_svg(
                    obs,
                    theme=mode,
                    layers=STATIC_LAYERS,
                    cell_labels="none",
                    backdrop=False,
                )
            )
        if thumbs:
            (out / f"{case_id}.thumb.svg").write_text(thumbnail_svg(obs, px=320))
        library.append(
            {
                "id": case_id,
                "kind": kind,
                "title": data["meta"]["title"],
                "blurb": data["meta"]["blurb"],
                "setting": data["meta"]["setting"],
                "size": data["meta"]["size"],
                "difficulty": data["meta"]["difficulty"],
                "people": data["meta"]["people"],
                "rooms": data["meta"]["rooms"],
                "accent": data["meta"]["accent"],
                "goal_type": data["public"]["goal_type"],
                "content_hash": data["content_hash"],
                "thumb": data["thumb"],
                "url": f"{case_id}.json",
            }
        )
    index = {"schema": LIBRARY, "cases": library}
    (out / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1) + "\n"
    )
    return index


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", help="dressed records (scripts/build_showcase.py)")
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--no-thumbs", action="store_true")
    args = parser.parse_args(argv)
    index = export(args.out, args.records, thumbs=not args.no_thumbs)
    print(f"wrote {len(index['cases'])} cases to {args.out}")


if __name__ == "__main__":
    main()
