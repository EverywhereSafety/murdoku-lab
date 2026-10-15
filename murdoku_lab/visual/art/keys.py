"""Casebook exports: the board with its keys, and the full case-file page.

The image alone must carry everything a vision solver needs (areas and numbers, doors, blocked
squares, coordinates, a key naming every prop and terrain), so every key glyph is drawn by the
same drawer, with the same skin, as on the board.
"""

import math
import textwrap

from . import casebook, materials, portraits, props
from .geometry import dimensions
from .palette import THEMES, mix
from .svg import FONT_MONO, FONT_SANS, FONT_SERIF, esc, num, text


def _skin(observation, prop):
    skins = (observation["scene"].get("visual") or {}).get("skins") or {}
    return skins.get(prop["id"]) or skins.get(prop["art"])


def _prop_glyph(observation, prop, x, y, size):
    drawing = props.draw(prop["art"], size, size, skin=_skin(observation, prop))
    return f'<g transform="translate({num(x)} {num(y)})">{drawing}</g>'


def _terrain_swatch(terrain_id, x, y, w, h, colours):
    base = materials.TERRAIN_BASE.get(terrain_id, colours["paper_2"])
    if terrain_id == "tile":
        base = mix(colours["paper_2"], "#ffffff", 0.3)
    out = f'<rect x="{num(x)}" y="{num(y)}" width="{w}" height="{h}" rx="5" fill="{base}" stroke="{colours["ink"]}" stroke-opacity=".35"/>'
    if materials.terrain_pattern(terrain_id):
        out += f'<rect x="{num(x)}" y="{num(y)}" width="{w}" height="{h}" rx="5" fill="url(#{materials.terrain_id(terrain_id)})"/>'
    return out


def _heading(x, y, label, colours, size=15):
    return text(x, y, label.upper(), size, colours["ink"], weight="700", spacing=1.6)


def _key_defs(observation):
    terrains = [t["id"] for t in observation["scene"]["terrains"]]
    defs = [materials.terrain_pattern(t) for t in terrains]
    return "<defs>" + "".join(d for d in defs if d) + "</defs>"


def board_svg(observation, *, theme="day"):
    colours = THEMES[theme]
    bw, bh = dimensions(observation)
    scene = observation["scene"]
    props_list = scene["props"]
    terrains = scene["terrains"]
    columns = max(2, min(4, int(bw // 230)))
    slot = bw / columns
    wrap = max(14, int((slot - 78) / 8))
    row_height = max(
        [82] + [50 + 18 * len(textwrap.wrap(p["name"], wrap)) for p in props_list]
    )
    key_y = bh + 44
    terrain_y = key_y + math.ceil(len(props_list) / columns) * row_height + 32
    height = terrain_y + math.ceil(len(terrains) / columns) * 58 + 56
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{bw}" height="{height}" viewBox="0 0 {bw} {height}" data-style="casebook" data-theme="{theme}">',
        _key_defs(observation),
        f'<rect width="{bw}" height="{height}" fill="{colours["paper"]}"/>',
        casebook.scene_svg(observation, theme=theme, export=True),
        _heading(26, bh + 20, "Object key · crossed squares are blocked", colours),
    ]
    for i, prop in enumerate(props_list):
        x, y = 22 + (i % columns) * slot, key_y + (i // columns) * row_height
        out.append(
            f'<rect x="{num(x)}" y="{num(y - 4)}" width="58" height="58" rx="8" fill="{colours["paper_2"]}" stroke="{colours["ink"]}" stroke-opacity=".18"/>'
        )
        out.append(_prop_glyph(observation, prop, x + 3, y - 1, 52))
        name = (
            f'{prop["id"]} · {prop["name"]}'
            if prop["art"] == "generic"
            else prop["name"]
        )
        lines = textwrap.wrap(name, wrap)
        for j, line in enumerate(lines):
            out.append(
                text(x + 70, y + 16 + j * 18, line, 15, colours["ink"], weight="600")
            )
        out.append(
            text(
                x + 70,
                y + 20 + len(lines) * 18,
                "standable object" if prop["standable"] else "blocking object",
                12.5,
                colours["ink_soft"],
            )
        )
    out.append(
        _heading(26, terrain_y - 14, "Ground key · separate from objects", colours)
    )
    for i, terrain in enumerate(terrains):
        x, y = 24 + (i % columns) * slot, terrain_y + (i // columns) * 58
        out.append(_terrain_swatch(terrain["id"], x, y, 44, 34, colours))
        out.append(
            text(x + 58, y + 15, terrain["name"], 15, colours["ink"], weight="600")
        )
        out.append(
            text(
                x + 58,
                y + 33,
                "standable ground" if terrain["standable"] else "blocked ground",
                12.5,
                colours["ink_soft"],
            )
        )
    out.append(
        text(
            26,
            height - 18,
            f'Board revision {observation["revision"]} · coordinates: column letter + row number',
            13,
            colours["ink_soft"],
            family=FONT_MONO,
        )
    )
    return "".join(out) + "</svg>"


def observation_svg(observation, *, theme="day", selected=None, focus_cells=()):
    """The complete case file: board, rooms, cast, statements, rules and keys."""
    colours = THEMES[theme]
    bw, bh = dimensions(observation)
    left = bw + 64
    side = 540
    width = left + side + 42
    wraps = [(c, textwrap.wrap(c["text"], width=50)) for c in observation["clues"]]
    clue_h = sum(54 + len(lines) * 23 for _, lines in wraps)
    people = observation["people"]
    cast_cols = 6
    cast_rows = math.ceil(len(people) / cast_cols)
    legend_rows = math.ceil(len(observation["scene"]["areas"]) / 3)
    key_columns = 3
    key_cell_width = bw / key_columns
    key_wrap = max(12, int((key_cell_width - 64) / 6.6))
    props_list = observation["scene"]["props"]
    key_row_height = max(
        [70]
        + [
            15
            * len(
                textwrap.wrap(
                    f'{p["id"]} · {p["name"]}' if p["art"] == "generic" else p["name"],
                    key_wrap,
                )
            )
            + 32
            for p in props_list
        ]
    )
    prop_key_height = math.ceil(len(props_list) / key_columns) * key_row_height
    rule_height = max(
        400,
        116
        + sum(len(textwrap.wrap(rule, 58)) * 19 + 12 for rule in observation["rules"]),
    )
    height = max(
        int(210 + bh + cast_rows * 136 + legend_rows * 30 + 140 + prop_key_height),
        205 + clue_h + rule_height + len(observation["scene"]["terrains"]) * 32,
    )
    accents = {p["id"]: p for p in people}
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" data-style="casebook" data-theme="{theme}">',
        _key_defs(observation),
        f'<defs><clipPath id="mk-cast-clip"><circle cx="50" cy="50" r="48"/></clipPath></defs>',
        f'<rect width="{width}" height="{height}" fill="{colours["paper"]}"/>',
        text(
            38,
            40,
            "MURDOKU LAB · THE ILLUSTRATED CASEBOOK",
            12.5,
            colours["accent"],
            weight="700",
            spacing=2.2,
        ),
        text(
            38,
            92,
            observation["title"],
            36,
            colours["ink"],
            family=FONT_SERIF,
            weight="500",
        ),
        text(38, 122, observation["goal"], 15, colours["ink_soft"]),
        text(
            38,
            154,
            f'{observation["scene"]["width"]} × {observation["scene"]["height"]}  ·  {len(people)} people  ·  {observation["variant"]}',
            13,
            colours["ink_muted"],
            family=FONT_MONO,
        ),
        f'<g transform="translate(20 172)">{casebook.scene_svg(observation, theme=theme, selected=selected, focus_cells=focus_cells, export=True)}</g>',
    ]
    tints = casebook.room_tints(observation, theme)
    y = 190 + bh
    for i, area in enumerate(observation["scene"]["areas"]):
        xx, yy = 42 + (i % 3) * (bw / 3), y + (i // 3) * 30
        o.append(
            f'<rect x="{num(xx)}" y="{num(yy - 13)}" width="16" height="16" rx="4" fill="{tints[area["id"]]}" stroke="{colours["ink"]}" stroke-opacity=".4"/>'
        )
        o.append(
            text(
                xx + 25,
                yy,
                f'{area["number"]:02d}  {area["name"]}',
                13.5,
                colours["ink"],
                weight="500",
            )
        )
    y += legend_rows * 30 + 26
    o.append(_heading(42, y, "The people · letters identify every token", colours, 12))
    for i, p in enumerate(people):
        xx, yy = (
            38 + (i % cast_cols) * (bw / cast_cols),
            y + 16 + (i // cast_cols) * 136,
        )
        size = 66
        state = "victim" if p["victim"] else None
        o.append(
            f'<circle cx="{num(xx + 46)}" cy="{num(yy + size / 2)}" r="{size / 2 + 3}" fill="{colours["paper"]}" stroke="{accents[p["id"]].get("accent", colours["ink"])}" stroke-width="3"/>'
            f'<g transform="translate({num(xx + 46 - size / 2)} {num(yy)}) scale({size / 100})"><g clip-path="url(#mk-cast-clip)">{portraits.portrait_for(p, state=state, cast_size=len(people))}</g></g>'
        )
        o.append(
            text(
                xx + 46,
                yy + size + 22,
                f'{p["id"]} · {p["name"]}',
                12.5,
                colours["ink"],
                anchor="middle",
                weight="700",
            )
        )
        label = "VICTIM" if p["victim"] else "SUSPECT"
        if p["tags"]:
            label += " / " + ", ".join(p["tags"])
        o.append(
            text(
                xx + 46,
                yy + size + 39,
                label,
                10,
                colours["evidence_text"] if p["victim"] else colours["ink_muted"],
                anchor="middle",
                weight="600",
                spacing=1.2,
            )
        )
    o.append(
        f'<path d="M{left - 18} 176V{height - 30}" stroke="{colours["ink"]}" stroke-opacity=".15"/>'
    )
    o.append(_heading(left + 10, 196, "Witness statements", colours, 12.5))
    yy = 228
    for clue, lines in wraps:
        o.append(
            text(
                left + 10,
                yy,
                f'{clue["number"]:02d}',
                13,
                colours["brass_dark"],
                weight="700",
                family=FONT_MONO,
            )
        )
        for line in lines:
            o.append(text(left + 46, yy, line, 16, colours["ink"]))
            yy += 23
        yy += 31
    o.append(_heading(left + 10, yy + 9, "Rules and symbols", colours, 12.5))
    yy += 40
    for rule in observation["rules"]:
        for line in textwrap.wrap(rule, 58):
            o.append(text(left + 10, yy, line, 13.5, colours["ink_soft"]))
            yy += 19
        yy += 12
    key_y = y + cast_rows * 136 + 26
    o.append(_heading(42, key_y, "Object key", colours, 12))
    key_y += 26
    for i, prop in enumerate(props_list):
        px, py = (
            38 + (i % key_columns) * key_cell_width,
            key_y + (i // key_columns) * key_row_height,
        )
        o.append(_prop_glyph(observation, prop, px, py - 6, 44))
        name = (
            f'{prop["id"]} · {prop["name"]}'
            if prop["art"] == "generic"
            else prop["name"]
        )
        lines = textwrap.wrap(name, key_wrap)
        for j, line in enumerate(lines):
            o.append(
                text(
                    px + 54, py + 11 + j * 15, line, 12.5, colours["ink"], weight="600"
                )
            )
        o.append(
            text(
                px + 54,
                py + 13 + len(lines) * 15,
                "standable" if prop["standable"] else "blocked",
                10.5,
                colours["ink_muted"],
            )
        )
    yy += 20
    o.append(_heading(left + 10, yy, "Terrain key", colours, 12.5))
    yy += 28
    for terrain in observation["scene"]["terrains"]:
        o.append(_terrain_swatch(terrain["id"], left + 12, yy - 15, 30, 22, colours))
        o.append(
            text(
                left + 54,
                yy,
                f'{terrain["name"]} · {"standable" if terrain["standable"] else "blocked"}',
                13,
                colours["ink"],
            )
        )
        yy += 32
    o.append(
        text(
            38,
            height - 28,
            f'Observation revision {observation["revision"]} · Cross = blocked · Letters = your pencil marks · No hidden solution included',
            11.5,
            colours["ink_muted"],
            family=FONT_MONO,
        )
    )
    o.append("</svg>")
    return "".join(o)


__all__ = ["board_svg", "observation_svg", "esc", "FONT_SANS"]
