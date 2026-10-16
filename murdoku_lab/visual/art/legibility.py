"""Legibility gate for casebook vision exports.

Exported boards are read by vision models, so the art must stay legible whatever a setting
draws: every prop on the board appears in the key under its name, every area carries its
number, coordinates stay readable at the export resolutions, text meets WCAG AA contrast and
touching rooms have clearly different floors. `glyph_distances` adds the pixel check that no two
objects of one setting look alike (scripts/check_vision_legibility.py runs it per setting).

    findings = check(observation)    # {"problems": [...], "metrics": {...}}; no problems = pass
"""

import struct
import zlib

from . import casebook, frames, labels, props
from .geometry import area_adjacency, dimensions
from .keys import board_svg
from .palette import THEMES, contrast, delta_e
from .svg import esc

MIN_TEXT_CONTRAST = 4.5
MIN_FLOOR_DELTA_E = 10.0
MIN_AXIS_PX = 9.0
EXPORT_WIDTHS = (1568, 1024)
AXIS_FONT = 13
# Brass and wood plates behind plaque names (the props gradients).
PLATES = {"brass": ("#e2c27a", "#b58a3c"), "wood": ("#dcab75", "#b9824f")}
PLAQUE_NAME = labels.PLAQUE_INK
PLAQUE_NUMBER = labels.PLAQUE_NUMBER


def check(observation, *, theme="day"):
    problems, metrics = [], {}
    scene = observation["scene"]
    visual = scene.get("visual") or {}
    frame = frames.get(visual.get("frame"))

    top, bottom = frames.GRADIENTS[frame["fill"]]
    axis = min(contrast(frame["axis"], top), contrast(frame["axis"], bottom))
    halo = min(contrast(frame["axis"], frame["halo"]), 21)
    metrics["axis_contrast"] = round(axis, 2)
    metrics["axis_halo_contrast"] = round(halo, 2)
    if axis < MIN_TEXT_CONTRAST:
        problems.append(f"axis labels {frame['axis']} on frame reach only {axis:.2f}:1")
    if halo < MIN_TEXT_CONTRAST:
        problems.append(f"axis halo {frame['halo']} reaches only {halo:.2f}:1")
    for plate, stops in PLATES.items():
        value = min(contrast(PLAQUE_NAME, c) for c in stops)
        metrics[f"plaque_{plate}_contrast"] = round(value, 2)
        if value < MIN_TEXT_CONTRAST:
            problems.append(f"plaque names on {plate} reach only {value:.2f}:1")
    number = contrast(*PLAQUE_NUMBER)
    if number < MIN_TEXT_CONTRAST:
        problems.append(f"plaque numbers reach only {number:.2f}:1")

    styles = casebook.room_styles(observation)
    gaps = [
        delta_e(styles[a]["base"], styles[b]["base"])
        for a, b in area_adjacency(observation)
    ]
    metrics["min_floor_delta_e"] = round(min(gaps), 1) if gaps else None
    if gaps and min(gaps) < MIN_FLOOR_DELTA_E:
        problems.append(f"touching floors only ΔE00 {min(gaps):.1f} apart")

    anchors = labels.plaque_anchors(observation, visual.get("skins"))
    unmarked = sorted({a["id"] for a in scene["areas"]} - {p["area"] for p in anchors})
    if unmarked:
        problems.append(f"areas without a plaque: {unmarked}")

    width, _ = dimensions(observation)
    for target in EXPORT_WIDTHS:
        px = AXIS_FONT * min(1.0, target / width)
        metrics[f"axis_px_at_{target}"] = round(px, 1)
        if px < MIN_AXIS_PX:
            problems.append(f"coordinates shrink to {px:.1f}px at {target}px wide")

    svg = board_svg(observation, theme=theme)
    for prop in scene["props"]:
        if esc(prop["name"]) not in svg:
            problems.append(
                f"prop {prop['id']} ({prop['name']}) is missing from the key"
            )
        if f'data-prop="{esc(prop["id"])}"' not in svg:
            problems.append(f"prop {prop['id']} is not drawn on the board")
    metrics["svg_bytes"] = len(svg.encode())
    return {"problems": problems, "metrics": metrics}


# ----------------------------------------------------------------- glyph distinctness
GLYPH = 48
GRID = 16


def glyph_sheet(items):
    """One SVG with each (kind, skin) glyph in its own GLYPH×GLYPH square, left to right."""
    w = GLYPH * len(items)
    body = "".join(
        f'<g transform="translate({i * GLYPH} 0)">{props.glyph(kind, GLYPH, skin=skin)}</g>'
        for i, (kind, skin) in enumerate(items)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{GLYPH}">'
        f'<defs>{props.defs()}</defs><rect width="{w}" height="{GLYPH}" fill="#d9b07c"/>{body}</svg>'
    )


def decode_png(data):
    """RGBA rows from an 8-bit RGB(A) PNG (what resvg writes); stdlib only."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")
    pos, idat, width = 8, b"", 0
    channels = 4
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos : pos + 8])
        chunk = data[pos + 8 : pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour = struct.unpack(">IIBB", chunk[:10])
            if depth != 8 or colour not in (2, 6):
                raise ValueError("only 8-bit RGB/RGBA PNGs are supported")
            channels = 4 if colour == 6 else 3
        elif kind == b"IDAT":
            idat += chunk
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * channels
    rows, previous = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1 : start + 1 + stride])
        for i in range(stride):
            left = line[i - channels] if i >= channels else 0
            up = previous[i]
            corner = previous[i - channels] if i >= channels else 0
            if kind == 1:
                line[i] = (line[i] + left) & 255
            elif kind == 2:
                line[i] = (line[i] + up) & 255
            elif kind == 3:
                line[i] = (line[i] + (left + up) // 2) & 255
            elif kind == 4:
                p = left + up - corner
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - corner)
                pred = left if pa <= pb and pa <= pc else up if pb <= pc else corner
                line[i] = (line[i] + pred) & 255
        rows.append(bytes(line))
        previous = line
    return width, height, channels, rows


def _features(rows, channels, x0):
    """A coarse GRID×GRID colour signature of one glyph square."""
    step = GLYPH // GRID
    out = []
    for gy in range(GRID):
        for gx in range(GRID):
            acc = [0, 0, 0]
            for dy in range(step):
                row = rows[gy * step + dy]
                for dx in range(step):
                    i = (x0 + gx * step + dx) * channels
                    acc[0] += row[i]
                    acc[1] += row[i + 1]
                    acc[2] += row[i + 2]
            out.extend(v / (step * step * 255) for v in acc)
    return out


def glyph_distances(items, png):
    """For each glyph, its nearest other glyph and the RMS distance between their signatures."""
    _, _, channels, rows = decode_png(png)
    feats = [_features(rows, channels, i * GLYPH) for i in range(len(items))]
    out = []
    for i, a in enumerate(feats):
        best = None
        for j, b in enumerate(feats):
            if i == j:
                continue
            d = (sum((p - q) ** 2 for p, q in zip(a, b)) / len(a)) ** 0.5
            if best is None or d < best[1]:
                best = (j, d)
        out.append((i, best[0], best[1]))
    return out
