"""Room plaques, board axes and the accessible hit layer of the casebook board."""

from .geometry import CELL, PAD, by_label, connected, dimensions, origin
from .svg import FONT_MONO, FONT_SANS, esc, num, text

# Average advance of an uppercase DM Sans glyph at 1px, with the plaque's letter spacing.
UPPER_ADVANCE = 0.68
PLAQUE_SIZE = 10.5
PLAQUE_SPACING = 0.7
# Axis labels are engraved on the wooden plinth around the board.
AXIS = "#f3e3c3"


def plaque_width(name, size=PLAQUE_SIZE):
    return len(name) * (size * UPPER_ADVANCE + PLAQUE_SPACING)


def plaque_anchors(observation, skins=None):
    """Where each connected patch of an area is labelled: a nameplate on the wallpaper of its
    north wall, over the longest run of top-row squares, preferring squares with no tall
    furniture in front of the wall. Returns one dict per patch."""
    from . import props

    skins = skins or {}
    cells_by_label = by_label(observation)
    prop_kind = {p["id"]: p["art"] for p in observation["scene"]["props"]}
    out = []
    for area in observation["scene"]["areas"]:
        members = [
            c["cell"] for c in observation["scene"]["cells"] if c["area"] == area["id"]
        ]
        for group in connected(members, cells_by_label):
            top = min(c["row"] for c in group)
            row = sorted((c for c in group if c["row"] == top), key=lambda c: c["col"])

            def tall(c):
                pid = c["prop"]
                if not pid:
                    return False
                kind = prop_kind.get(pid, "generic")
                return props.is_tall(kind, skins.get(pid) or skins.get(kind))

            runs, current = [], [row[0]]
            for c in row[1:]:
                if c["col"] == current[-1]["col"] + 1:
                    current.append(c)
                else:
                    runs.append(current)
                    current = [c]
            runs.append(current)
            best = max(runs, key=len)
            start = next((c for c in best if not tall(c)), best[0])
            run = len([c for c in best if c["col"] >= start["col"]])
            needed = 24 + plaque_width(area["name"].upper(), 9.5) + 10
            if run * CELL - 16 < needed:
                # Rather than lose the name, hang the plate in front of the furniture.
                start, run = best[0], len(best)
            x, y = origin(start)
            out.append(
                {
                    "area": area["id"],
                    "number": area["number"],
                    "name": area["name"],
                    "cell": start["cell"],
                    "x": x + 8,
                    "y": y + 5,
                    "available": run * CELL - 16,
                }
            )
    return out


def plaques(observation, colours, *, styles=None, skins=None, show_names=True):
    out = []
    for anchor in plaque_anchors(observation, skins):
        name = anchor["name"].upper()
        number = f'{anchor["number"]:02d}'
        x, y = anchor["x"], anchor["y"]
        full = 24 + plaque_width(name, 9.5) + 10
        with_name = show_names and full <= anchor["available"]
        w = full if with_name else 22
        outdoor = bool(styles and styles[anchor["area"]]["outdoor"])
        plate = "url(#mk-g-wood)" if outdoor else "url(#mk-g-brass)"
        out.append(
            f'<g class="room-plaque" data-area="{anchor["area"]}">'
            f'<rect x="{num(x + 1.5)}" y="{num(y + 2)}" width="{num(w)}" height="17" rx="3.5" '
            f'fill="#1b130e" fill-opacity=".3"/>'
            f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="17" rx="3.5" fill="{plate}" '
            f'stroke="#2a221d" stroke-width="1.4"/>'
            f'<rect x="{num(x + 2.5)}" y="{num(y + 2.5)}" width="17" height="12" rx="2.5" fill="#2a221d"/>'
            + text(
                x + 11,
                y + 12.2,
                number,
                9,
                "#f3e3c3",
                anchor="middle",
                weight="600",
                family=FONT_MONO,
            )
        )
        if with_name:
            out.append(
                text(
                    x + 24,
                    y + 12.4,
                    name,
                    9.5,
                    "#3a2a15",
                    weight="700",
                    spacing=PLAQUE_SPACING,
                )
            )
        out.append("</g>")
    return "".join(out)


def axes(observation, colours):
    """Column letters and row numbers engraved on the plinth. The Lab locates axis labels by
    x === 20 and y === 25, so those exact positions are kept."""
    scene = observation["scene"]
    width, height = dimensions(observation)
    out = []
    for c in range(scene["width"]):
        letter = chr(97 + c).upper()
        x = PAD + c * CELL + 50
        for y in (25, height - 15):
            out.append(
                text(
                    x,
                    y,
                    letter,
                    13,
                    AXIS,
                    anchor="middle",
                    weight="600",
                    family=FONT_MONO,
                )
            )
    for r in range(scene["height"]):
        y = PAD + r * CELL + 55
        for x in (20, width - 20):
            out.append(
                text(
                    x,
                    y,
                    r + 1,
                    13,
                    AXIS,
                    anchor="middle",
                    weight="600",
                    family=FONT_MONO,
                )
            )
    return "".join(out)


def hit_layer(observation, colours, areas, *, tabs=True):
    props = {p["id"]: p for p in observation["scene"]["props"]}
    cast = {p["id"]: p for p in observation["people"]}
    out = []
    for c in observation["scene"]["cells"]:
        x, y = origin(c)
        who = [
            cast[p]["name"]
            for p, k in observation["placements"].items()
            if k == c["cell"]
        ]
        details = f'{c["cell"]}; area {c["area"] + 1}, {areas[c["area"]]["name"]}; {c["terrain"]}; '
        if c["prop"]:
            details += props[c["prop"]]["name"] + "; "
        details += "standable" if c["standable"] else "blocked"
        if who:
            details += "; placed: " + ", ".join(who)
        out.append(
            f'<g class="cell-hit" data-cell="{c["cell"]}" role="button" tabindex="0" '
            f'aria-label="{esc(details)}"><title>{esc(details)}</title>'
            f'<rect class="hit-box" x="{x + 3}" y="{y + 3}" width="94" height="94" rx="4" fill="transparent"/>'
        )
        if tabs:
            out.append(
                f'<rect x="{x + 71}" y="{y + 80}" width="25" height="16" rx="4" '
                f'fill="{colours["paper"]}" fill-opacity=".86" pointer-events="none"/>'
            )
            out.append(
                text(
                    x + 83.5,
                    y + 92,
                    c["cell"],
                    10,
                    colours["ink_soft"],
                    anchor="middle",
                    family=FONT_MONO,
                    weight="500",
                    pointer_events="none",
                )
            )
        out.append("</g>")
    return "".join(out)


__all__ = ["plaques", "plaque_anchors", "axes", "hit_layer", "text", "FONT_SANS"]
