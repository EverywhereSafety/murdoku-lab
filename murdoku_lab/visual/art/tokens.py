"""People and notes on the casebook board.

Token geometry is shared with the player app's overlay through `TOKEN` (exported to
`web/src/generated/tokens.json`), so a board drawn here and a board drawn in the browser show
the same pieces.
"""

from .geometry import origin
from .palette import person_accent
from .svg import FONT_MONO, FONT_SANS, num, text

CLIP_ID = "mk-token-clip"

TOKEN = {
    "cx": 50,
    "cy": 52,
    "r": 34,
    "ring": 4,
    "portrait_r": 31,
    "badge": {"x": 66, "y": 66, "size": 24, "rx": 7, "font": 14},
}


def clip_defs():
    return f'<clipPath id="{CLIP_ID}"><circle cx="50" cy="50" r="48"/></clipPath>'


def accent(person):
    if person.get("accent"):
        return person["accent"]
    return person_accent(person["portrait"])


def portrait_group(person, x, y, size, reveal=None, cast_size=0):
    """A portrait scaled into a size×size box at (x, y), clipped to a circle."""
    from . import portraits

    state = "victim" if person.get("victim") else None
    inner = portraits.portrait_for(person, state=state, cast_size=cast_size)
    s = size / 100
    return (
        f'<g transform="translate({num(x)} {num(y)}) scale({num(s)})" '
        f'clip-path="url(#{CLIP_ID})">{inner}</g>'
    )


def token(person, x, y, colours, *, selected=False, reveal=None, cast_size=0):
    t = TOKEN
    cx, cy, r = x + t["cx"], y + t["cy"], t["r"]
    ring = colours["brass"] if selected else accent(person)
    out = [
        f'<circle cx="{cx + 2.5}" cy="{cy + 3.5}" r="{r}" fill="{colours["shadow"]}" fill-opacity=".2"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{colours["paper"]}" stroke="{ring}" stroke-width="{t["ring"]}"/>',
        portrait_group(
            person,
            cx - t["portrait_r"],
            cy - t["portrait_r"],
            t["portrait_r"] * 2,
            reveal,
            cast_size,
        ),
    ]
    if person.get("victim"):
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r + 4.5}" fill="none" stroke="{colours["ink"]}" '
            f'stroke-opacity=".55" stroke-width="1.6" stroke-dasharray="4 4"/>'
        )
    b = t["badge"]
    out.append(
        f'<rect x="{x + b["x"]}" y="{y + b["y"]}" width="{b["size"]}" height="{b["size"]}" '
        f'rx="{b["rx"]}" fill="{accent(person)}" stroke="{colours["paper"]}" stroke-width="2"/>'
    )
    out.append(
        text(
            x + b["x"] + b["size"] / 2,
            y + b["y"] + b["size"] / 2 + 5,
            person["id"],
            b["font"],
            "#ffffff",
            anchor="middle",
            weight="700",
        )
    )
    if reveal and reveal.get("murderer") == person["id"]:
        out.append(guilty_stamp(cx, cy, colours))
    return "".join(out)


def guilty_stamp(cx, cy, colours):
    return (
        f'<g transform="rotate(-14 {cx} {cy})">'
        f'<rect x="{cx - 38}" y="{cy - 12}" width="76" height="24" rx="4" fill="{colours["paper"]}" '
        f'fill-opacity=".86" stroke="{colours["evidence"]}" stroke-width="3"/>'
        + text(
            cx,
            cy + 6,
            "GUILTY",
            16,
            colours["evidence_text"],
            anchor="middle",
            weight="700",
            spacing=2,
            family=FONT_MONO,
        )
        + "</g>"
    )


def cell_layer(
    observation,
    colours,
    *,
    selected=None,
    focus_cells=(),
    people=True,
    notes=True,
    reveal=None,
):
    cast = {p["id"]: p for p in observation["people"]}
    selected_cells = set(observation["marks"].get(selected, ())) | set(focus_cells)
    out = []
    for c in observation["scene"]["cells"]:
        x, y = origin(c)
        label = c["cell"]
        occupants = [
            p for p, value in observation["placements"].items() if value == label
        ]
        marks = [p for p, values in observation["marks"].items() if label in values]
        exclusions = [
            p
            for p, values in observation.get("exclusions", {}).items()
            if label in values and (selected is None or selected == p)
        ]
        out.append('<g class="placement-notes">')
        if notes and exclusions and not occupants:
            out.append(
                f'<g class="manual-exclusion" pointer-events="none">'
                f'<path d="m{x + 37} {y + 34} 26 26m0-26-26 26" stroke="{colours["exclusion"]}" '
                f'stroke-width="4.5" stroke-linecap="round"/>'
                + text(
                    x + 50,
                    y + 80,
                    " ".join(exclusions),
                    12,
                    colours["exclusion"],
                    anchor="middle",
                    weight="600",
                    family=FONT_MONO,
                )
                + "</g>"
            )
        if notes and label in selected_cells:
            out.append(
                f'<rect x="{x + 4}" y="{y + 4}" width="92" height="92" rx="7" fill="{colours["note"]}" '
                f'fill-opacity=".10" stroke="{colours["note"]}" stroke-width="2.5" stroke-dasharray="6 4"/>'
            )
        if people and len(occupants) == 1:
            person = cast[occupants[0]]
            out.append(
                token(
                    person,
                    x,
                    y,
                    colours,
                    selected=selected == person["id"],
                    reveal=reveal,
                    cast_size=len(cast),
                )
            )
        elif people and occupants:
            joined = " · ".join(occupants)
            out.append(
                f'<rect x="{x + 7}" y="{y + 30}" width="86" height="40" rx="9" fill="#fbe3dc" '
                f'stroke="{colours["evidence"]}" stroke-width="2.5"/>'
                + text(
                    x + 50,
                    y + 55,
                    joined,
                    min(16, 128 / max(1, len(joined))),
                    colours["evidence_text"],
                    anchor="middle",
                    weight="700",
                )
            )
        if notes and marks:
            shown = " ".join(marks)
            top = y + 24 if occupants else y + 72
            out.append(
                f'<rect x="{x + 8}" y="{top}" width="84" height="20" rx="10" fill="{colours["paper"]}" '
                f'fill-opacity=".93" stroke="{colours["note"]}" stroke-opacity=".6" stroke-width="1.2"/>'
                + text(
                    x + 50,
                    top + 14.5,
                    shown,
                    min(13, 140 / max(1, len(shown))),
                    colours["note"],
                    anchor="middle",
                    weight="600",
                    family=FONT_MONO,
                )
            )
        out.append("</g>")
    return "".join(out)


__all__ = ["TOKEN", "token", "cell_layer", "clip_defs", "accent", "FONT_SANS"]
