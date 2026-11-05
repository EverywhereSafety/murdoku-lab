"""Alderwick Manor: a Persian rug, a concert grand, a marble bust and a 1920s open tourer.

The manor's first drawings (wingback, chaise, fern and the rest) live in `props`."""

import math

from . import _kit as k
from ._kit import INK, f, grad, s, shadow

GRADIENTS = {
    "concert-black": ("#4a4a55", "#141318"),
    "white-marble": ("#fffefa", "#d9d5ca"),
    "verde": ("#5d8573", "#345245"),
    "tourer": ("#2f6d51", "#173f2e"),
}


def _medallion(cx, cy, rx, ry, *, lobes=10, swell=1.22):
    """A scalloped oval: the outline of a rug's central medallion."""
    pts = [
        (
            cx + rx * math.cos(2 * math.pi * i / lobes),
            cy + ry * math.sin(2 * math.pi * i / lobes),
        )
        for i in range(lobes)
    ]
    d = [f"M{f(pts[0][0])} {f(pts[0][1])}"]
    for i in range(lobes):
        a = 2 * math.pi * (i + 0.5) / lobes
        p = pts[(i + 1) % lobes]
        d.append(
            f"Q{f(cx + rx * swell * math.cos(a))} {f(cy + ry * swell * math.sin(a))} {f(p[0])} {f(p[1])}"
        )
    return "".join(d) + "Z"


def _persian_rug(length, width):
    crimson, navy, gold, ivory = "#a81f2e", "#1e2d55", "#e5bc62", "#f4e8cd"
    band = 9
    x0, y0, x1, y1 = band, band, length - band, width - band
    cx, cy = length / 2, width / 2
    rx, ry = min(length * 0.29, 38), min(width * 0.31, 24)
    o = [k.fringe(length, width, ivory)]
    o.append(
        f'<rect width="{f(length)}" height="{f(width)}" rx="3" fill="{navy}" {s(2)}/>'
        f'<rect x="{f(band / 2)}" y="{f(band / 2)}" width="{f(length - band)}" height="{f(width - band)}" fill="none" '
        f'stroke="{gold}" stroke-width="2.6" stroke-linecap="round" stroke-dasharray=".1 6.4"/>'
        f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(x1 - x0)}" height="{f(y1 - y0)}" fill="{crimson}" stroke="{gold}" stroke-width="1.8"/>'
    )
    # small blossoms scattered over the field, clear of the medallion
    dots, x = [], x0 + 8
    while x < x1 - 4:
        y = y0 + 8
        while y < y1 - 4:
            if ((x - cx) / (rx + 8)) ** 2 + ((y - cy) / (ry + 8)) ** 2 > 1:
                dots.append(f"M{f(x)} {f(y - 2.4)}l2.4 2.4 -2.4 2.4 -2.4 -2.4Z")
            y += 13
        x += 13
    o.append(f'<path d="{"".join(dots)}" fill="{gold}" fill-opacity=".85"/>')
    # corner spandrels
    r = min(20, width * 0.27)
    for x, y, dx, dy in (
        (x0, y0, 1, 1),
        (x1, y0, -1, 1),
        (x0, y1, 1, -1),
        (x1, y1, -1, -1),
    ):
        o.append(
            f'<path d="M{f(x)} {f(y)}h{f(dx * r)}Q{f(x + dx * r * 0.3)} {f(y + dy * r * 0.3)} {f(x)} {f(y + dy * r)}Z" '
            f'fill="{navy}" stroke="{gold}" stroke-width="1.4"/>'
        )
    # the medallion and its pendants
    for side in (-1, 1):
        px = cx + side * (rx * 1.22 + 6)
        o.append(
            f'<path d="M{f(px - 7)} {f(cy)}L{f(px)} {f(cy - 5.4)}L{f(px + 7)} {f(cy)}L{f(px)} {f(cy + 5.4)}Z" '
            f'fill="{gold}" stroke="{navy}" stroke-width="1.2"/>'
        )
    o.append(
        f'<path d="{_medallion(cx, cy, rx, ry)}" fill="{navy}" stroke="{gold}" stroke-width="2.2"/>'
        f'<path d="{_star8(cx, cy, rx * 0.82, ry * 0.82)}" fill="{ivory}" stroke="{gold}" stroke-width="1.2" stroke-linejoin="round"/>'
        f'<path d="{_star8(cx, cy, rx * 0.36, ry * 0.36)}" fill="{crimson}"/>'
    )
    return "".join(o)


def persian_rug(w, h):
    return k.rug(w, h, _persian_rug)


def grand_piano(w, h):
    cx = w / 2
    black = "#1c1b20"
    o = [shadow(cx, h - 12, 42, 9)]
    # the back leg and the pedal lyre, under the keyboard block
    o.append(k.outlined(f"M{f(cx - 17)} 62V84", black, 6, cap="butt"))
    o.append(
        k.outlined(
            f"M{f(cx + 1)} 72V84M{f(cx + 9)} 72V84",
            "#d8b264",
            2,
            ink_width=3.8,
            cap="butt",
        )
    )
    o.append(
        f'<rect x="{f(cx - 2)}" y="83" width="14" height="4" rx="1.5" fill="{grad("brass")}" {s(1.2)}/>'
    )
    # the case: its curved side, then the open well with the gold plate and strings
    rim = (
        f"M{f(cx - 40)} 52L{f(cx - 28)} 6Q{f(cx - 18)} 0 {f(cx - 8)} 4"
        f"Q{f(cx + 3)} 10 {f(cx + 9)} 26Q{f(cx + 15)} 42 {f(cx + 40)} 42V52Z"
    )
    o.append(f'<path d="{rim}" transform="translate(0 12)" fill="{black}" {s()}/>')
    o.append(f'<path d="{rim}" fill="{grad("brass")}" {s(3)}/>')
    strings = "".join(
        f"M{f(cx + x)} 50L{f(cx + x * 0.5 - 8)} 22" for x in range(2, 38, 6)
    )
    o.append(f'<path d="{strings}" stroke="#8f6a22" stroke-width="1.1"/>')
    # the lid, hinged along the straight side and propped up on a stick
    o.append(k.outlined(f"M{f(cx + 25)} 40L{f(cx + 17)} 10", "#d8b264", 2, ink_width=4))
    o.append(
        f'<path d="M{f(cx - 40)} 52L{f(cx - 28)} 6L{f(cx - 14)} -20Q{f(cx - 2)} -22 {f(cx + 5)} -8'
        f'Q{f(cx + 11)} 6 {f(cx + 36)} -6Z" fill="{grad("concert-black")}" {s()}/>'
    )
    o.append(k.highlight(f"M{f(cx - 26)} 26L{f(cx - 16)} -6", 0.3, 2.6))
    # the keyboard block: fall, keys, slip and cheeks
    o.append(
        f'<rect x="{f(cx - 44)}" y="47" width="88" height="29" rx="3" fill="{black}" {s()}/>'
    )
    o.append(k.keyboard(cx - 37, cx + 37, 53, 14))
    o.append(k.highlight(f"M{f(cx - 36)} 50H{f(cx + 14)}", 0.3, 1.6))
    for side in (-1, 1):
        x = cx + side * 35
        o.append(
            f'<path d="M{f(x - 5.5)} 75H{f(x + 5.5)}L{f(x + 3)} 86H{f(x - 3)}Z" fill="{black}" {s()}/>'
            f'<circle cx="{f(x)}" cy="87" r="2.6" fill="{grad("brass")}" {s(1.1)}/>'
        )
    return "".join(o)


def marble_bust(w, h):
    cx = w / 2
    marble = grad("white-marble")
    o = [shadow(cx, h - 12, 28, 8)]
    # the plinth, in dark verde so the white reads
    o.append(
        f'<rect x="{f(cx - 22)}" y="76" width="44" height="11" rx="2" fill="{grad("verde")}" {s()}/>'
        f'<rect x="{f(cx - 15)}" y="46" width="30" height="31" fill="{grad("verde")}" {s()}/>'
        f'<path d="M{f(cx - 10)} 50L{f(cx - 3)} 60L{f(cx - 7)} 74M{f(cx + 7)} 48L{f(cx + 3)} 64L{f(cx + 9)} 72" fill="none" stroke="#a9c9b8" stroke-width="1.3"/>'
        f'<rect x="{f(cx - 20)}" y="38" width="40" height="9" rx="2" fill="{grad("verde")}" {s()}/>'
    )
    # the turned foot, then shoulders cut away to it as a sculptor cuts them
    o.append(
        f'<path d="M{f(cx - 11)} 38L{f(cx - 6)} 28H{f(cx + 6)}L{f(cx + 11)} 38Z" fill="{marble}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 8)} -1L{f(cx - 6)} -8H{f(cx + 6)}L{f(cx + 8)} -1Q{f(cx + 22)} 1 {f(cx + 27)} 9Q{f(cx + 22)} 22 {f(cx + 7)} 30'
        f'H{f(cx - 7)}Q{f(cx - 22)} 22 {f(cx - 27)} 9Q{f(cx - 22)} 1 {f(cx - 8)} -1Z" fill="{marble}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx + 27)} 9Q{f(cx + 22)} 22 {f(cx + 7)} 30L{f(cx + 4)} 26Q{f(cx + 15)} 18 {f(cx + 19)} 6Z" fill="#a9a497" fill-opacity=".4"/>'
        f'<path d="M{f(cx - 21)} 7Q{f(cx - 8)} 11 {f(cx + 2)} 27M{f(cx - 11)} 3Q{f(cx + 3)} 7 {f(cx + 10)} 22" fill="none" stroke="#a9a497" stroke-width="1.5" stroke-linecap="round"/>'
    )
    o.append(f'<ellipse cx="{f(cx)}" cy="-16" rx="13" ry="16" fill="{marble}" {s()}/>')
    # a cap of Roman curls, then a calm blank-eyed face
    o.append(
        f'<path d="M{f(cx - 14)} -14Q{f(cx - 17)} -30 {f(cx - 6)} -33Q{f(cx)} -36 {f(cx + 6)} -33Q{f(cx + 17)} -30 {f(cx + 14)} -14'
        f'Q{f(cx + 11)} -22 {f(cx + 6.5)} -21Q{f(cx + 3)} -25 {f(cx)} -22Q{f(cx - 3)} -25 {f(cx - 6.5)} -21Q{f(cx - 11)} -22 {f(cx - 14)} -14Z" fill="#f4f1e9" {s(1.8)}/>'
        f'<path d="M{f(cx - 10)} -25a2.6 2.6 0 1 1 3 3M{f(cx - 2)} -31a2.6 2.6 0 1 1 3 3M{f(cx + 6)} -27a2.6 2.6 0 1 1 3 3M{f(cx - 3)} -25a2 2 0 1 1 2.4 2.4" fill="none" stroke="#a9a497" stroke-width="1.3" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx - 8)} -13q3 -2 6 0M{f(cx + 2)} -13q3 -2 6 0M{f(cx)} -13l-1.6 7h3M{f(cx - 4)} -2q4 2 8 0" '
        f'fill="none" stroke="#7f7b70" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    o.append(k.highlight(f"M{f(cx - 23)} 8Q{f(cx - 17)} 3 {f(cx - 11)} 2", 0.9, 2))
    return "".join(o)


def _tourer_side(w):
    """Facing east; the bonnet keeps two-fifths of the length and the tub takes the rest."""
    x0, x1 = 6, w - 6
    rear, front = x0 + 18, x1 - 18
    scuttle = x1 - max(38, (x1 - x0) * 0.42)
    long_car = w > 150
    o = [shadow(w / 2, 88, (x1 - x0) / 2, 9)]
    # the hood folded behind the back seat, and the leather seat backs
    o.append(
        f'<rect x="{f(x0 - 1)}" y="31" width="22" height="13" rx="6" fill="#c7b488" {s()}/>'
        f'<path d="M{f(x0 + 6)} 32v11M{f(x0 + 13)} 32v11" stroke="#8f7c52" stroke-width="1.6"/>'
    )
    seats = max(1, round((scuttle - x0) / 55))
    seat_xs = [
        scuttle - 14 - i * (scuttle - x0 - 48) / max(1, seats - 1) for i in range(seats)
    ]
    for x in seat_xs:
        o.append(
            f'<rect x="{f(x - 9)}" y="26" width="18" height="22" rx="6" fill="#c08a52" {s()}/>'
            f'<path d="M{f(x - 4)} 30v12" stroke="#e0b482" stroke-width="2" stroke-linecap="round"/>'
        )
    # tub and bonnet, a coachline along the tub, a door by each seat
    o.append(
        f'<path d="M{f(x0 + 3)} 69Q{f(x0 - 1)} 50 {f(x0 + 5)} 42H{f(scuttle)}V39H{f(x1 - 9)}V69Z" fill="{grad("tourer")}" {s()}/>'
    )
    doors = "".join(f"M{f(x - 12)} 45V66M{f(x + 11)} 45V66" for x in seat_xs)
    o.append(
        f'<path d="M{f(x0 + 6)} 49H{f(scuttle - 2)}" stroke="#e8d7b1" stroke-width="2.2"/>'
        f'<path d="{doors}M{f(scuttle)} 42V68" stroke="#0f2a20" stroke-width="1.8"/>'
    )
    for x in seat_xs:
        o.append(f'<circle cx="{f(x + 7)}" cy="55" r="1.8" fill="{grad("brass")}"/>')
    start = scuttle + (28 if long_car else 8)
    louvres = "".join(
        f"M{f(start + i * 6.5)} 46v11" for i in range(int((x1 - 14 - start) // 6.5))
    )
    o.append(
        f'<path d="{louvres}" stroke="#0f2a20" stroke-width="2.2" stroke-linecap="round"/>'
    )
    o.append(k.highlight(f"M{f(scuttle + 4)} 42H{f(x1 - 14)}", 0.4, 2))
    # windscreen
    o.append(
        f'<path d="M{f(scuttle - 1)} 41L{f(scuttle - 6)} 17H{f(scuttle)}L{f(scuttle + 6)} 41Z" fill="#cfe1ea" fill-opacity=".9" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
    )
    # radiator with its cap, headlamp
    o.append(
        f'<rect x="{f(x1 - 11)}" y="36" width="8" height="34" rx="2.4" fill="{grad("brass")}" {s()}/>'
        f'<circle cx="{f(x1 - 7)}" cy="34" r="2.2" fill="{grad("brass")}" {s(1.1)}/>'
    )
    o.append(
        f'<circle cx="{f(x1 - 1)}" cy="51" r="5.6" fill="#fff3c8" stroke="{INK}" stroke-width="1.8"/>'
        f'<circle cx="{f(x1 - 1)}" cy="51" r="3" fill="none" stroke="#d8b264" stroke-width="1.6"/>'
    )
    # wire wheels under the great sweep of mudguard and running board
    for x in (rear, front):
        o.append(_wire_wheel(x, 75, 12.5))
    if long_car:
        o.append(_wire_wheel(scuttle + 14, 56, 10.5))
    o.append(
        k.outlined(
            f"M{f(rear - 17)} 74Q{f(rear - 15)} 58 {f(rear)} 58Q{f(rear + 15)} 58 {f(rear + 18)} 70L{f(front - 18)} 70"
            f"Q{f(front - 15)} 58 {f(front)} 58Q{f(front + 15)} 58 {f(front + 16)} 72",
            "#1b3a2c",
            4.4,
            ink_width=7.4,
        )
    )
    return "".join(o)


def _tourer_lengthwise(w, h):
    """Running down a column: seen from above, the radiator to the south."""
    cx = w / 2
    top, bottom = 6, h - 22
    half = 25
    screen = bottom - 64
    o = [shadow(cx, (top + bottom) / 2 + 8, half + 9, (bottom - top) / 2, 0.26)]
    for y in (top + 34, bottom - 20):
        for side in (-1, 1):
            x = cx + side * (half + 5)
            o.append(
                f'<rect x="{f(x - 5)}" y="{f(y - 13)}" width="10" height="34" rx="4" fill="#2a2a2a" {s(1.6)}/>'
                f'<path d="M{f(x - side * 4)} {f(y - 15)}Q{f(x + side * 9)} {f(y - 15)} {f(x + side * 9)} {f(y + 2)}Q{f(x + side * 9)} {f(y + 15)} {f(x - side * 4)} {f(y + 15)}Z" '
                f'fill="#1b3a2c" {s(1.8)}/>'
            )
    body = (
        f"M{f(cx - half)} {f(top + 14)}Q{f(cx - half)} {f(top)} {f(cx - half + 14)} {f(top)}H{f(cx + half - 14)}"
        f"Q{f(cx + half)} {f(top)} {f(cx + half)} {f(top + 14)}V{f(screen)}L{f(cx + half - 6)} {f(screen + 8)}V{f(bottom)}"
        f"H{f(cx - half + 6)}V{f(screen + 8)}L{f(cx - half)} {f(screen)}Z"
    )
    o.append(f'<path d="{body}" transform="translate(0 8)" fill="#173f2e" {s()}/>')
    o.append(f'<path d="{body}" fill="{grad("tourer")}" {s()}/>')
    # the folded hood, the cockpit and its benches
    o.append(
        f'<rect x="{f(cx - half + 4)}" y="{f(top + 3)}" width="{f(2 * half - 8)}" height="14" rx="6" fill="#c7b488" {s(1.6)}/>'
        f'<path d="M{f(cx - half + 8)} {f(top + 10)}H{f(cx + half - 8)}" stroke="#8f7c52" stroke-width="1.6"/>'
    )
    well_top, well_bottom = top + 21, screen - 4
    o.append(
        f'<rect x="{f(cx - half + 5)}" y="{f(well_top)}" width="{f(2 * half - 10)}" height="{f(well_bottom - well_top)}" rx="6" fill="#5a3826" {s(1.6)}/>'
    )
    rows = max(1, round((well_bottom - well_top) / 44))
    gap = (well_bottom - well_top) / rows
    for i in range(rows):
        y = well_top + 3 + i * gap
        o.append(
            f'<rect x="{f(cx - half + 8)}" y="{f(y)}" width="{f(2 * half - 16)}" height="18" rx="5" fill="#c08a52" {s(1.4)}/>'
            f'<path d="M{f(cx)} {f(y + 2)}v14" stroke="#8a5a33" stroke-width="1.4"/>'
        )
    o.append(
        f'<circle cx="{f(cx + 11)}" cy="{f(screen - 11)}" r="6" fill="none" stroke="{INK}" stroke-width="2.2"/>'
    )
    # windscreen and bonnet
    o.append(
        f'<rect x="{f(cx - half + 1)}" y="{f(screen - 3)}" width="{f(2 * half - 2)}" height="6" rx="2" fill="#cfe1ea" {s(1.5)}/>'
    )
    louvres = "".join(
        f"M{f(cx - 14)} {f(y)}h8M{f(cx + 6)} {f(y)}h8"
        for y in range(int(screen + 18), int(bottom - 8), 7)
    )
    o.append(
        f'<path d="M{f(cx)} {f(screen + 6)}V{f(bottom - 4)}" stroke="#0f2a20" stroke-width="1.8"/>'
        f'<path d="{louvres}" stroke="#0f2a20" stroke-width="2" stroke-linecap="round"/>'
    )
    # the radiator faces the viewer
    o.append(
        f'<rect x="{f(cx - half + 7)}" y="{f(bottom - 5)}" width="{f(2 * half - 14)}" height="13" rx="2" fill="{grad("brass")}" {s(1.8)}/>'
    )
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(cx + side * (half - 2))}" cy="{f(bottom + 2)}" r="5.4" fill="#fff3c8" stroke="{INK}" stroke-width="1.8"/>'
        )
    return "".join(o)


def motor_car(w, h):
    if h > w * 1.15:
        return _tourer_lengthwise(w, h)
    side = _tourer_side(w)
    return side if h <= 100 else f'<g transform="translate(0 {f(h - 100)})">{side}</g>'


def _star8(cx, cy, rx, ry):
    """An eight-pointed star: the heart of the medallion."""
    points = []
    for i in range(16):
        a, reach = math.pi * i / 8, 1 if i % 2 == 0 else 0.62
        points.append(
            f"{f(cx + rx * reach * math.cos(a))} {f(cy + ry * reach * math.sin(a))}"
        )
    return f'M{"L".join(points)}Z'


def _wire_wheel(x, y, r):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#3a2f28"/>' + k.wheel(
        x, y, r, spoke="#e4d6ae", spokes=8
    )


SKINS = {
    "persian_rug": persian_rug,
    "grand_piano": grand_piano,
    "marble_bust": marble_bust,
    "motor_car": motor_car,
}
STRETCH = {"persian_rug", "motor_car"}
TALL = {"grand_piano", "marble_bust"}
