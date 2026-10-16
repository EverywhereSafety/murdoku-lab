"""Drawing helpers shared by the theme skins (this module defines no skins of its own).

Same conventions as `props`: a drawer works in its footprint's frame (0, 0)–(w, h), the floor
contact sits around h − 12, light comes from the upper left, outlines are 2.2px ink.
"""

import math

from ..geometry import PAD
from ..props import INK, f, grad, legs, s, shadow

__all__ = [
    "INK",
    "armchair",
    "bed",
    "block",
    "bulb",
    "f",
    "face_pattern",
    "grad",
    "highlight",
    "legs",
    "lying",
    "outlined",
    "s",
    "shadow",
    "star",
    "wheel",
]


def face_pattern(pid, body, width=100):
    """A wallpaper drawn per square: tiles start at the board origin, so a tile's x 0–100 is one
    square and its y 0–26 is the visible wall face (the bottom 7px are the skirting board).
    """
    return (
        f'<pattern id="{pid}" width="{width}" height="100" patternUnits="userSpaceOnUse" '
        f'patternTransform="translate({PAD} {PAD})">{body}</pattern>'
    )


def outlined(d, colour, width, *, ink_width=None, cap="round"):
    """A stroked path with an ink outline: rails, ropes, handles, stems."""
    iw = ink_width or width + 3
    return (
        f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{f(iw)}" stroke-linecap="{cap}" stroke-linejoin="round"/>'
        f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{f(width)}" stroke-linecap="{cap}" stroke-linejoin="round"/>'
    )


def highlight(d, opacity=0.4, width=2.4):
    return (
        f'<path d="{d}" fill="none" stroke="#ffffff" stroke-opacity="{opacity}" '
        f'stroke-width="{width}" stroke-linecap="round"/>'
    )


def block(x0, x1, top, front, bottom, *, lid, face, side, depth=8, line=2.2, rx=2):
    """A box seen from above the front: its lid, a sliver of its right side and its front."""
    return (
        f'<path d="M{f(x0)} {f(front)}L{f(x0 + depth)} {f(top)}H{f(x1 + depth)}L{f(x1)} {f(front)}Z" fill="{lid}" {s(1.8)}/>'
        f'<path d="M{f(x1)} {f(front)}L{f(x1 + depth)} {f(top)}V{f(bottom - depth)}L{f(x1)} {f(bottom)}Z" fill="{side}" {s(1.8)}/>'
        f'<rect x="{f(x0)}" y="{f(front)}" width="{f(x1 - x0)}" height="{f(bottom - front)}" rx="{rx}" fill="{face}" {s(line)}/>'
    )


def wheel(cx, cy, r, *, tyre="#2a2a2a", spoke="#7a4d33", hub="#e2c27a", spokes=8):
    d = "".join(
        f"M{f(cx)} {f(cy)}L{f(cx + (r - 3) * math.cos(2 * math.pi * i / spokes))} "
        f"{f(cy + (r - 3) * math.sin(2 * math.pi * i / spokes))}"
        for i in range(spokes)
    )
    return (
        f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="none" stroke="{INK}" stroke-width="5.4"/>'
        f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="none" stroke="{tyre}" stroke-width="3"/>'
        f'<path d="{d}" stroke="{spoke}" stroke-width="2.2" stroke-linecap="round"/>'
        f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(max(2.6, r * 0.2))}" fill="{hub}" {s(1.2)}/>'
    )


def bulb(cx, cy, r=3.6):
    return (
        f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r + 3.4)}" fill="#ffd56b" fill-opacity=".3"/>'
        f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="#fff3c8" stroke="#7a5a1c" stroke-width="1"/>'
    )


def bed(
    w,
    h,
    *,
    frame,
    frame_light,
    sheet,
    blanket,
    band,
    pillow="#ffffff",
    foot=True,
    leg="#3b2418",
):
    """A bed for any footprint: head to the north when it runs down a column (or is square),
    head to the west when it runs along a row."""
    if w > h * 1.15:
        x0, x1 = 8, w - 8
        o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 9)]
        o.append(
            f'<rect x="{f(x0)}" y="-4" width="20" height="78" rx="6" fill="{frame}" {s()}/>'
        )
        if foot:
            o.append(
                f'<rect x="{f(x1 - 16)}" y="22" width="16" height="52" rx="5" fill="{frame}" {s()}/>'
            )
        o.append(
            f'<rect x="{f(x0 + 16)}" y="30" width="{f(x1 - x0 - 30)}" height="26" rx="9" fill="{sheet}" {s()}/>'
        )
        o.append(
            f'<rect x="{f(x0 + 22)}" y="24" width="34" height="18" rx="8" fill="{pillow}" {s(1.8)}/>'
        )
        o.append(
            f'<path d="M{f(x0 + 60)} 30H{f(x1 - 16)}V58H{f(x0 + 60)}Q{f(x0 + 52)} 44 {f(x0 + 60)} 30Z" fill="{blanket}" {s()}/>'
        )
        o.append(f'<path d="M{f(x0 + 70)} 31V57" stroke="{band}" stroke-width="3"/>')
        o.append(
            f'<rect x="{f(x0 + 14)}" y="54" width="{f(x1 - x0 - 26)}" height="18" rx="4" fill="{frame}" {s()}/>'
        )
        o.append(legs(((x0 + 8, 72), (x1 - 8, 72)), 84, 5, leg))
        return "".join(o)
    x0, x1 = 10, w - 10
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 9)]
    o.append(
        f'<rect x="{f(x0)}" y="-6" width="{f(x1 - x0)}" height="34" rx="10" fill="{frame}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 8)} 4H{f(x1 - 8)}" stroke="{frame_light}" stroke-width="2.4" stroke-linecap="round"/>'
    )
    o.append(
        f'<rect x="{f(x0 + 4)}" y="20" width="{f(x1 - x0 - 8)}" height="{f(h - 46)}" rx="6" fill="{sheet}" {s()}/>'
    )
    pairs = 2 if x1 - x0 > 70 else 1
    pw = (x1 - x0 - 24) / pairs
    for i in range(pairs):
        o.append(
            f'<rect x="{f(x0 + 10 + i * (pw + 4))}" y="26" width="{f(pw)}" height="18" rx="7" fill="{pillow}" {s(1.8)}/>'
        )
    o.append(
        f'<rect x="{f(x0 + 2)}" y="50" width="{f(x1 - x0 - 4)}" height="{f(h - 72)}" rx="6" fill="{blanket}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 2)} 60H{f(x1 - 2)}" stroke="{band}" stroke-width="3"/>'
    )
    if foot:
        o.append(
            f'<rect x="{f(x0)}" y="{f(h - 26)}" width="{f(x1 - x0)}" height="14" rx="4" fill="{frame}" {s()}/>'
        )
    o.append(legs(((x0 + 6, h - 14), (x1 - 6, h - 14)), h - 8, 5, leg))
    return "".join(o)


def armchair(
    w,
    h,
    *,
    back,
    seat,
    front,
    arm,
    buttons=True,
    leg="#3b2418",
    studs=None,
    back_top=4,
):
    """An upholstered chair facing south, its back rising a little in front of the wall."""
    cx = w / 2
    o = [shadow(cx, h - 12, 34, 9)]
    o.append(
        f'<path d="M{f(cx - 30)} 50Q{f(cx - 32)} {back_top + 2} {f(cx)} {back_top}Q{f(cx + 32)} {back_top + 2} {f(cx + 30)} 50Z" fill="{back}" {s()}/>'
    )
    o.append(
        highlight(
            f"M{f(cx - 22)} {back_top + 11}Q{f(cx)} {back_top + 3} {f(cx + 22)} {back_top + 11}",
            0.35,
            2.6,
        )
    )
    if buttons:
        for bx in (cx - 14, cx, cx + 14):
            o.append(
                f'<circle cx="{f(bx)}" cy="{back_top + 23}" r="1.9" fill="{INK}" fill-opacity=".45"/>'
            )
    o.append(
        f'<rect x="{f(cx - 28)}" y="44" width="56" height="22" rx="9" fill="{seat}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 28)}" y="60" width="56" height="16" rx="5" fill="{front}" {s()}/>'
    )
    for side in (-1, 1):
        ax = cx + side * 34
        o.append(
            f'<rect x="{f(ax - 8)}" y="38" width="16" height="40" rx="7" fill="{arm}" {s()}/>'
        )
        if studs:
            o.append(
                "".join(
                    f'<circle cx="{f(ax)}" cy="{yy}" r="1.3" fill="{studs}"/>'
                    for yy in range(46, 76, 6)
                )
            )
    o.append(legs(((cx - 26, 76), (cx + 26, 76)), 84, 5, leg))
    return "".join(o)


def star(cx, cy, r, fill, *, inner=0.45, line=1.0):
    points = []
    for i in range(10):
        a = math.radians(-90 + 36 * i)
        rr = r if i % 2 == 0 else r * inner
        points.append(f"{f(cx + rr * math.cos(a))} {f(cy + rr * math.sin(a))}")
    return f'<path d="M{"L".join(points)}Z" fill="{fill}" stroke="{INK}" stroke-width="{line}" stroke-linejoin="round"/>'


def lying(w, h, draw, *, fill, band):
    """Something lying along its footprint (a coffin, a boat). `draw(length, width)` returns
    (outline path, details) in a local frame with the head at (0, 0) and the foot at
    (0, length); the shape's side shows 8px lower, as every front does in this view."""
    if w > h * 1.15:
        length, width = w - 16, h - 24
        place = f"translate(8 {f(h / 2 - 4)}) rotate(-90)"
    else:
        length, width = h - 24, w - 24
        place = f"translate({f(w / 2)} 2)"
    outline, details = draw(length, width)
    return (
        shadow(w / 2, h / 2 + 8, (w - 22) / 2, (h - 30) / 2, 0.26)
        + f'<g transform="translate(0 8)"><g transform="{place}"><path d="{outline}" fill="{band}" {s()}/></g></g>'
        + f'<g transform="{place}"><path d="{outline}" fill="{fill}" {s()}/>{details}</g>'
    )
