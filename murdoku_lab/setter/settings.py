"""Setting packs: the words and the look of a case, never its maths.

A setting pack (`setter/settings/<id>.json`) names rooms by the furniture they suit, gives each
formal prop kind a noun and a drawing (its "skin"), and carries the colours, floor finishes and
frame of the casebook art. `dress()` turns a formal case into a `Theme` for one setting and the
recurring cast. The content hash ignores themes, so dressing a case can never change its
solution, certificate or difficulty (tests/test_theme_invariance.py).
"""

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
    objects = pack["objects"]
    missing = [k for k in CLASSIC_KINDS if k not in objects]
    if missing:
        problems.append(f"no noun for {missing}")
    nouns = [v.lower() for v in objects.values()]
    if len(set(nouns)) != len(nouns):
        problems.append("object nouns must be distinct")
    visual = pack["visual"]
    for kind, skin in (visual.get("skins") or {}).items():
        if kind not in OBJECTS:
            problems.append(f"skin for unknown kind {kind!r}")
        if skin not in props.SKINS and skin not in props.BASE:
            problems.append(f"unknown skin {skin!r}")
    for finish in visual.get("finishes") or ():
        if finish not in materials.FINISHES:
            problems.append(f"unknown finish {finish!r}")
    for tint in visual.get("tints") or ():
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", tint):
            problems.append(f"bad tint {tint!r}")
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
    visual["area_finishes"] = {
        str(a): rooms[chosen[a]]["finish"]
        for a in range(case.scene.n_areas)
        if rooms[chosen[a]].get("finish")
    }
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
