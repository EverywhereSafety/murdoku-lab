"""The casebook board: a 3/4 dollhouse floor plan.

Rooms have real floors and wallpapered north walls; furniture shows its front; everything is
painted back to front, row by row. The geometry contract is unchanged (CELL=100, PAD=40, one
`g.cell-hit[data-cell]` per square, axis labels at x=20 / y=25), so frontends and exports read
it the same way. Everything is drawn from the public observation; nothing here sees a solution.
"""

from . import frames, labels, materials, props, tokens
from .geometry import (
    CELL,
    PAD,
    area_adjacency,
    bounds,
    by_label,
    connected,
    dimensions,
    door_geometry,
    is_outer,
    is_rectangle,
    origin,
    wall_runs,
)
from .palette import THEMES, delta_e
from .styles import ALL_LAYERS, check_theme
from .svg import esc

FACE = materials.FACE
DEFAULT_FINISHES = (
    "parquet",
    "checker",
    "carpet",
    "planks",
    "herringbone",
    "marble",
    "flagstone",
    "boards",
    "terracotta",
    "paving",
)
OUTDOOR_TERRAIN = {"fairway", "rough", "sand", "water"}
MIN_FLOOR_GAP = 12.0
CAP_DARK = "#2a221d"
CAP_LIGHT = "#e7d6b6"


def visual_of(observation):
    return observation["scene"].get("visual") or {}


def room_styles(observation):
    """Floor material, colour variant and wallpaper per area. Touching rooms differ."""
    scene = observation["scene"]
    visual = visual_of(observation)
    terrains = {t["id"] for t in scene["terrains"]}
    allowed = [
        f
        for f in (visual.get("finishes") or DEFAULT_FINISHES)
        if f in materials.FLOOR_VARIANTS
        and not (materials.FINISH_CONFLICTS.get(f, set()) & terrains)
    ] or ["planks"]
    explicit = {int(k): v for k, v in (visual.get("area_finishes") or {}).items()}
    # A restyled case may also name each room's colourway (setter/restyles/).
    explicit_variant = {
        int(k): v for k, v in (visual.get("area_variants") or {}).items()
    }
    wallpapers = [w for w in (visual.get("wallpapers") or materials.WALLPAPERS)]
    room_papers = {int(k): v for k, v in (visual.get("area_wallpapers") or {}).items()}
    # A setting may prefer some colourways of a finish (green velvet aboard a train, red carpet
    # in a theatre); others remain as a fallback when touching rooms would otherwise match.
    palette = visual.get("variants") or {}
    cells = scene["cells"]
    outdoor = {}
    for area in scene["areas"]:
        own = [c for c in cells if c["area"] == area["id"]]
        outdoor[area["id"]] = sum(
            c["terrain"] in OUTDOOR_TERRAIN for c in own
        ) * 2 > len(own)
    neighbours = {a["id"]: set() for a in scene["areas"]}
    for a, b in area_adjacency(observation):
        neighbours[a].add(b)
        neighbours[b].add(a)
    chosen = {}
    order = sorted(neighbours, key=lambda a: (-len(neighbours[a]), a))
    for area in order:
        used = [chosen[n]["base"] for n in neighbours[area] if n in chosen]
        preferred = explicit.get(area)
        if preferred not in allowed:
            preferred = allowed[area % len(allowed)]
        candidates = [preferred] + [f for f in allowed if f != preferred]
        best = None
        for finish in candidates:
            liked = palette.get(finish)
            wanted = explicit_variant.get(area) if finish == preferred else None
            for name, base, _, _ in materials.FLOOR_VARIANTS[finish]:
                gap = min((delta_e(base, u) for u in used), default=100.0)
                key = (
                    gap >= MIN_FLOOR_GAP,
                    finish == preferred,
                    wanted is None or name == wanted,
                    not liked or name in liked,
                    gap,
                )
                if best is None or key > best[0]:
                    best = (key, finish, name, base)
            if best[0][0] and best[1] == preferred:
                break
        _, finish, name, base = best
        chosen[area] = {
            "finish": finish,
            "variant": name,
            "base": base,
            "wallpaper": (
                "hedge"
                if outdoor[area]
                else room_papers.get(area) or wallpapers[area % len(wallpapers)]
            ),
            "outdoor": outdoor[area],
        }
    return chosen


def room_tints(observation, theme="day"):
    """The colour that identifies each area (its floor), for legends and the overlay."""
    return {a: style["base"] for a, style in room_styles(observation).items()}


def scene_svg(
    observation,
    *,
    theme="day",
    selected=None,
    focus_cells=(),
    layers=None,
    cell_labels="tabs",
    reveal=None,
    export=False,
    backdrop=True,
):
    check_theme(theme)
    show = ALL_LAYERS if layers is None else frozenset(layers)
    colours = THEMES[theme]
    scene = observation["scene"]
    width, height = dimensions(observation)
    cells = scene["cells"]
    cells_by_label = by_label(observation)
    areas = {a["id"]: a for a in scene["areas"]}
    styles = room_styles(observation)
    visual = visual_of(observation)
    skins = visual.get("skins") or {}
    frame = frames.get(visual.get("frame"))
    caps = frame["caps"]
    terrain_ids = sorted({c["terrain"] for c in cells if c["terrain"] != "floor"})

    defs = [
        props.defs(),
        frames.defs(),
        materials.hatch_pattern("#3b2418"),
        tokens.clip_defs(),
    ]
    for style in sorted({(s["finish"], s["variant"]) for s in styles.values()}):
        defs.append(materials.floor_pattern(*style))
    for wp in sorted({s["wallpaper"] for s in styles.values()}):
        defs.append(materials.wallpaper_pattern(wp))
    for t in terrain_ids:
        pattern = materials.terrain_pattern(t)
        if pattern:
            defs.append(pattern)

    root = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" class="scene-svg" data-style="casebook" '
        f'data-theme="{theme}" data-revision="{observation["revision"]}" role="group" '
        f'aria-label="{esc(observation["setting"])}; {scene["width"]} by {scene["height"]} board">',
        "<defs>" + "".join(defs) + "</defs>",
        "<style>"
        'svg[data-style="casebook"] .cell-hit{cursor:pointer;outline:none}'
        'svg[data-style="casebook"] .cell-hit:hover .hit-box{fill:#ffffff38;stroke:#0b7469;stroke-width:2.5}'
        'svg[data-style="casebook"] .cell-hit:focus .hit-box{stroke:#b98a3e;stroke-width:4;fill:#ffffff22}'
        'svg[data-style="casebook"] .board-decoration{pointer-events:none}'
        "</style>",
    ]
    if "paper" in show:
        root.append(
            frames.plinth(observation, colours, visual.get("frame"), backdrop=backdrop)
        )
    root.append('<g class="board-decoration">')
    if "floor" in show:
        root.append(_floors(cells, styles))
    if "terrain" in show:
        root.append(_terrain(cells))
    if "floor" in show:
        root.append(_grid(observation))
    if "blocked" in show:
        root.append(_blocked_hatch(cells))
    if "walls" in show:
        root.append(_wall_occlusion(observation))
    # Painter's order: each row's north wall (face, doorway, cap), then that row's furniture.
    runs = wall_runs(observation)
    door_list = [door_geometry(observation, d) + (d,) for d in scene["doors"]]
    prop_spans = _prop_spans(scene, cells_by_label, skins)
    for r in range(scene["height"]):
        y_top = PAD + r * CELL
        if "walls" in show:
            root.append(_north_faces(observation, styles, runs, y_top))
        if "doors" in show:
            root.append(_face_doorways(door_list, styles, cells_by_label, y_top, caps))
        if "walls" in show:
            root.append(_horizontal_caps(runs, y_top, observation, caps))
        if "doors" in show:
            root.append(_cap_doorways(door_list, y_top, caps))
        if "props" in show:
            for bottom_row, x, y, ww, hh, prop_id, kind, skin in prop_spans:
                if bottom_row == r:
                    root.append(
                        f'<g data-prop="{esc(prop_id)}" transform="translate({x} {y})">'
                        f"{props.draw(kind, ww, hh, skin=skin)}</g>"
                    )
                    if kind == "generic":
                        root.append(
                            labels.text(
                                x + ww / 2,
                                y + hh - 22,
                                prop_id[:13],
                                11,
                                colours["ink"],
                                anchor="middle",
                            )
                        )
    if "walls" in show:
        root.append(_bottom_caps(runs, observation, caps))
        root.append(_vertical_caps(runs, caps))
    if "doors" in show:
        root.append(_side_doorways(door_list, caps))
    if theme == "night":
        root.append(_night(observation))
    if "blocked" in show:
        root.append(_blocked_badges(cells, colours))
    if "plaques" in show:
        root.append(labels.plaques(observation, colours, styles=styles, skins=skins))
    if "notes" in show or "people" in show:
        root.append(
            tokens.cell_layer(
                observation,
                colours,
                selected=selected,
                focus_cells=focus_cells,
                people="people" in show,
                notes="notes" in show,
                reveal=reveal,
            )
        )
    if "axes" in show:
        root.append(
            labels.axes(observation, colours, colour=frame["axis"], halo=frame["halo"])
        )
    root.append("</g>")
    if "hit" in show:
        root.append(
            labels.hit_layer(observation, colours, areas, tabs=cell_labels == "tabs")
        )
    root.append("</svg>")
    return "".join(root)


# ------------------------------------------------------------------------------- layers
def _floors(cells, styles):
    out = []
    for c in cells:
        x, y = origin(c)
        s = styles[c["area"]]
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'fill="url(#{materials.floor_id(s["finish"], s["variant"])})"/>'
        )
    return "".join(out)


def _terrain(cells):
    grid = {(c["row"], c["col"]): c for c in cells}
    out = []
    for c in cells:
        t = c["terrain"]
        if t == "floor" or materials.terrain_pattern(t) is None:
            continue
        x, y = origin(c)
        insets = []
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            n = grid.get((c["row"] + dr, c["col"] + dc))
            same = n is not None and n["terrain"] == t and n["area"] == c["area"]
            insets.append(0 if same else 6)
        top, right, bottom, left = insets
        rx = 7 if any(insets) else 0
        out.append(
            f'<rect x="{x + left}" y="{y + top}" width="{CELL - left - right}" '
            f'height="{CELL - top - bottom}" rx="{rx}" fill="url(#{materials.terrain_id(t)})" '
            f'stroke="#2a221d" stroke-opacity=".25" stroke-width="1.4"/>'
        )
    return "".join(out)


def _grid(observation):
    scene = observation["scene"]
    width, height = dimensions(observation)
    d = []
    for c in range(1, scene["width"]):
        x = PAD + c * CELL
        d.append(f"M{x} {PAD}V{height - PAD}")
    for r in range(1, scene["height"]):
        y = PAD + r * CELL
        d.append(f"M{PAD} {y}H{width - PAD}")
    return (
        f'<path d="{"".join(d)}" fill="none" stroke="#2a221d" stroke-opacity=".16" '
        f'stroke-width="1.2" stroke-dasharray="3 4"/>'
    )


def _blocked_hatch(cells):
    out = []
    for c in cells:
        if c["standable"] or c["prop"]:
            continue
        x, y = origin(c)
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="url(#{materials.HATCH_ID})"/>'
        )
    return "".join(out)


def _blocked_badges(cells, colours):
    out = []
    for c in cells:
        if c["standable"]:
            continue
        x, y = origin(c)
        cx, cy = x + 12, y + 88
        out.append(
            f'<g class="blocked-mark"><circle cx="{cx}" cy="{cy}" r="7.5" fill="#fbf7ee" '
            f'fill-opacity=".92" stroke="#6d5444" stroke-width="1.4"/>'
            f'<path d="m{cx - 3} {cy - 3} 6 6m0-6-6 6" stroke="#6d5444" stroke-width="1.7" '
            f'stroke-linecap="round"/></g>'
        )
    return "".join(out)


def _wall_occlusion(observation):
    out = []
    for x1, y1, x2, y2 in wall_runs(observation):
        if x1 == x2:
            out.append(
                f'<rect x="{x1 - 9}" y="{y1}" width="18" height="{y2 - y1}" fill="#1b130e" '
                f'fill-opacity=".16" filter="url(#mk-softer)"/>'
            )
    return "".join(out)


def _north_faces(observation, styles, runs, y_top):
    """South-facing wallpaper under every horizontal wall at the top of this row."""
    out = []
    cells = {(c["row"], c["col"]): c for c in observation["scene"]["cells"]}
    r = (y_top - PAD) // CELL
    for x1, y1, x2, y2 in runs:
        if y1 != y2 or y1 != y_top or r >= observation["scene"]["height"]:
            continue
        for x in range(x1, x2, CELL):
            c = cells.get((r, (x - PAD) // CELL))
            if c is None:
                continue
            wp = styles[c["area"]]["wallpaper"]
            out.append(
                f'<rect x="{x}" y="{y_top}" width="{CELL}" height="{FACE}" '
                f'fill="url(#{materials.wallpaper_id(wp)})"/>'
            )
            if wp != "hedge":
                out.append(
                    f'<rect x="{x}" y="{y_top + FACE - 7}" width="{CELL}" height="7" fill="#4a3022"/>'
                )
            out.append(
                f'<rect x="{x}" y="{y_top + FACE}" width="{CELL}" height="10" fill="#1b130e" '
                f'fill-opacity=".18" filter="url(#mk-softer)"/>'
                f'<rect x="{x}" y="{y_top}" width="{CELL}" height="5" fill="#1b130e" fill-opacity=".22"/>'
            )
    return "".join(out)


def _face_doorways(door_list, styles, cells_by_label, y_top, caps):
    out = []
    for x, y, vertical_wall, (a, b) in door_list:
        if vertical_wall or y != y_top:
            continue
        upper = min(cells_by_label[a], cells_by_label[b], key=lambda c: c["row"])
        s = styles[upper["area"]]
        floor = f"url(#{materials.floor_id(s['finish'], s['variant'])})"
        out.append(
            f'<g data-door="{esc(a)}:{esc(b)}">'
            f'<rect x="{x - 24}" y="{y}" width="48" height="{FACE}" fill="#3b2a20"/>'
            f'<rect x="{x - 20}" y="{y + 4}" width="40" height="{FACE - 4}" fill="{floor}"/>'
            f'<rect x="{x - 20}" y="{y + 4}" width="40" height="{FACE - 4}" fill="#1b130e" fill-opacity=".3"/>'
            f'<path d="M{x - 24} {y}v{FACE}M{x + 24} {y}v{FACE}" stroke="{caps[0]}" stroke-width="5"/></g>'
        )
    return "".join(out)


def _cap(x1, y1, x2, y2, width=12, caps=(CAP_DARK, CAP_LIGHT)):
    return (
        f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{caps[0]}" stroke-width="{width}" stroke-linecap="square"/>'
        f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{caps[1]}" stroke-width="{width / 2:.0f}" stroke-linecap="square"/>'
    )


def _horizontal_caps(runs, y_top, observation, caps):
    return "".join(
        _cap(
            x1,
            y1,
            x2,
            y2,
            14 if is_outer((x1, y1, x2, y2), observation) else 12,
            caps,
        )
        for x1, y1, x2, y2 in runs
        if y1 == y2 == y_top
    )


def _cap_doorways(door_list, y_top, caps):
    out = []
    for x, y, vertical_wall, (a, b) in door_list:
        if vertical_wall or y != y_top:
            continue
        out.append(
            f'<rect x="{x - 24}" y="{y - 7}" width="48" height="14" fill="#3b2a20"/>'
            f'<path d="M{x - 24} {y - 7}h48" stroke="{caps[0]}" stroke-width="5"/>'
            f'<path d="M{x - 24} {y - 7}v14M{x + 24} {y - 7}v14" stroke="{caps[0]}" stroke-width="5"/>'
        )
    return "".join(out)


def _bottom_caps(runs, observation, caps):
    _, height = dimensions(observation)
    return "".join(
        _cap(x1, y1, x2, y2, 14, caps)
        for x1, y1, x2, y2 in runs
        if y1 == y2 == height - PAD
    )


def _vertical_caps(runs, caps):
    out, light = [], []
    for x1, y1, x2, y2 in runs:
        if x1 != x2:
            continue
        out.append(
            f'<path d="M{x1} {y1 - 6}V{y2 + 6}" stroke="{caps[0]}" stroke-width="12"/>'
        )
        light.append(f'<path d="M{x1} {y1}V{y2}" stroke="{caps[1]}" stroke-width="6"/>')
    return "".join(out + light)


def _side_doorways(door_list, caps):
    out = []
    for x, y, vertical_wall, (a, b) in door_list:
        if not vertical_wall:
            continue
        out.append(
            f'<g data-door="{esc(a)}:{esc(b)}">'
            f'<rect x="{x - 8}" y="{y - 24}" width="16" height="48" fill="#b98a54"/>'
            f'<path d="M{x - 4} {y - 22}v44M{x + 4} {y - 22}v44" stroke="#9a6b3e" stroke-width="1.2"/>'
            f'<path d="M{x - 9} {y - 24}h18M{x - 9} {y + 24}h18" stroke="{caps[0]}" stroke-width="4.5"/></g>'
        )
    return "".join(out)


def _night(observation):
    width, height = dimensions(observation)
    return (
        f'<rect x="{PAD - 6}" y="{PAD - 6}" width="{width - 2 * PAD + 12}" height="{height - 2 * PAD + 12}" '
        f'fill="#0c1a26" fill-opacity=".42"/>'
    )


def _prop_spans(scene, cells_by_label, skins):
    """(bottom row, x, y, w, h, prop id, kind, skin) for every drawing, in left-to-right order."""
    out = []
    for prop in scene["props"]:
        kind = prop["art"]
        skin = skins.get(prop["id"]) or skins.get(kind)
        for group in connected(prop["cells"], cells_by_label):
            r0, c0, h, w = bounds(group)
            if props.stretches(kind, skin) and is_rectangle(group):
                spans = [(r0, c0, h, w)]
            else:
                spans = [(c["row"], c["col"], 1, 1) for c in group]
            for r, c, hh, ww in spans:
                out.append(
                    (
                        r + hh - 1,
                        PAD + c * CELL,
                        PAD + r * CELL,
                        ww * CELL,
                        hh * CELL,
                        prop["id"],
                        kind,
                        skin,
                    )
                )
    return sorted(out, key=lambda p: (p[0], p[1]))
