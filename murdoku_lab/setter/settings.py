"""Setting packs: the words and the look of a case, never its maths.

A setting pack (`setter/settings/<id>.json`) names rooms by the furniture they suit, gives each
formal prop kind a noun and a drawing (its "skin"), and carries the colours, floor finishes and
frame of the casebook art. `dress()` turns a formal case into a `Theme` for one setting and the
recurring cast. The content hash ignores themes, so dressing a case can never change its
solution, certificate or difficulty (tests/test_theme_invariance.py).
"""

import dataclasses
from functools import lru_cache
import hashlib
import json
import re
from pathlib import Path

from murdoku_lab.core.board import OBJECTS
from murdoku_lab.core.theme import Theme

SETTINGS_DIR = Path(__file__).resolve().parent / "settings"
CAST_PATH = Path(__file__).resolve().parents[1] / "resources" / "cast.json"

CLASSIC_KINDS = (
    "bed",
    "chair",
    "carpet",
    "car",
    "table",
    "tv",
    "shelf",
    "plant",
    "tree",
    "flowers",
    "shrub",
    "crate",
    "box",
    "register",
    "palm",
    "bear",
    "statue",
    "piano",
    "boulder",
    "barrel",
)
MIN_ROOMS = 9
SPATIAL_WORDS = (
    "north",
    "south",
    "east",
    "west",
    "left",
    "right",
    "beside",
    "corner",
    "row",
    "column",
    "above",
    "below",
    "next to",
    "alone",
)
EPILOGUE_FIELDS = {"murderer", "victim", "area", "motive"}


@lru_cache(maxsize=None)
def available():
    return tuple(sorted(p.stem for p in SETTINGS_DIR.glob("*.json")))


@lru_cache(maxsize=None)
def load(setting_id):
    if setting_id not in available():
        raise ValueError(f"unknown setting {setting_id!r}")
    pack = json.loads((SETTINGS_DIR / f"{setting_id}.json").read_text())
    validate(pack)
    return pack


@lru_cache(maxsize=None)
def cast():
    return json.loads(CAST_PATH.read_text())


def _words(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def validate(pack):
    """Schema and taste checks a pack must pass before it can dress a case."""
    from murdoku_lab.visual.art import materials, props

    problems = []
    if pack.get("schema") != "murdoku.setting/1":
        problems.append("schema must be murdoku.setting/1")
    for key in ("id", "name", "titles", "blurbs", "rooms", "objects", "visual"):
        if not pack.get(key):
            problems.append(f"missing {key}")
    if problems:
        raise ValueError(f"setting {pack.get('id')!r}: " + "; ".join(problems))
    rooms = pack["rooms"]
    names = [r["name"] for r in rooms]
    if len(rooms) < MIN_ROOMS:
        problems.append(f"needs at least {MIN_ROOMS} rooms")
    if len({n.lower() for n in names}) != len(names):
        problems.append("room names must be distinct")
    for room in rooms:
        unknown = set(room.get("suits", ())) - set(OBJECTS)
        if unknown:
            problems.append(
                f"room {room['name']!r} suits unknown kinds {sorted(unknown)}"
            )
        if room.get("finish") and room["finish"] not in materials.FINISHES:
            problems.append(
                f"room {room['name']!r} has unknown finish {room['finish']!r}"
            )
        if room.get("wallpaper"):
            try:
                materials.wallpaper_pattern(room["wallpaper"])
            except ValueError:
                problems.append(
                    f"room {room['name']!r} has unknown wallpaper {room['wallpaper']!r}"
                )
    objects = pack["objects"]
    missing = [k for k in CLASSIC_KINDS if k not in objects]
    if missing:
        problems.append(f"no noun for {missing}")
    nouns = [v.lower() for v in objects.values()]
    if len(set(nouns)) != len(nouns):
        problems.append("object nouns must be distinct")
    visual = pack["visual"]
    known_skins = props.all_skins()
    for kind, skin in (visual.get("skins") or {}).items():
        if kind not in OBJECTS:
            problems.append(f"skin for unknown kind {kind!r}")
        if skin not in known_skins and skin not in props.BASE:
            problems.append(f"unknown skin {skin!r}")
    for wp in visual.get("wallpapers") or ():
        try:
            materials.wallpaper_pattern(wp)
        except ValueError:
            problems.append(f"unknown wallpaper {wp!r}")
    for finish in visual.get("finishes") or ():
        if finish not in materials.FINISHES:
            problems.append(f"unknown finish {finish!r}")
    for finish, colourways in (visual.get("variants") or {}).items():
        known = {v[0] for v in materials.FLOOR_VARIANTS.get(finish, ())}
        if not known or set(colourways) - known:
            problems.append(f"unknown floor variants {finish}: {colourways}")
    for tint in list(visual.get("tints") or ()) + [visual.get("accent", "#000000")]:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", tint):
            problems.append(f"bad colour {tint!r}")
    # Blurbs and titles are read before the case is solved: they must name no room, object,
    # person or direction, so they carry no information.
    phrases = [n.lower() for n in names] + [v.lower() for v in objects.values()]
    people_words = {
        w
        for person in list(cast()["suspects"].values()) + cast()["victims"]
        for w in _words(person["name"])
    }
    for blurb in pack["blurbs"] + pack["titles"]:
        lower = blurb.lower()
        leaks = [p for p in phrases if re.search(rf"\b{re.escape(p)}\b", lower)]
        leaks += sorted(set(_words(blurb)) & people_words)
        leaks += [w for w in SPATIAL_WORDS if re.search(rf"\b{w}\b", lower)]
        if leaks:
            problems.append(f"blurb/title {blurb!r} mentions {leaks}")
    for line in pack.get("epilogues", ()):
        fields = set(re.findall(r"{(\w+)}", line))
        if not fields <= EPILOGUE_FIELDS:
            problems.append(
                f"epilogue uses unknown fields {sorted(fields - EPILOGUE_FIELDS)}"
            )
    from murdoku_lab.visual.art import frames

    if visual.get("frame") and visual["frame"] not in frames.FRAMES:
        problems.append(f"unknown frame {visual['frame']!r}")
    if problems:
        raise ValueError(f"setting {pack['id']!r}: " + "; ".join(problems))


def _pick(key, n):
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "big") % n


def _area_kinds(case):
    scene = case.scene
    kinds = [dict() for _ in range(scene.n_areas)]
    for k in range(scene.n_cells):
        pid = scene.obj_of[k]
        if pid:
            counts = kinds[scene.area_of[k]]
            counts[pid] = counts.get(pid, 0) + 1
    return kinds


def assign_rooms(case, rooms):
    """Room index per area, maximising how well each room suits the furniture it holds."""
    import networkx as nx

    kinds = _area_kinds(case)
    graph = nx.Graph()
    for a, counts in enumerate(kinds):
        for r, room in enumerate(rooms):
            suits = set(room.get("suits", ()))
            score = sum(n for kind, n in counts.items() if kind in suits)
            # A small preference for the pack's own order keeps ties deterministic.
            graph.add_edge(("a", a), ("r", r), weight=1000 + 10 * score - r)
    matching = nx.max_weight_matching(graph, maxcardinality=True)
    out = {}
    for u, v in matching:
        area, room = (u, v) if u[0] == "a" else (v, u)
        out[area[1]] = room[1]
    return out


def dress(case, setting_id, *, salt=""):
    """A Theme for `case` in setting `setting_id`, with the recurring cast."""
    pack = load(setting_id)
    key = f"{setting_id}|{case.content_hash()}|{salt}"
    people = cast()
    names, pronouns = {}, {}
    for symbol in case.characters:
        if symbol == case.victim:
            victims = people["victims"]
            v = victims[_pick(key + "|victim", len(victims))]
            names[symbol], pronouns[symbol] = v["name"], v["pronoun"]
        elif symbol in people["suspects"]:
            s = people["suspects"][symbol]
            names[symbol], pronouns[symbol] = s["name"], s["pronoun"]
        else:
            from murdoku_lab.core.name_library import FEMININE

            names[symbol], pronouns[symbol] = FEMININE[symbol][0], "they"
    rooms = pack["rooms"]
    if case.scene.n_areas > len(rooms):
        raise ValueError(
            f"setting {setting_id!r} names {len(rooms)} rooms; the board has {case.scene.n_areas}"
        )
    chosen = assign_rooms(case, rooms)
    areas = tuple(rooms[chosen[a]]["name"] for a in range(case.scene.n_areas))
    present = {p.pid for p in case.scene.props}
    objects = {k: v for k, v in pack["objects"].items() if k in present}
    visual = dict(pack["visual"])
    visual["setting"] = setting_id
    for field, slot in (("finish", "area_finishes"), ("wallpaper", "area_wallpapers")):
        chosen_values = {
            str(a): rooms[chosen[a]][field]
            for a in range(case.scene.n_areas)
            if rooms[chosen[a]].get(field)
        }
        if chosen_values:
            visual[slot] = chosen_values
    theme = Theme(
        theme_id=f"{setting_id}-{hashlib.sha256(key.encode()).hexdigest()[:8]}",
        title=pack["titles"][_pick(key + "|title", len(pack["titles"]))],
        names=names,
        pronouns=pronouns,
        areas=areas,
        objects=objects,
        blurb=pack["blurbs"][_pick(key + "|blurb", len(pack["blurbs"]))],
        setting_id=setting_id,
        visual=visual,
    )
    theme.validate(case)
    return theme


RESTYLES_DIR = Path(__file__).resolve().parent / "restyles"


@lru_cache(maxsize=None)
def restyles():
    """Restyle specs by case slug (`setter/restyles/<slug>.json`)."""
    return {
        p.stem: json.loads(p.read_text()) for p in sorted(RESTYLES_DIR.glob("*.json"))
    }


def restyle(case, theme, spec):
    """Draw a case that has its own written theme in a setting pack's casebook look.

    The theme's words stay as written: title, people, rooms, roles, named area groups and every
    noun its clues use. The pack supplies the frame, accent and floor colourways; the spec picks,
    for each prop kind, a drawing that still shows the theme's noun while suiting the setting
    (a museum's "statue" becomes a classical statue, never a sarcophagus for its "bed"), and a
    floor finish, wallpaper and optional colourway for every room by name.
    """
    from murdoku_lab.visual.art import materials, props

    pack = load(spec["look"])
    problems = []
    present = {p.pid for p in case.scene.props}
    for kind, skin in spec.get("skins", {}).items():
        if kind not in present:
            problems.append(f"skin for {kind!r}, which the case does not use")
        if skin not in props.all_skins() and skin not in props.BASE:
            problems.append(f"unknown skin {skin!r}")
    rooms = spec.get("rooms", {})
    names = [theme.area(a) for a in range(case.scene.n_areas)]
    for name in names:
        if name not in rooms:
            problems.append(f"no finish and wallpaper for room {name!r}")
    for name, (finish, wallpaper, *variant) in rooms.items():
        if name not in names:
            problems.append(f"room {name!r} is not on the board")
        if finish not in materials.FINISHES:
            problems.append(f"room {name!r} has unknown finish {finish!r}")
        elif variant and variant[0] not in {
            v[0] for v in materials.FLOOR_VARIANTS[finish]
        }:
            problems.append(
                f"room {name!r} has unknown {finish} colourway {variant[0]!r}"
            )
        try:
            materials.wallpaper_pattern(wallpaper)
        except ValueError:
            problems.append(f"room {name!r} has unknown wallpaper {wallpaper!r}")
    if problems:
        raise ValueError(f"restyle {spec.get('case')!r}: " + "; ".join(problems))
    visual = {
        key: value
        for key, value in pack["visual"].items()
        if key in ("accent", "tints", "finishes", "variants", "frame", "wallpapers")
    }
    visual["setting"] = spec["look"]
    # The spec's finishes come first, so each room gets the floor it names; the pack's own
    # remain as fallbacks when touching rooms would otherwise look alike.
    visual["finishes"] = list(
        dict.fromkeys([room[0] for room in rooms.values()] + visual.get("finishes", []))
    )
    visual["skins"] = dict(spec.get("skins", {}))
    visual["area_finishes"] = {str(a): rooms[n][0] for a, n in enumerate(names)}
    visual["area_wallpapers"] = {str(a): rooms[n][1] for a, n in enumerate(names)}
    visual["area_variants"] = {
        str(a): rooms[n][2] for a, n in enumerate(names) if len(rooms[n]) > 2
    }
    out = dataclasses.replace(theme, setting_id=spec["look"], visual=visual)
    out.validate(case)
    return out


def epilogue(theme, case, murderer, area_id, *, salt=""):
    """Post-solve paragraph: only ever shown after the case is closed."""
    pack = load(theme.setting_id)
    key = f"{theme.theme_id}|{salt}"
    line = pack["epilogues"][_pick(key + "|epilogue", len(pack["epilogues"]))]
    motive = pack["motives"][_pick(key + "|motive", len(pack["motives"]))]
    return line.format(
        murderer=theme.name(murderer).split()[0],
        victim=theme.name(case.victim),
        area=theme.area(area_id),
        motive=motive,
    )
