"""Room plaques, board axes and the accessible hit layer of the casebook board."""

from .geometry import CELL, PAD, by_label, connected, dimensions, origin
from .svg import FONT_MONO, FONT_SANS, esc, num, text

# Average advance of an uppercase DM Sans glyph at 1px, with the plaque's letter spacing.
UPPER_ADVANCE = 0.68
PLAQUE_SIZE = 10.5
PLAQUE_SPACING = 0.7


def plaque_width(name, size=PLAQUE_SIZE):
    return len(name) * (size * UPPER_ADVANCE + PLAQUE_SPACING)


def plaque_anchors(observation):
    """Where each connected patch of an area is labelled: a nameplate hung on the patch's top
    wall, over its longest run of top-row squares. Hung on the wall it never sits on top of
    furniture or a person. Returns one dict per patch."""
    cells_by_label = by_label(observation)
    out = []
    for area in observation["scene"]["areas"]:
        members = [
            c["cell"] for c in observation["scene"]["cells"] if c["area"] == area["id"]
        ]
        for group in connected(members, cells_by_label):
            top = min(c["row"] for c in group)
            cols = sorted(c["col"] for c in group if c["row"] == top)
            best, run_start, prev = (cols[0], 1), cols[0], cols[0]
            for col in cols[1:] + [None]:
                if col is not None and col == prev + 1:
                    prev = col
                    continue
                length = prev - run_start + 1
                if length > best[1]:
                    best = (run_start, length)
                if col is not None:
                    run_start = prev = col
            start_col, run = best
            start = next(c for c in group if c["row"] == top and c["col"] == start_col)
            x, y = origin(start)
            out.append(
                {
                    "area": area["id"],
                    "number": area["number"],
                    "name": area["name"],
                    "cell": start["cell"],
                    "x": x + 9,
                    "y": y - 7,
                    "available": run * CELL - 18,
                }
            )
    return out


def plaques(observation, colours, *, show_names=True):
    out = []
    for anchor in plaque_anchors(observation):
        name = anchor["name"].upper()
        number = f'{anchor["number"]:02d}'
        x, y = anchor["x"], anchor["y"]
        full = 26 + plaque_width(name) + 9
        with_name = show_names and full <= anchor["available"]
        w = full if with_name else 22
        out.append(
            f'<g class="room-plaque" data-area="{anchor["area"]}">'
            f'<rect x="{num(x + 1.5)}" y="{num(y + 2)}" width="{num(w)}" height="21" rx="10.5" '
            f'fill="{colours["shadow"]}" fill-opacity=".12"/>'
            f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="21" rx="10.5" '
            f'fill="{colours["paper"]}" fill-opacity=".96" stroke="{colours["wall"]}" '
            f'stroke-opacity=".55" stroke-width="1.1"/>'
            f'<circle cx="{num(x + 10.5)}" cy="{num(y + 10.5)}" r="8.2" fill="{colours["wall"]}"/>'
            + text(
                x + 10.5,
                y + 14.2,
                number,
                9.5,
                colours["paper"],
                anchor="middle",
                weight="600",
                family=FONT_MONO,
            )
        )
        if with_name:
            out.append(
                text(
                    x + 25,
                    y + 14.4,
                    name,
                    PLAQUE_SIZE,
                    colours["ink"],
                    weight="700",
                    spacing=PLAQUE_SPACING,
                )
            )
        out.append("</g>")
    return "".join(out)


def axes(observation, colours):
    scene = observation["scene"]
    width, height = dimensions(observation)
    out = []
    for c in range(scene["width"]):
        letter = chr(97 + c).upper()
        x = PAD + c * CELL + 50
        # The Lab locates axis labels by x === 20 and y === 25; keep those exact positions.
        out.append(
            text(
                x,
                25,
                letter,
                13,
                colours["ink_soft"],
                anchor="middle",
                weight="600",
                family=FONT_MONO,
            )
        )
        out.append(
            text(
                x,
                height - 14,
                letter,
                13,
                colours["ink_soft"],
                anchor="middle",
                weight="600",
                family=FONT_MONO,
            )
        )
    for r in range(scene["height"]):
        y = PAD + r * CELL + 55
        out.append(
            text(
                20,
                y,
                r + 1,
                13,
                colours["ink_soft"],
                anchor="middle",
                weight="600",
                family=FONT_MONO,
            )
        )
        out.append(
            text(
                width - 20,
                y,
                r + 1,
                13,
                colours["ink_soft"],
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
