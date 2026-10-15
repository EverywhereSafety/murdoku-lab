"""The casebook board: an illustrated floor plan in the Everywhere Safety palette.

Same geometry contract as the legacy renderer (CELL=100, PAD=40, one `g.cell-hit[data-cell]`
per square, axis labels at x=20 / y=25), so the interactive frontends and the exports read it
the same way. Everything is drawn from the public observation; nothing here can see a solution.
"""

from . import labels, materials, props, tokens
from .geometry import (
    CELL,
    PAD,
    by_label,
    colour_areas,
    connected,
    bounds,
    dimensions,
    door_geometry,
    is_outer,
    is_rectangle,
    origin,
    wall_runs,
)
from .palette import ROOM_TINTS, THEMES, mix, night_tint
from .styles import ALL_LAYERS, check_theme
from .svg import esc, num

DEFAULT_FINISHES = (
    "planks",
    "parquet",
    "herringbone",
    "flagstone",
    "carpet",
    "checker",
    "marble",
    "boards",
    "terracotta",
    "paving",
)


def visual_of(observation):
    """The theme's optional visual block, or an empty one."""
    return observation["scene"].get("visual") or {}


def room_tints(observation, theme):
    visual = visual_of(observation)
    tints = tuple(visual.get("tints") or ROOM_TINTS)
    chosen = colour_areas(observation, tints)
    out = {}
    for area in observation["scene"]["areas"]:
        tint = tints[chosen[area["id"]]]
        out[area["id"]] = night_tint(tint) if theme == "night" else tint
    return out


def room_finishes(observation):
    """Decorative floor per area: the theme's choice, else a deterministic cycle, never a
    finish that could be read as one of the board's formal terrains."""
    visual = visual_of(observation)
    terrains = {t["id"] for t in observation["scene"]["terrains"]}
    allowed = [
        f
        for f in (visual.get("finishes") or DEFAULT_FINISHES)
        if not (materials.FINISH_CONFLICTS.get(f, set()) & terrains)
    ] or ["planks"]
    explicit = {int(k): v for k, v in (visual.get("area_finishes") or {}).items()}
    out = {}
    for area in observation["scene"]["areas"]:
        finish = explicit.get(area["id"])
        if finish is None or finish not in allowed:
            finish = allowed[area["id"] % len(allowed)]
        out[area["id"]] = finish
    return out


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
):
    check_theme(theme)
    show = ALL_LAYERS if layers is None else frozenset(layers)
    colours = THEMES[theme]
    scene = observation["scene"]
    width, height = dimensions(observation)
    cells = scene["cells"]
    cells_by_label = by_label(observation)
    areas = {a["id"]: a for a in scene["areas"]}
    tints = room_tints(observation, theme)
    finishes = room_finishes(observation)
    visual = visual_of(observation)
    skins = visual.get("skins") or {}
    terrain_ids = sorted({c["terrain"] for c in cells if c["terrain"] != "floor"})
    finish_strength = 0.85 if export else 1.0
    if theme == "night":
        finish_strength *= 1.6

    defs = [materials.hatch_pattern(colours["blocked"])]
    for name in sorted(set(finishes.values())):
        defs.append(
            materials.finish_pattern(
                name,
                colours["ink"] if theme == "day" else "#f6edd9",
                finish_strength,
            )
        )
    for t in terrain_ids:
        pattern = materials.terrain_pattern(t)
        if pattern:
            defs.append(pattern)
    defs.append(tokens.clip_defs())

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
            f'<rect width="{width}" height="{height}" rx="14" fill="{colours["paper"]}"/>'
        )
        root.append(_frame(observation, colours, visual))
    root.append('<g class="board-decoration">')
    if "floor" in show:
        root.append(_floor(cells, tints, finishes, colours))
    if "terrain" in show:
        root.append(_terrain(cells, cells_by_label, tints, colours, theme))
    if "floor" in show:
        root.append(_grid(observation, colours))
    if "blocked" in show:
        root.append(_blocked_hatch(cells))
    if "walls" in show:
        root.append(_wall_shadows(cells, colours))
    if "props" in show:
        root.append(_props(scene, cells_by_label, skins))
    if "walls" in show:
        root.append(_walls(observation, colours))
    if "doors" in show:
        root.append(_doors(observation, colours, tints))
    if "blocked" in show:
        root.append(_blocked_badges(cells, colours))
    if "plaques" in show:
        root.append(labels.plaques(observation, colours, show_names=True))
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
        root.append(labels.axes(observation, colours))
    root.append("</g>")
    if "hit" in show:
        root.append(
            labels.hit_layer(observation, colours, areas, tabs=cell_labels == "tabs")
        )
    root.append("</svg>")
    return "".join(root)


# ------------------------------------------------------------------------------- layers
def _frame(observation, colours, visual):
    width, height = dimensions(observation)
    x, y, w, h = PAD - 14, PAD - 14, width - 2 * PAD + 28, height - 2 * PAD + 28
    out = [
        f'<rect x="{x + 4}" y="{y + 6}" width="{w}" height="{h}" rx="10" '
        f'fill="{colours["shadow"]}" fill-opacity=".10"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{colours["mat"]}" '
        f'stroke="{colours["ink"]}" stroke-opacity=".55" stroke-width="1.5"/>',
        f'<rect x="{x + 5}" y="{y + 5}" width="{w - 10}" height="{h - 10}" rx="7" fill="none" '
        f'stroke="{colours["brass"]}" stroke-opacity=".7" stroke-width="1.2"/>',
    ]
    return "".join(out)


def _floor(cells, tints, finishes, colours):
    out = []
    for c in cells:
        x, y = origin(c)
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{tints[c["area"]]}"/>'
        )
    for c in cells:
        if c["terrain"] != "floor":
            continue
        x, y = origin(c)
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'fill="url(#{materials.finish_id(finishes[c["area"]])})"/>'
        )
    return "".join(out)


def _terrain(cells, cells_by_label, tints, colours, theme):
    grid = {(c["row"], c["col"]): c for c in cells}
    out = []
    for c in cells:
        t = c["terrain"]
        if t == "floor":
            continue
        x, y = origin(c)
        insets = []
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            n = grid.get((c["row"] + dr, c["col"] + dc))
            same = n is not None and n["terrain"] == t and n["area"] == c["area"]
            insets.append(0 if same else 6)
        top, right, bottom, left = insets
        base = materials.TERRAIN_BASE.get(t)
        if t == "tile":
            base = mix(tints[c["area"]], "#ffffff", 0.45)
        if base is None:
            continue
        if theme == "night":
            base = (
                night_tint(base)
                if t != "tile"
                else mix(tints[c["area"]], "#ffffff", 0.12)
            )
        rx = 6 if any(insets) else 0
        geometry = (
            f'x="{x + left}" y="{y + top}" width="{CELL - left - right}" '
            f'height="{CELL - top - bottom}" rx="{rx}"'
        )
        out.append(f'<rect {geometry} fill="{base}"/>')
        out.append(f'<rect {geometry} fill="url(#{materials.terrain_id(t)})"/>')
    return "".join(out)


def _grid(observation, colours):
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
        f'<path d="{"".join(d)}" fill="none" stroke="{colours["grid"]}" '
        f'stroke-opacity=".13" stroke-width="1" stroke-dasharray="3 4"/>'
    )


def _blocked_hatch(cells):
    out = []
    for c in cells:
        if c["standable"]:
            continue
        x, y = origin(c)
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'fill="url(#{materials.HATCH_ID})"/>'
        )
    return "".join(out)


def _blocked_badges(cells, colours):
    out = []
    for c in cells:
        if c["standable"]:
            continue
        x, y = origin(c)
        cx, cy = x + 14, y + 86
        out.append(
            f'<g class="blocked-mark"><circle cx="{cx}" cy="{cy}" r="7.5" fill="{colours["paper"]}" '
            f'fill-opacity=".95" stroke="{colours["blocked"]}" stroke-width="1.4"/>'
            f'<path d="m{cx - 3} {cy - 3} 6 6m0-6-6 6" stroke="{colours["blocked"]}" '
            f'stroke-width="1.6" stroke-linecap="round"/></g>'
        )
    return "".join(out)


def _wall_shadows(cells, colours):
    out = []
    for c in cells:
        x, y = origin(c)
        for wall in c["walls"]:
            if wall == "north":
                band = (x, y, CELL, 9)
            elif wall == "south":
                band = (x, y + CELL - 5, CELL, 5)
            elif wall == "west":
                band = (x, y, 9, CELL)
            else:
                band = (x + CELL - 5, y, 5, CELL)
            bx, by, bw, bh = band
            out.append(
                f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" '
                f'fill="{colours["shadow"]}" fill-opacity=".07"/>'
            )
    return "".join(out)


def _walls(observation, colours):
    runs = wall_runs(observation)
    out = []
    for run in runs:
        x1, y1, x2, y2 = run
        w = 10 if is_outer(run, observation) else 7.5
        out.append(
            f'<path d="M{x1 + 2} {y1 + 3}L{x2 + 2} {y2 + 3}" stroke="{colours["shadow"]}" '
            f'stroke-opacity=".16" stroke-width="{w + 1.5}" stroke-linecap="round"/>'
        )
    for run in runs:
        x1, y1, x2, y2 = run
        w = 10 if is_outer(run, observation) else 7.5
        out.append(
            f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{colours["wall"]}" '
            f'stroke-width="{w}" stroke-linecap="round"/>'
        )
        out.append(
            f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{colours["wall_light"]}" '
            f'stroke-opacity=".35" stroke-width="1.4"/>'
        )
    return "".join(out)


def _doors(observation, colours, tints):
    out = []
    cells_by_label = by_label(observation)
    for a, b in observation["scene"]["doors"]:
        x, y, vertical_wall = door_geometry(observation, (a, b))
        ca = cells_by_label[a]
        tint = tints[ca["area"]]
        if vertical_wall:
            gap = (
                f'<rect x="{x - 6}" y="{y - 22}" width="12" height="44" fill="{tint}"/>'
            )
            sill = (
                f'<rect x="{x - 4.5}" y="{y - 22}" width="9" height="44" rx="2.5" '
                f'fill="{colours["brass"]}" stroke="{colours["brass_dark"]}" stroke-width="1.4"/>'
            )
            ends = f"M{x - 7} {y - 22}h14M{x - 7} {y + 22}h14"
            swing = f"M{x} {y - 22}A44 44 0 0 1 {x + 30} {y + 10}"
        else:
            gap = (
                f'<rect x="{x - 22}" y="{y - 6}" width="44" height="12" fill="{tint}"/>'
            )
            sill = (
                f'<rect x="{x - 22}" y="{y - 4.5}" width="44" height="9" rx="2.5" '
                f'fill="{colours["brass"]}" stroke="{colours["brass_dark"]}" stroke-width="1.4"/>'
            )
            ends = f"M{x - 22} {y - 7}v14M{x + 22} {y - 7}v14"
            swing = f"M{x - 22} {y}A44 44 0 0 0 {x + 10} {y + 30}"
        out.append(
            f'<g data-door="{esc(a)}:{esc(b)}">{gap}'
            f'<path d="{swing}" fill="none" stroke="{colours["brass_dark"]}" stroke-opacity=".55" '
            f'stroke-width="1.4" stroke-dasharray="3 4"/>{sill}'
            f'<path d="{ends}" stroke="{colours["wall"]}" stroke-width="3" stroke-linecap="round"/></g>'
        )
    return "".join(out)


def _props(scene, cells_by_label, skins):
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
                x, y = PAD + c * CELL, PAD + r * CELL
                fw, fh = ww * CELL - 16, hh * CELL - 18
                drawing = props.draw(kind, fw, fh, skin=skin)
                out.append(
                    f'<g data-prop="{esc(prop["id"])}" transform="translate({x + 8} {y + 10})">'
                    f"{drawing}</g>"
                )
                if kind == "generic":
                    out.append(
                        labels.text(
                            x + ww * CELL / 2,
                            y + hh * CELL - 22,
                            prop["id"][:13],
                            11,
                            "#102725",
                            anchor="middle",
                        )
                    )
    return "".join(out)


__all__ = ["scene_svg", "room_tints", "room_finishes", "num"]
