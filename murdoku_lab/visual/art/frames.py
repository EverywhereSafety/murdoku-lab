"""Board frames: the plinth around the floor plan, dressed per setting.

A frame owns the band between the paper edge and the board (10–40px), the colour the axis
labels are engraved in, and the two colours of the wall caps, so a setting reads at a glance
from the outside in. Ornaments only ever sit at cell boundaries or in the corner squares: the
axis labels live at cell centres in the middle of each band, and nothing may cover them.
"""

import math

from .geometry import CELL, PAD, dimensions

MARGIN = 10

GRADIENTS = {
    "fr-walnut": ("#7a4d33", "#5a3826"),
    "fr-hull": ("#30506f", "#1b3049"),
    "fr-gilt": ("#e5c272", "#b08636"),
    "fr-velvet": ("#a3283a", "#6c1424"),
    "fr-log": ("#8a5a37", "#6c4529"),
    "fr-iron": ("#f3f5ef", "#d6ded4"),
    "fr-livery": ("#2f5c48", "#1d3b2e"),
    "fr-leather": ("#7d3030", "#561d21"),
}

# name -> fill gradient, outline, inner rim, axis ink and the halo that keeps it legible over
# furniture rising into the band, wall caps (dark, light)
FRAMES = {
    "manor": {
        "fill": "fr-walnut",
        "edge": "#2a221d",
        "rim": "#b07a52",
        "axis": "#f3e3c3",
        "halo": "#3a2416",
        "caps": ("#2a221d", "#e7d6b6"),
    },
    "liner": {
        "fill": "fr-hull",
        "edge": "#13212f",
        "rim": "#e9e4d8",
        "axis": "#f4efe2",
        "halo": "#13212f",
        "caps": ("#1d2b38", "#f1eee6"),
    },
    "museum": {
        "fill": "fr-gilt",
        "edge": "#6b4c1c",
        "rim": "#fff1c4",
        "axis": "#24170a",
        "halo": "#f6dc94",
        "caps": ("#2a221d", "#efe9dc"),
    },
    "theatre": {
        "fill": "fr-velvet",
        "edge": "#3d0a12",
        "rim": "#e2c27a",
        "axis": "#f9e8c6",
        "halo": "#4a0c16",
        "caps": ("#1f1416", "#dcc8a6"),
    },
    "chalet": {
        "fill": "fr-log",
        "edge": "#3a2416",
        "rim": "#c2925f",
        "axis": "#fbefdc",
        "halo": "#3a2416",
        "caps": ("#2a1d14", "#ead9bd"),
    },
    "glasshouse": {
        "fill": "fr-iron",
        "edge": "#4f6b5f",
        "rim": "#7fa392",
        "axis": "#2a463b",
        "halo": "#f3f5ef",
        "caps": ("#3b5249", "#f4f6f1"),
    },
    "train": {
        "fill": "fr-livery",
        "edge": "#0f2219",
        "rim": "#d9b866",
        "axis": "#f6e7c1",
        "halo": "#0f2219",
        "caps": ("#1d2a22", "#e9dcc0"),
    },
    "library": {
        "fill": "fr-leather",
        "edge": "#33100f",
        "rim": "#d9b45f",
        "axis": "#f3dfae",
        "halo": "#33100f",
        "caps": ("#2a1d16", "#e7d6b6"),
    },
}
DEFAULT = "manor"


def get(name):
    return FRAMES.get(name or DEFAULT, FRAMES[DEFAULT])


def defs():
    return "".join(
        f'<linearGradient id="mk-g-{name}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>'
        for name, (top, bottom) in GRADIENTS.items()
    )


def _boundaries(observation):
    """Ornament anchors at cell boundaries along the four bands (never at label positions)."""
    scene = observation["scene"]
    width, height = dimensions(observation)
    band = (MARGIN + PAD) / 2
    out = []
    for c in range(1, scene["width"]):
        x = PAD + c * CELL
        out += [("top", x, band), ("bottom", x, height - band)]
    for r in range(1, scene["height"]):
        y = PAD + r * CELL
        out += [("left", band, y), ("right", width - band, y)]
    return out


def _corners(observation):
    width, height = dimensions(observation)
    band = (MARGIN + PAD) / 2
    return [
        (band, band),
        (width - band, band),
        (band, height - band),
        (width - band, height - band),
    ]


def _rivet(x, y, colour="#c9d3dc"):
    return (
        f'<circle cx="{x}" cy="{y}" r="2.6" fill="{colour}" stroke="#13212f" stroke-width="1"/>'
        f'<circle cx="{x - 0.8}" cy="{y - 0.8}" r="0.9" fill="#ffffff" fill-opacity=".7"/>'
    )


def _porthole(x, y):
    return (
        f'<circle cx="{x}" cy="{y}" r="9" fill="#e2c27a" stroke="#13212f" stroke-width="1.6"/>'
        f'<circle cx="{x}" cy="{y}" r="5.6" fill="#7fb2c9" stroke="#13212f" stroke-width="1.2"/>'
        f'<path d="M{x - 3} {y - 2}q2 -2 5 -1" stroke="#ffffff" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
    )


def _rosette(x, y, gold="#f3d68c", ink="#6b4c1c"):
    petals = "".join(
        f'<ellipse cx="{x + 5 * math.cos(math.radians(a)):.1f}" cy="{y + 5 * math.sin(math.radians(a)):.1f}" '
        f'rx="3.6" ry="2.2" transform="rotate({a} {x + 5 * math.cos(math.radians(a)):.1f} '
        f'{y + 5 * math.sin(math.radians(a)):.1f})"/>'
        for a in range(0, 360, 45)
    )
    return (
        f'<g fill="{gold}" stroke="{ink}" stroke-width=".9">{petals}</g>'
        f'<circle cx="{x}" cy="{y}" r="3" fill="{gold}" stroke="{ink}" stroke-width="1"/>'
    )


def _bulb(x, y, r=4.2):
    return (
        f'<circle cx="{x}" cy="{y}" r="{r + 4}" fill="#ffd56b" fill-opacity=".28"/>'
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff1c2" stroke="#7a5a1c" stroke-width="1.1"/>'
        f'<circle cx="{x - r * 0.35:.1f}" cy="{y - r * 0.35:.1f}" r="{r * 0.35:.1f}" fill="#ffffff"/>'
    )


def _log_end(x, y):
    return (
        f'<circle cx="{x}" cy="{y}" r="10" fill="#e3b985" stroke="#3a2416" stroke-width="1.6"/>'
        f'<circle cx="{x}" cy="{y}" r="6.5" fill="none" stroke="#b9895a" stroke-width="1.2"/>'
        f'<circle cx="{x}" cy="{y}" r="3" fill="none" stroke="#b9895a" stroke-width="1.2"/>'
    )


def _snow(observation):
    width, _ = dimensions(observation)
    x, d = MARGIN + 4, [f"M{MARGIN + 2} {MARGIN + 3}"]
    i = 0
    while x < width - MARGIN - 4:
        step = 22 + (i * 7) % 12
        nx = min(x + step, width - MARGIN - 4)
        dip = 3 + (i * 5) % 4
        d.append(f"Q{(x + nx) / 2:.1f} {MARGIN + dip + 3} {nx:.1f} {MARGIN + 3}")
        x, i = nx, i + 1
    d.append(
        f"L{width - MARGIN - 2} {MARGIN - 2}Q{width / 2:.1f} {MARGIN - 7} {MARGIN + 2} {MARGIN - 2}Z"
    )
    return f'<path d="{"".join(d)}" fill="#fbfdff" stroke="#9fb6c8" stroke-width="1.4" stroke-linejoin="round"/>'


def _bolt(x, y):
    return (
        f'<circle cx="{x}" cy="{y}" r="3" fill="#cfdad3" stroke="#4f6b5f" stroke-width="1.1"/>'
        f'<path d="M{x - 1.6} {y}h3.2" stroke="#4f6b5f" stroke-width="1"/>'
    )


def _scroll(x, y):
    return (
        f'<path d="M{x - 8} {y + 6}q0 -12 8 -12q7 0 7 7q0 5 -5 5q-4 0 -4 -4" fill="none" '
        f'stroke="#4f6b5f" stroke-width="2.2" stroke-linecap="round"/>'
    )


def _wheel(x, y, r=10):
    spokes = "".join(
        f'<path d="M{x} {y}L{x + r * 0.8 * math.cos(math.radians(a)):.1f} {y + r * 0.8 * math.sin(math.radians(a)):.1f}"/>'
        for a in range(0, 360, 45)
    )
    return (
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#1c1f22" stroke="#0b0d0e" stroke-width="1.4"/>'
        f'<circle cx="{x}" cy="{y}" r="{r - 2.4}" fill="#3a4045"/>'
        f'<g stroke="#9aa3a8" stroke-width="1.3">{spokes}</g>'
        f'<circle cx="{x}" cy="{y}" r="2.4" fill="#d9b866"/>'
    )


def _lamp(x, y):
    return (
        f'<rect x="{x - 5}" y="{y - 7}" width="10" height="13" rx="2.5" fill="#d9b866" stroke="#0f2219" stroke-width="1.2"/>'
        f'<rect x="{x - 3}" y="{y - 4}" width="6" height="7" rx="1.5" fill="#fff1c2"/>'
    )


def _fleuron(x, y, gold="#d9b45f", ink="#33100f"):
    return (
        f'<path d="M{x} {y - 8}L{x + 4} {y}L{x} {y + 8}L{x - 4} {y}Z M{x - 8} {y}L{x} {y - 3}L{x + 8} {y}L{x} {y + 3}Z" '
        f'fill="{gold}" stroke="{ink}" stroke-width=".9"/>'
    )


def _ornaments(name, observation):
    edges, corners = _boundaries(observation), _corners(observation)
    if name == "manor":
        return "".join(_rosette(x, y, "#e2c27a", "#2a221d") for x, y in corners)
    if name == "liner":
        return "".join(_rivet(x, y) for _, x, y in edges) + "".join(
            _porthole(x, y) for x, y in corners
        )
    if name == "museum":
        return "".join(_rosette(x, y) for x, y in corners) + "".join(
            f'<circle cx="{x}" cy="{y}" r="2.2" fill="#fff1c4" stroke="#6b4c1c" stroke-width=".9"/>'
            for _, x, y in edges
        )
    if name == "theatre":
        return "".join(_bulb(x, y) for _, x, y in edges) + "".join(
            _bulb(x, y, 5.6) for x, y in corners
        )
    if name == "chalet":
        return _snow(observation) + "".join(_log_end(x, y) for x, y in corners[2:])
    if name == "glasshouse":
        return "".join(_bolt(x, y) for _, x, y in edges) + "".join(
            _scroll(x, y) for x, y in corners
        )
    if name == "train":
        return "".join(
            _wheel(x, y) for side, x, y in edges if side == "bottom"
        ) + "".join(_lamp(x, y) for x, y in corners)
    if name == "library":
        return "".join(_fleuron(x, y) for x, y in corners)
    return ""


def plinth(observation, colours, name=None, *, backdrop=True):
    """The paper, the frame's drop shadow, the frame band and the board's dark inset.
    `backdrop=False` leaves the corners transparent for pages with their own background.
    """
    spec = get(name)
    key = name if name in FRAMES else DEFAULT
    width, height = dimensions(observation)
    m = MARGIN
    x, y, w, h = m, m, width - 2 * m, height - 2 * m
    out = [
        (
            f'<rect width="{width}" height="{height}" fill="{colours["paper"]}"/>'
            if backdrop
            else ""
        ),
        f'<rect x="{x + 4}" y="{y + 8}" width="{w}" height="{h}" rx="16" fill="#1b130e" fill-opacity=".22" filter="url(#mk-soft)"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="url(#mk-g-{spec["fill"]})" stroke="{spec["edge"]}" stroke-width="2.4"/>',
        f'<rect x="{x + 5}" y="{y + 5}" width="{w - 10}" height="{h - 10}" rx="12" fill="none" stroke="{spec["rim"]}" stroke-width="1.6" stroke-opacity=".8"/>',
    ]
    if key == "library":
        out.append(
            f'<rect x="{x + 9}" y="{y + 9}" width="{w - 18}" height="{h - 18}" rx="9" fill="none" '
            f'stroke="{spec["rim"]}" stroke-width="1.2" stroke-dasharray="1.5 3.5" stroke-opacity=".9"/>'
        )
    if key == "train":
        out.append(
            f'<rect x="{x + 9}" y="{y + 9}" width="{w - 18}" height="{h - 18}" rx="9" fill="none" '
            f'stroke="{spec["rim"]}" stroke-width="1" stroke-opacity=".7"/>'
        )
    if key == "chalet":
        grain = "".join(
            f'<path d="M{x + 18} {yy}H{x + w - 18}" stroke="#5a3a22" stroke-width="1" stroke-opacity=".35"/>'
            for yy in (y + 8, y + 20, height - m - 8, height - m - 20)
        )
        out.append(grain)
    out.append(_ornaments(key, observation))
    out.append(
        f'<rect x="{PAD - 4}" y="{PAD - 4}" width="{width - 2 * PAD + 8}" height="{height - 2 * PAD + 8}" rx="3" fill="#1b130e" fill-opacity=".35"/>'
    )
    return "".join(out)
