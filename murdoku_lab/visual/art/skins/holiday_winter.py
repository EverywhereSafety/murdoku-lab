"""Holiday props: a museum's Friday the 13th, then Thanksgiving, Christmas and New Year.

On a holiday the daily case renames and redraws a few prop kinds; the day's season file maps them
to these names. All are one-cell landmarks, so each is drawn once in a 100×100 cell (floor contact
at y = 88, overhang above y = 0) and `_cell` centres it on the floor of a larger footprint.
"""

import math

from . import _kit as k
from ._kit import INK, f, grad, s, shadow

# Prefixed so a holiday's colours can never collide with a setting's gradient of the same name.
GRADIENTS = {
    "win-cat": ("#3d3843", "#1f1c24"),
    "win-cushion": ("#cf4453", "#8e2132"),
    "win-glass": ("#e8f3f7", "#a7c3d1"),
    "win-gold": ("#f7d873", "#c8952f"),
    "win-plinth": ("#8f8a99", "#5b5766"),
    "win-straw": ("#f8d964", "#d9a12c"),
    "win-horn": ("#e6b873", "#a9713a"),
    "win-pumpkin": ("#fbab45", "#dc6c16"),
    "win-stem": ("#98a653", "#5c6a2d"),
    "win-holly": ("#58a765", "#2c6c3e"),
    "win-fir": ("#41a160", "#1c6339"),
    "win-red": ("#e4544a", "#b52f2a"),
    "win-green": ("#4da06a", "#2a7248"),
    "win-blue": ("#5f9fe4", "#2d68b0"),
    "win-navy": ("#3b5283", "#1d2c50"),
    "win-cream": ("#fffaf0", "#ecdcc0"),
    "win-pudding": ("#6a3c2a", "#351a10"),
    "win-bark": ("#8e6240", "#5a3a22"),
    "win-silver": ("#f2f5f6", "#9eaab0"),
    "win-bottle": ("#3f7a55", "#173f2b"),
    "win-crate": ("#d3a26c", "#a8743f"),
}


def _cell(w, h, *parts):
    return f'<g transform="translate({f((w - 100) / 2)} {f(h - 100)})">{"".join(parts)}</g>'


def _glow(cx, cy, rx, ry, colour, opacity=0.4, soft="mk-soft"):
    # An ellipse, not a circle: sticker cut-outs (art/cards.py) strip soft ellipses and rects.
    return (
        f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{colour}" '
        f'fill-opacity="{opacity}" filter="url(#{soft})"/>'
    )


def _holly_leaf(x, y, angle, length=24, width=8.5):
    """A spiky holly leaf growing from (x, y); angle 0 points right, 90 points down."""
    points = ((0, 0), (0.2, 0.95), (0.5, 1), (0.78, 0.8), (1, 0))
    dips = ((0.05, 0.6), (0.35, 0.45), (0.64, 0.4), (0.86, 0.25))
    d = "M0 0"
    for (cx, cy), (px, py) in zip(dips, points[1:]):
        d += f"Q{f(cx * length)} {f(-cy * width)} {f(px * length)} {f(-py * width)}"
    for (cx, cy), (px, py) in zip(dips[::-1], points[-2::-1]):
        d += f"Q{f(cx * length)} {f(cy * width)} {f(px * length)} {f(py * width)}"
    return (
        f'<g transform="translate({f(x)} {f(y)}) rotate({f(angle)})">'
        f'<path d="{d}Z" fill="{grad("win-holly")}" {s(1.4)}/>'
        f'<path d="M{f(0.08 * length)} 0H{f(0.86 * length)}" stroke="#bfe0a4" stroke-width="1.2" stroke-linecap="round"/></g>'
    )


def _berry(x, y, r=4):
    return (
        f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#d9302c" {s(1.3)}/>'
        f'<circle cx="{f(x - r * 0.3)}" cy="{f(y - r * 0.35)}" r="{f(r * 0.28)}" fill="#ffffff" fill-opacity=".8"/>'
    )


def _bow(x, y, colour, size=1.0):
    """A ribbon bow knotted at (x, y): two short tails, two loops and a knot."""
    return (
        f'<g transform="translate({f(x)} {f(y)}) scale({f(size)})">'
        f'<path d="M-1 1L-9 13L-5 13L-3 16L2 3ZM1 1L9 13L5 13L3 16L-2 3Z" fill="{colour}" {s(1.3)}/>'
        f'<path d="M0 0C-5 -11 -20 -13 -19 -3C-18 6 -6 5 0 0ZM0 0C5 -11 20 -13 19 -3C18 6 6 5 0 0Z" fill="{colour}" {s(1.5)}/>'
        '<path d="M-4 -2Q-11 -7 -15 -4M4 -2Q11 -7 15 -4" fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-width="1.6" stroke-linecap="round"/>'
        f'<rect x="-3.6" y="-3.6" width="7.2" height="7.2" rx="2.4" fill="{colour}" {s(1.4)}/></g>'
    )


def _sparkle(x, y, r, colour="#fff3b0"):
    return (
        f'<path d="M{f(x)} {f(y - r)}Q{f(x)} {f(y)} {f(x + r)} {f(y)}Q{f(x)} {f(y)} {f(x)} {f(y + r)}'
        f'Q{f(x)} {f(y)} {f(x - r)} {f(y)}Q{f(x)} {f(y)} {f(x)} {f(y - r)}Z" fill="{colour}" {s(0.9)}/>'
    )


# ------------------------------------------------------------------------- Friday the 13th
def black_cat(w, h):
    fur = grad("win-cat")
    line = "#5f5a69"
    o = [shadow(50, 86, 38, 8)]
    # A red cushion keeps the black silhouette clear of a dark floor.
    o.append(
        f'<path d="M10 76Q50 62 90 76Q96 82 90 87Q50 95 10 87Q4 82 10 76Z" fill="{grad("win-cushion")}" {s()}/>'
        '<path d="M16 77Q50 66 84 77" fill="none" stroke="#ffffff" stroke-opacity=".3" stroke-width="2" stroke-linecap="round"/>'
    )
    for x, y in ((9, 87), (91, 87)):
        o.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="#e2b44c" {s(1.2)}/>')
    # The tail rises behind the body in a question mark.
    o.append(
        k.outlined(
            "M68 80C84 86 98 74 92 56C88 44 78 46 80 34", "#2d2933", 7.6, ink_width=10.6
        )
    )
    o.append(k.highlight("M91 56C88 47 81 47 81 37", 0.3, 1.8))
    # Body with its haunches and two front legs in a lighter line.
    o.append(
        f'<path d="M37 38C29 50 22 66 25 82Q50 90 75 82C78 66 71 50 63 38Z" fill="{fur}" {s()}/>'
        f'<path d="M36 82Q29 79 29.5 70Q30 63 36 61M64 82Q71 79 70.5 70Q70 63 64 61" fill="none" stroke="#4b4655" stroke-width="1.6" stroke-linecap="round"/>'
        f'<path d="M39 58Q37.5 70 38 80M50 62V81M61 58Q62.5 70 62 80" fill="none" stroke="{line}" stroke-width="1.7" stroke-linecap="round"/>'
    )
    for x in (43.6, 56.4):
        o.append(
            f'<ellipse cx="{x}" cy="83" rx="7.2" ry="4.2" fill="#38333e" stroke="{line}" stroke-width="1.5"/>'
            f'<path d="M{x - 2.4} 81.6v2.8M{x + 2.4} 81.6v2.8" stroke="{line}" stroke-width="1.1" stroke-linecap="round"/>'
        )
    o.append(k.highlight("M30 58C27 64 26 70 26.5 76", 0.26, 2))
    # Head and pointed ears as one shape.
    o.append(
        f'<path d="M26 26C25 16 23 4 21 -10Q33 -4 41 2Q50 0 59 2Q67 -4 79 -10C77 4 75 16 74 26'
        f'C74 38 63 45 50 45C37 45 26 38 26 26Z" fill="{fur}" {s()}/>'
    )
    o.append(
        '<path d="M26.5 -2Q32 0 36.5 4L29 12ZM73.5 -2Q68 0 63.5 4L71 12Z" fill="#c26f88"/>'
    )
    o.append(k.highlight("M41 5.4Q50 3.4 59 5.4", 0.28, 2))
    o.append(k.highlight("M28 18Q27.6 24 29.5 30", 0.24, 2))
    # Almond eyes with slit pupils.
    o.append(
        '<path d="M31 20Q40 12 47.5 26Q38 31 31 20ZM69 20Q60 12 52.5 26Q62 31 69 20Z" fill="#ffd93b" stroke="#151116" stroke-width="1.3"/>'
        '<ellipse cx="39.8" cy="22.4" rx="2" ry="6" fill="#151116"/><ellipse cx="60.2" cy="22.4" rx="2" ry="6" fill="#151116"/>'
        '<circle cx="37.2" cy="19.6" r="1.2" fill="#ffffff"/><circle cx="57.6" cy="19.6" r="1.2" fill="#ffffff"/>'
    )
    o.append(
        '<path d="M46.8 31.5H53.2L50 35.2Z" fill="#e58a9e"/>'
        '<path d="M50 35.2Q47.5 39 44 37M50 35.2Q52.5 39 56 37" fill="none" stroke="#8a8494" stroke-width="1.3" stroke-linecap="round"/>'
    )
    # Whiskers: pale, with a dark edge so they still show on a pale floor.
    o.append(
        k.outlined(
            "M35 33Q24 29 14 29M35 36.5Q24 36 13 38.5M65 33Q76 29 86 29M65 36.5Q76 36 87 38.5",
            "#f4efe6",
            1,
            ink_width=2,
        )
    )
    return _cell(w, h, *o)


def cracked_mirror(w, h):
    o = [shadow(50, 87, 40, 7)]
    wood = "#6b4229"
    for x in (17, 83):
        o.append(k.outlined(f"M{x - 12} 86H{x + 12}", wood, 4.4))
    o.append(k.outlined("M17 77H83", wood, 3.6, cap="butt"))
    for x in (17, 83):
        o.append(k.outlined(f"M{x} 84V14", "#7d4f33", 4.4, cap="butt"))
        o.append(f'<circle cx="{x}" cy="11" r="4" fill="{grad("win-gold")}" {s(1.4)}/>')
    # The oval: finial, walnut frame, gold bead, silvered glass.
    o.append(
        f'<circle cx="50" cy="-23" r="4.2" fill="{grad("win-gold")}" {s(1.4)}/>'
        f'<ellipse cx="50" cy="26" rx="27" ry="45" fill="{grad("walnut")}" {s()}/>'
        f'<ellipse cx="50" cy="26" rx="23.6" ry="41.6" fill="none" stroke="#e2b44c" stroke-width="1.8"/>'
        f'<ellipse cx="50" cy="26" rx="21" ry="39" fill="{grad("win-glass")}" {s(1.6)}/>'
    )
    for x in (21, 79):
        o.append(f'<circle cx="{x}" cy="26" r="3.2" fill="#e2b44c" {s(1.2)}/>')
    o.append(k.highlight("M36 2Q31 16 32 34", 0.9, 3.4))
    o.append(k.highlight("M41 -4Q38 2 37 8", 0.9, 2.4))
    # The crack: a dark hole, a web around it and long runs out to the frame.
    runs = (
        "M57 18L51 6L53 -3L49 -10",
        "M57 18L63 9L65 2",
        "M57 18L66 22L70 26",
        "M57 18L61 32L57 44L61 56",
        "M57 18L46 26L38 24L31 30",
        "M57 18L49 38L42 48L41 58",
    )
    d = "".join(runs)
    o.append(
        f'<path d="{d}" transform="translate(1 1)" fill="none" stroke="#ffffff" stroke-width="1.3" stroke-linejoin="round"/>'
        f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>'
        f'<path d="M51 6L63 9L66 22L61 32L49 38L46 26Z" fill="none" stroke="{INK}" stroke-width="1.3" stroke-linejoin="round"/>'
        f'<path d="M54 13L61 12L62 20L57 24L52 20Z" fill="#46525e" {s(1.4)}/>'
    )
    # Shards fallen under it.
    o.append(
        f'<path d="M37 87L44 81L46 88ZM58 88L62 83L67 87Z" fill="{grad("win-glass")}" {s(1.2)}/>'
    )
    return _cell(w, h, *o)


def cursed_idol(w, h):
    gold = grad("win-gold")
    carve, socket = "#6b4a17", "#1d1a12"
    o = [shadow(50, 87, 36, 8)]
    o.append(_glow(50, 26, 44, 44, "#a6ff86", 0.22))
    o.append(_glow(50, 26, 34, 35, "#d2ffab", 0.34))
    # A dark plinth with a carved zigzag.
    o.append(
        f'<rect x="24" y="66" width="52" height="21" rx="2" fill="{grad("win-plinth")}" {s()}/>'
        f'<rect x="18" y="59" width="64" height="9" rx="2.5" fill="#a9a4b1" {s()}/>'
        '<path d="M29 80l6 -7 6 7 6 -7 6 7 6 -7 6 7 6 -7" fill="none" stroke="#403c49" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    # Seated: crossed legs under a short body, hands on the belly.
    o.append(
        f'<path d="M34 54Q30 42 37 36H63Q70 42 66 54Z" fill="{gold}" {s()}/>'
        f'<path d="M25 59Q24 49 36 49Q44 49 50 54Q56 49 64 49Q76 49 75 59Z" fill="{gold}" {s()}/>'
    )
    o.append(
        f'<circle cx="44" cy="49" r="4.2" fill="#f7d873" {s(1.5)}/><circle cx="56" cy="49" r="4.2" fill="#f7d873" {s(1.5)}/>'
    )
    # Stepped headdress, ear spools and a wide, mask-like head.
    o.append(
        f'<path d="M30 10V2H38V-3H45V-8H55V-3H62V2H70V10Z" fill="#d9a93c" {s()}/>'
        f'<path d="M50 -5L53.6 -0.6L50 3.8L46.4 -0.6Z" fill="#d9473a" {s(1.2)}/>'
    )
    for x in (24.5, 75.5):
        o.append(
            f'<circle cx="{x}" cy="25" r="5.6" fill="{gold}" {s(1.7)}/><circle cx="{x}" cy="25" r="1.8" fill="{carve}"/>'
        )
    o.append(
        f'<path d="M28 13Q28 8 33 8H67Q72 8 72 13L70 33Q69 44 58 44H42Q31 44 30 33Z" fill="{gold}" {s()}/>'
    )
    # The carved face: deep lit eyes under one heavy brow, a broad nose, a toothy grimace.
    o.append(
        f'<circle cx="40" cy="23.5" r="7.4" fill="{socket}"/><circle cx="60" cy="23.5" r="7.4" fill="{socket}"/>'
    )
    o.append(_glow(40, 23.5, 4.2, 4.2, "#c4ff5c", 0.9, "mk-softer"))
    o.append(_glow(60, 23.5, 4.2, 4.2, "#c4ff5c", 0.9, "mk-softer"))
    o.append(
        '<circle cx="40" cy="23.5" r="2.8" fill="#f2ffb4"/><circle cx="60" cy="23.5" r="2.8" fill="#f2ffb4"/>'
    )
    o.append(
        f'<path d="M31 18Q40 9 48 17L50 19L52 17Q60 9 69 18" fill="none" stroke="{carve}" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M50 19Q48.4 27 43.6 30.4Q50 33.6 56.4 30.4Q51.6 27 50 19Z" fill="#fbe493" {s(1.4)}/>'
        f'<path d="M35 34.4H65Q64 42 57 42H43Q36 42 35 34.4Z" fill="{socket}"/>'
        '<path d="M36 34.8H64L61.4 39.4L58.8 34.8L56.2 39.4L53.6 34.8L51 39.4L48.4 34.8L45.8 39.4L43.2 34.8L40.6 39.4L38 34.8Z" fill="#f6edc9"/>'
    )
    o.append(k.highlight("M32 12.4Q40 10.2 50 10.4", 0.6, 2))
    return _cell(w, h, *o)


# ---------------------------------------------------------------------------- Thanksgiving
def _wheat_ear(x, y, angle, length=25, half=5.6):
    """One ear growing from (x, y), leaning `angle` degrees from upright."""
    chevrons = "".join(
        f"M0 {f(-t * length)}L{f(-half * 0.74)} {f(-t * length - 4.2)}"
        f"M0 {f(-t * length)}L{f(half * 0.74)} {f(-t * length - 4.2)}"
        for t in (0.12, 0.32, 0.52, 0.72)
    )
    return (
        f'<g transform="translate({f(x)} {f(y)}) rotate({f(angle)})">'
        f'<path d="M0 {f(-length)}V{f(-length - 8)}M{f(-half * 0.5)} {f(-length * 0.8)}L{f(-half * 1.1)} {f(-length - 4)}'
        f'M{f(half * 0.5)} {f(-length * 0.8)}L{f(half * 1.1)} {f(-length - 4)}" stroke="#9c7420" stroke-width="1" stroke-linecap="round"/>'
        f'<path d="M0 2C{f(-half * 1.25)} {f(-length * 0.25)} {f(-half * 1.25)} {f(-length * 0.72)} 0 {f(-length)}'
        f'C{f(half * 1.25)} {f(-length * 0.72)} {f(half * 1.25)} {f(-length * 0.25)} 0 2Z" fill="{grad("win-straw")}" {s(1.5)}/>'
        f'<path d="{chevrons}" fill="none" stroke="#a97a1e" stroke-width="1.2" stroke-linecap="round"/></g>'
    )


def wheat_sheaf(w, h):
    waist = 52
    o = [shadow(50, 87, 30, 7)]

    def ear(angle, reach):
        a = math.radians(angle)
        return 50 + reach * math.sin(a), waist - reach * math.cos(a), angle

    back = [ear(a, 44) for a in (-34, -17, 0, 17, 34)]
    front = [ear(a, 26) for a in (-46, -27, -9, 9, 27, 46)]
    # Stalks fanning up from the waist, ears behind and in front of them.
    o.append(
        f'<path d="M41 {waist}L19 30Q50 8 81 30L59 {waist}Z" fill="{grad("win-straw")}" {s(1.6)}/>'
    )
    for x, y, angle in back:
        o.append(_wheat_ear(x, y, angle))
    stalks = "".join(f"M50 {waist}L{f(x)} {f(y)}" for x, y, _ in back + front)
    o.append(
        f'<path d="{stalks}" fill="none" stroke="#b5851f" stroke-width="1.6" stroke-linecap="round"/>'
    )
    for x, y, angle in front:
        o.append(_wheat_ear(x, y, angle))
    # Cut stalks flaring below the band.
    o.append(
        f'<path d="M40 {waist}Q36 72 26 85Q50 92 74 85Q64 72 60 {waist}Z" fill="{grad("win-straw")}" {s()}/>'
        '<path d="M45 56Q43 72 36 86M50 56V88M55 56Q57 72 64 86M42 56Q38 72 30 84M58 56Q62 72 70 84" fill="none" stroke="#a97a1e" stroke-width="1.5" stroke-linecap="round"/>'
    )
    # The binding.
    o.append(
        f'<rect x="37" y="{waist - 6}" width="26" height="11" rx="3" fill="{grad("win-red")}" {s()}/>'
        f'<path d="M39 {waist - 3}H61" stroke="#ffffff" stroke-opacity=".35" stroke-width="1.6" stroke-linecap="round"/>'
    )
    o.append(_bow(50, waist, grad("win-red"), 0.8))
    return _cell(w, h, *o)


def _bezier(points, t):
    u = 1 - t
    weights = (u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t)
    return (
        sum(c * p[0] for c, p in zip(weights, points)),
        sum(c * p[1] for c, p in zip(weights, points)),
    )


def _apple(x, y, r, colour="#d8352f"):
    return (
        f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{colour}" {s(1.8)}/>'
        f'<path d="M{f(x)} {f(y - r + 3)}Q{f(x + 1)} {f(y - r - 2)} {f(x + 3)} {f(y - r - 5)}" fill="none" stroke="#4a2f1c" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M{f(x + 2)} {f(y - r - 1)}Q{f(x + 8)} {f(y - r - 7)} {f(x + 12)} {f(y - r - 2)}Q{f(x + 7)} {f(y - r + 2)} {f(x + 2)} {f(y - r - 1)}Z" fill="#6aa84f" {s(1)}/>'
        f'<path d="M{f(x - r * 0.6)} {f(y - r * 0.2)}Q{f(x - r * 0.5)} {f(y - r * 0.6)} {f(x - r * 0.15)} {f(y - r * 0.7)}" fill="none" stroke="#ffffff" stroke-opacity=".65" stroke-width="2" stroke-linecap="round"/>'
    )


def _grapes(x, y):
    """A bunch hanging from (x, y)."""
    spots = ((0, 0), (9, -1), (-9, -1), (4.5, 7), (-4.5, 7), (0, 14), (13, 6), (-13, 6))
    out = []
    for dx, dy in sorted(spots, key=lambda p: p[1]):
        out.append(
            f'<circle cx="{f(x + dx)}" cy="{f(y + dy)}" r="5.2" fill="#6d3f96" {s(1.4)}/>'
            f'<circle cx="{f(x + dx - 1.6)}" cy="{f(y + dy - 1.8)}" r="1.4" fill="#ffffff" fill-opacity=".65"/>'
        )
    return "".join(out)


def cornucopia(w, h):
    spine = ((38, 52), (70, 68), (98, 58), (85, 10))

    def station(t):
        x, y = _bezier(spine, t)
        x2, y2 = _bezier(spine, min(1, t + 0.01))
        x1, y1 = _bezier(spine, max(0, t - 0.01))
        length = math.hypot(x2 - x1, y2 - y1)
        tx, ty = (x2 - x1) / length, (y2 - y1) / length
        half = 24 * (1 - t) ** 0.8
        return x, y, tx, ty, half

    upper, lower = [], []
    for i in range(29):
        x, y, tx, ty, half = station(i / 28)
        upper.append((x + ty * half, y - tx * half))
        lower.append((x - ty * half, y + tx * half))
    outline = "L".join(f"{f(x)} {f(y)}" for x, y in upper + lower[::-1])
    o = [shadow(50, 85, 44, 7)]
    o.append(f'<path d="M{outline}Z" fill="{grad("win-horn")}" {s()}/>')
    o.append(
        k.highlight(
            "M" + "L".join(f"{f(px)} {f(py + 4)}" for px, py in upper[3:18]), 0.4, 2.4
        )
    )
    # Woven hoops following the horn, curved like the rim.
    hoops = []
    for t in (0.12, 0.24, 0.36, 0.48, 0.6, 0.72, 0.84):
        x, y, tx, ty, half = station(t)
        hoops.append(
            f"M{f(x + ty * half)} {f(y - tx * half)}"
            f"Q{f(x + tx * half * 0.5)} {f(y + ty * half * 0.5)} {f(x - ty * half)} {f(y + tx * half)}"
        )
    o.append(
        f'<path d="{"".join(hoops)}" fill="none" stroke="#7a4c22" stroke-width="2.2" stroke-linecap="round"/>'
    )
    # The mouth, tilted across the horn's first stretch.
    o.append(
        f'<g transform="rotate(26 38 52)"><ellipse cx="38" cy="52" rx="11" ry="25" fill="#e8c384" {s()}/>'
        f'<ellipse cx="38" cy="52" rx="6.6" ry="20" fill="#54341a" {s(1.4)}/></g>'
    )
    # What spills out: leaves and a pear at the back, grapes, then apples rolling to the floor.
    o.append(
        f'<path d="M30 34Q18 22 6 28Q14 40 30 38ZM36 30Q36 16 24 10Q18 22 30 34Z" fill="#6aa84f" {s(1.5)}/>'
        '<path d="M28 36Q18 30 11 30M33 31Q29 22 25 15" fill="none" stroke="#3f7a3a" stroke-width="1.2" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M24 26C30 26 31 32 32 38C35 46 33 58 22 58C11 58 9 46 13 38C16 32 17 26 24 26Z" fill="#e6cf55" {s(1.8)}/>'
        '<path d="M24 26Q24 22 27 20" fill="none" stroke="#4a2f1c" stroke-width="2.2" stroke-linecap="round"/>'
        '<path d="M15 44Q15 38 19 34" fill="none" stroke="#ffffff" stroke-opacity=".7" stroke-width="2" stroke-linecap="round"/>'
    )
    o.append(_grapes(46, 60))
    o.append(_apple(22, 74, 13))
    o.append(
        f'<circle cx="50" cy="80" r="9" fill="#f08a2c" {s(1.8)}/>'
        '<path d="M45 76Q47 73 50 73" fill="none" stroke="#ffffff" stroke-opacity=".7" stroke-width="1.8" stroke-linecap="round"/>'
        f'<circle cx="52" cy="72.5" r="1.2" fill="{INK}"/>'
    )
    return _cell(w, h, *o)


def giant_pumpkin(w, h):
    skin = grad("win-pumpkin")
    o = [shadow(50, 87, 46, 8)]
    # Vine and leaf behind the stem.
    o.append(k.outlined("M58 18Q72 4 80 12Q86 18 78 22Q73 22 74 17", "#6d8a35", 2.2))
    o.append(
        f'<path d="M58 18C60 6 68 2 76 2C74 8 78 10 82 12C76 16 76 20 78 22C70 26 62 24 58 18Z" fill="{grad("win-holly")}" {s(1.6)}/>'
        '<path d="M60 18Q68 12 76 8" fill="none" stroke="#bfe0a4" stroke-width="1.2" stroke-linecap="round"/>'
    )
    # Ribs from the outside in, so each lobe overlaps the one beyond it.
    for dx, rx, ry in (
        (31, 16, 30),
        (-31, 16, 30),
        (20, 15, 33),
        (-20, 15, 33),
        (9, 13, 35),
        (-9, 13, 35),
        (0, 11, 36),
    ):
        o.append(
            f'<ellipse cx="{50 + dx}" cy="53" rx="{rx}" ry="{ry}" fill="{skin}" {s(1.8)}/>'
        )
    o.append(k.highlight("M26 30Q20 42 21 56", 0.55, 3))
    o.append(k.highlight("M40 24Q36 32 35 42", 0.45, 2.6))
    # A chunky stem, and the fair's blue ribbon: this one is a prize-winner.
    o.append(
        f'<path d="M42 21C43 12 42 6 37 -1L52 -5C52 3 54 12 58 21Q50 26 42 21Z" fill="{grad("win-stem")}" {s()}/>'
        '<path d="M47 20Q47 10 44 1M52 20Q51 10 49 -1" fill="none" stroke="#49551f" stroke-width="1.4" stroke-linecap="round"/>'
        '<path d="M38 -1L51 -5" stroke="#d6dc9a" stroke-width="2" stroke-linecap="round"/>'
    )
    spikes = "".join(
        f"{'M' if i == 0 else 'L'}{f(66 + (10 if i % 2 == 0 else 8) * math.cos(math.radians(i * 30)))} "
        f"{f(62 + (10 if i % 2 == 0 else 8) * math.sin(math.radians(i * 30)))}"
        for i in range(12)
    )
    o.append(
        f'<path d="M62 70L58 86L66 81L72 86L70 70Z" fill="#3f6fb0" {s(1.4)}/>'
        f'<path d="{spikes}Z" fill="#3f6fb0" {s(1.4)}/>'
        f'<circle cx="66" cy="62" r="5" fill="#f6efe0" {s(1.2)}/>'
    )
    return _cell(w, h, *o)


# ------------------------------------------------------------------------------- Christmas
def _bauble(x, y, r, colour):
    return (
        f'<rect x="{f(x - 1.7)}" y="{f(y - r - 2.4)}" width="3.4" height="3.2" rx=".8" fill="#e2c27a" stroke="{INK}" stroke-width=".8"/>'
        f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{colour}" {s(1.3)}/>'
        f'<circle cx="{f(x - r * 0.35)}" cy="{f(y - r * 0.35)}" r="{f(r * 0.28)}" fill="#ffffff" fill-opacity=".85"/>'
    )


def christmas_tree(w, h):
    o = [shadow(50, 87, 34, 8)]
    o.append(_glow(50, -20, 18, 18, "#ffe27a", 0.6))
    # A glazed red pot with a gold rim, under the tree's skirt: nothing like the fir's plain tub.
    o.append(
        f'<path d="M34 68H66L62 88H38Z" fill="{grad("win-red")}" {s()}/>'
        '<path d="M39 73L41.4 85" stroke="#ffffff" stroke-opacity=".4" stroke-width="2.4" stroke-linecap="round"/>'
        f'<rect x="30" y="63" width="40" height="9" rx="2.5" fill="{grad("win-gold")}" {s()}/>'
    )
    # Three full tiers with curved, flicked-out skirts; no snow.
    tiers = ((42, 62, 8), (33, 38, -12), (24, 14, -26))
    for half, yb, ya in tiers:
        n = 6
        scallop = "".join(
            f"Q{f(50 + half - (i + 0.5) * 2 * half / n)} {f(yb + 7)} {f(50 + half - (i + 1) * 2 * half / n)} {f(yb)}"
            for i in range(n)
        )
        o.append(
            f'<path d="M50 {ya}Q{f(50 + half * 0.42)} {f(ya + (yb - ya) * 0.66)} {f(50 + half)} {yb}{scallop}'
            f'Q{f(50 - half * 0.42)} {f(ya + (yb - ya) * 0.66)} 50 {ya}Z" fill="{grad("win-fir")}" {s()}/>'
        )
    # Gold garland swags, one per tier.
    for d in ("M23 50Q48 66 74 47", "M31 26Q50 40 68 23", "M39 2Q50 10 60 0"):
        o.append(k.outlined(d, "#f7d460", 2.6, ink_width=4.4))
    for x, y, r, colour in (
        (27, 54, 5.4, "#e23b33"),
        (43, 57, 5.4, "#3f83d8"),
        (59, 55, 5.4, "#f4c62f"),
        (74, 55, 5.4, "#e23b33"),
        (36, 30, 5, "#f4c62f"),
        (51, 33, 5, "#e23b33"),
        (65, 29, 5, "#3f83d8"),
        (44, 6, 4.4, "#e23b33"),
        (57, 4, 4.4, "#f4c62f"),
    ):
        o.append(_bauble(x, y, r, colour))
    o.append(k.star(50, -21, 12.5, "#ffd84d", line=1.8))
    return _cell(w, h, *o)


def _gift(x0, x1, top, front, bottom, *, lid, face, side, ribbon, band=4):
    """A wrapped box in the props' 3/4 view: the ribbon crosses the lid and runs down its front."""
    depth = 8
    mid = (x0 + x1) / 2
    level = (top + front) / 2
    return (
        k.block(x0, x1, top, front, bottom, lid=lid, face=face, side=side, depth=depth)
        + f'<path d="M{f(x0 + depth / 2)} {f(level)}H{f(x1 + depth / 2)}" stroke="{ribbon}" stroke-width="{f(band * 0.8)}"/>'
        + f'<path d="M{f(mid - band)} {f(front)}L{f(mid - band + depth)} {f(top)}H{f(mid + band + depth)}L{f(mid + band)} {f(front)}Z" fill="{ribbon}" {s(1.1)}/>'
        + f'<rect x="{f(mid - band)}" y="{f(front)}" width="{f(band * 2)}" height="{f(bottom - front)}" fill="{ribbon}" {s(1.1)}/>'
    )


def gift_pile(w, h):
    o = [shadow(50, 87, 44, 7)]
    gold, cream, red = "#f5cf5c", "#fffaf0", "#e0403a"
    # The big red box at the back, a blue one balanced on it, a green one in front.
    o.append(
        _gift(
            8,
            58,
            36,
            46,
            85,
            lid="#ef7a6e",
            face=grad("win-red"),
            side="#8e2522",
            ribbon=gold,
            band=5,
        )
    )
    o.append(
        '<g transform="rotate(-4 34 30)">'
        + _gift(
            17,
            47,
            11,
            19,
            42,
            lid="#8fc0ee",
            face=grad("win-blue"),
            side="#234f8a",
            ribbon=red,
        )
        + _bow(36, 13, red, 0.95)
        + "</g>"
    )
    o.append(
        _gift(
            50,
            84,
            56,
            64,
            89,
            lid="#7cc795",
            face=grad("win-green"),
            side="#23633f",
            ribbon=cream,
        )
    )
    o.append(_bow(71, 58, cream, 0.8))
    return _cell(w, h, *o)


def plum_pudding(w, h):
    o = [shadow(50, 87, 44, 7)]
    # The plate.
    o.append(
        f'<ellipse cx="50" cy="79" rx="45" ry="11" fill="{grad("win-cream")}" {s()}/>'
        '<ellipse cx="50" cy="78" rx="39" ry="8.2" fill="none" stroke="#c8952f" stroke-width="1.6"/>'
    )
    # The dome, studded with fruit.
    o.append(
        f'<path d="M17 66C17 30 33 12 50 12C67 12 83 30 83 66Q83 80 50 80Q17 80 17 66Z" fill="{grad("win-pudding")}" {s()}/>'
    )
    for x, y, colour in (
        (28, 62, "#1c0d08"),
        (40, 70, "#1c0d08"),
        (52, 64, "#1c0d08"),
        (64, 72, "#1c0d08"),
        (74, 60, "#1c0d08"),
        (35, 56, "#b5642c"),
        (60, 58, "#b5642c"),
        (47, 74, "#b5642c"),
        (71, 68, "#8c2f3a"),
        (24, 68, "#8c2f3a"),
    ):
        o.append(f'<circle cx="{x}" cy="{y}" r="2.2" fill="{colour}"/>')
    # White icing poured over the top, running down in drips.
    o.append(
        f'<path d="M21 42C24 22 38 9 50 9C62 9 76 22 79 42Q80 53 74 52Q70 51 69 45Q67 41 64 45'
        f'Q63 60 56 60Q50 60 50 48Q48 42 44 46Q43 55 37 55Q31 55 31 46Q29 42 26 47Q20 52 21 42Z" fill="#fffdf6" {s()}/>'
    )
    o.append(
        '<path d="M31 21Q37 15 44 14" fill="none" stroke="#c9d6e4" stroke-width="2.2" stroke-linecap="round"/>'
    )
    o.append(
        '<path d="M57 57Q62 56 62 46M34 52Q37 53 41 48M71 49Q75 50 77 43" fill="none" stroke="#c9d6e4" stroke-width="1.8" stroke-linecap="round"/>'
    )
    # The holly sprig on top.
    o.append(_holly_leaf(50, 9, 200, 28, 9.5))
    o.append(_holly_leaf(50, 9, -20, 28, 9.5))
    o.append(_berry(45, 8, 4.4) + _berry(55, 8, 4.4) + _berry(50, 2, 4.4))
    return _cell(w, h, *o)


def yule_log(w, h):
    o = [shadow(52, 85, 44, 7)]
    # The candle goes behind the log's top edge.
    o.append(_glow(58, 2, 12, 13, "#ffd56b", 0.65))
    o.append(
        f'<rect x="52" y="10" width="12" height="38" rx="2" fill="{grad("win-red")}" {s()}/>'
        '<path d="M55 14V40" stroke="#ffffff" stroke-opacity=".4" stroke-width="2" stroke-linecap="round"/>'
        '<path d="M58 10V5" stroke="#3b2418" stroke-width="1.6" stroke-linecap="round"/>'
        f'<path d="M58 6C53 2 54 -3 58 -10C62 -3 63 2 58 6Z" fill="#f6a12c" {s(1.4)}/>'
        '<path d="M58 5C56 2 57 -1 58 -4C59 -1 60 2 58 5Z" fill="#fff0a8"/>'
    )
    # The log: bark, a sawn branch stub, the pale cut end towards the light.
    o.append(
        f'<path d="M22 42H84Q97 62 84 84H22Z" fill="{grad("win-bark")}" {s()}/>'
        '<path d="M34 56Q48 53 60 57T88 56M38 70Q52 67 64 71T90 70M32 78Q44 76 56 79" fill="none" stroke="#3f2614" stroke-width="1.8" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M70 46L76 32L88 36L84 50Z" fill="{grad("win-bark")}" {s(1.8)}/>'
        f'<ellipse cx="82" cy="34" rx="6.4" ry="3.6" transform="rotate(16 82 34)" fill="#ecd2a6" {s(1.6)}/>'
    )
    o.append(
        f'<ellipse cx="22" cy="63" rx="14" ry="21" fill="#ecd2a6" {s()}/>'
        '<ellipse cx="22" cy="63" rx="9.4" ry="14.6" fill="none" stroke="#b9895a" stroke-width="1.5"/>'
        '<ellipse cx="22" cy="63" rx="4.6" ry="7.6" fill="none" stroke="#b9895a" stroke-width="1.5"/>'
        '<circle cx="22" cy="63" r="1.4" fill="#8a5a33"/>'
    )
    # A dusting of snow along the top, then holly at the candle's foot.
    o.append(
        f'<path d="M26 44Q30 40 40 42H82Q86 44 87 48Q80 53 75 48Q70 46 66 50Q58 54 52 49Q44 46 38 50Q32 52 26 44Z" fill="#fffdf6" {s(1.4)}/>'
    )
    o.append(_holly_leaf(52, 47, 152, 26, 9))
    o.append(_holly_leaf(64, 47, 28, 26, 9))
    o.append(_berry(54, 49, 4.2) + _berry(62, 49, 4.2) + _berry(58, 53, 4.2))
    return _cell(w, h, *o)


# -------------------------------------------------------------------------------- New Year
def _coupe(x, y, half=10.5):
    """A champagne coupe with its rim at y; 18px tall, so rows stack rim to foot."""
    return (
        f'<path d="M{f(x)} {f(y + 9)}V{f(y + 16)}" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
        f'<path d="M{f(x)} {f(y + 9)}V{f(y + 16)}" stroke="#eef6f8" stroke-width="1"/>'
        f'<ellipse cx="{f(x)}" cy="{f(y + 16.6)}" rx="{f(half * 0.52)}" ry="1.6" fill="#eef6f8" {s(1.1)}/>'
        f'<path d="M{f(x - half)} {f(y)}Q{f(x - half + 1)} {f(y + 10.5)} {f(x)} {f(y + 10.5)}Q{f(x + half - 1)} {f(y + 10.5)} {f(x + half)} {f(y)}Z" fill="{grad("win-straw")}" {s(1.9)}/>'
        f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(half)}" ry="2.7" fill="#fff4bf" {s(1.6)}/>'
    )


def champagne_tower(w, h):
    o = [shadow(50, 87, 34, 7)]
    # A small round table under a short midnight-blue cloth, on gold legs.
    for x, foot in ((30, 22), (70, 78)):
        o.append(k.outlined(f"M{x} 70L{foot} 87", "#c8952f", 3))
    o.append(k.outlined("M50 70V88", "#c8952f", 3))
    o.append(
        f'<path d="M5 59V71Q13 79 20 72Q28 80 35 73Q43 81 50 74Q57 81 65 73Q72 80 80 72Q87 79 95 71V59Z" fill="{grad("win-navy")}" {s()}/>'
        f'<ellipse cx="50" cy="59" rx="45" ry="7.4" fill="#4d6699" {s()}/>'
    )
    # Rows of 4, 3, 2 and 1, each glass standing where two rims below it meet.
    for count, y in ((4, 41), (3, 23), (2, 5), (1, -13)):
        for i in range(count):
            o.append(_coupe(50 + (i - (count - 1) / 2) * 21, y))
    o.append(_sparkle(20, -3, 8) + _sparkle(80, -12, 9) + _sparkle(28, -22, 5))
    return _cell(w, h, *o)


def ice_bucket(w, h):
    o = [shadow(50, 87, 36, 8)]
    # Ring handles behind the rim.
    for x in (15, 85):
        o.append(
            f'<circle cx="{x}" cy="50" r="8" fill="none" stroke="{INK}" stroke-width="5.2"/>'
            f'<circle cx="{x}" cy="50" r="8" fill="none" stroke="#c9d3d7" stroke-width="2.6"/>'
        )
    # Inside of the far rim, ice behind the bottle.
    o.append(f'<ellipse cx="50" cy="38" rx="32" ry="10" fill="#6f7f87" {s()}/>')
    for x, y, r in ((30, 32, -12), (44, 30, 14)):
        o.append(
            f'<rect x="{x - 7}" y="{y - 7}" width="14" height="14" rx="3" transform="rotate({r} {x} {y})" fill="#d6f0f8" {s(1.4)}/>'
        )
    # The bottle leans out of the ice: dark glass, gold foil, a cork.
    o.append(
        '<g transform="translate(58 40) rotate(13)">'
        f'<path d="M-11 22V-16Q-11 -26 -5 -33V-52H5V-33Q11 -26 11 -16V22Z" fill="{grad("win-bottle")}" {s()}/>'
        f'<path d="M-5.6 -32V-52H5.6V-32Q0 -28 -5.6 -32Z" fill="{grad("win-gold")}" {s(1.4)}/>'
        f'<path d="M-5 -59Q-7 -64 0 -64Q7 -64 5 -59L3.4 -52H-3.4Z" fill="#e3c08e" {s(1.5)}/>'
        f'<rect x="-9" y="-20" width="18" height="20" rx="1.5" fill="#f6efe0" {s(1.2)}/>'
        '<path d="M-5 -14H5M-5 -9H5" stroke="#c8952f" stroke-width="1.8" stroke-linecap="round"/>'
        '<path d="M-7.6 -26Q-8.6 -20 -8 -14" fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-width="1.8"/>'
        "</g>"
    )
    for x, y, r in (
        (38, 40, 8),
        (52, 42, -14),
        (72, 37, 20),
        (62, 42, 6),
        (27, 40, -8),
    ):
        o.append(
            f'<rect x="{x - 7}" y="{y - 7}" width="14" height="14" rx="3" transform="rotate({r} {x} {y})" fill="#e6f7fb" {s(1.4)}/>'
        )
    # The bucket itself, rolled rim and all.
    o.append(
        f'<path d="M18 40Q50 56 82 40L74 82Q50 92 26 82Z" fill="{grad("win-silver")}" {s()}/>'
        '<path d="M28 50L33 80" stroke="#ffffff" stroke-opacity=".85" stroke-width="4.2" stroke-linecap="round"/>'
        '<path d="M68 52L64 80" stroke="#6f7f87" stroke-opacity=".55" stroke-width="3.4" stroke-linecap="round"/>'
        '<path d="M24 72Q50 84 76 72" fill="none" stroke="#7d8a90" stroke-width="1.8"/>'
    )
    o.append(k.outlined("M18 40Q50 56 82 40", "#e8eef0", 3.6, ink_width=6.4))
    return _cell(w, h, *o)


def _balloon(x, y, rx, ry, colour):
    tie = y + ry
    return (
        f'<path d="M{f(x)} {f(tie - 1)}L{f(x - 3.4)} {f(tie + 4.4)}H{f(x + 3.4)}Z" fill="{colour}" {s(1.3)}/>'
        f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(ry)}" fill="{colour}" {s()}/>'
        f'<ellipse cx="{f(x - rx * 0.38)}" cy="{f(y - ry * 0.42)}" rx="{f(rx * 0.2)}" ry="{f(ry * 0.3)}" '
        f'transform="rotate(24 {f(x - rx * 0.38)} {f(y - ry * 0.42)})" fill="#ffffff" fill-opacity=".7"/>'
    )


def party_balloons(w, h):
    o = [shadow(50, 87, 20, 6)]
    balloons = (
        (50, -16, 15, 18, "#f4c62f"),
        (24, 0, 15, 18, "#e23b33"),
        (76, 0, 15, 18, "#3f83d8"),
        (37, 24, 15, 18, "#3fa873"),
        (64, 25, 15, 18, "#d9539c"),
    )
    strings = "".join(
        f"M{x} {y + ry + 4}Q{f(50 + (x - 50) * 0.3)} 52 50 64.5"
        for x, y, _, ry, _ in balloons
    )
    # Pale with a dark edge, so the strings show on any floor.
    o.append(k.outlined(strings, "#f6efe0", 0.8, ink_width=1.8))
    for b in balloons:
        o.append(_balloon(*b))
    # The strings all gather at a small brass weight on the floor.
    o.append(
        f'<circle cx="50" cy="68" r="3.8" fill="none" stroke="{INK}" stroke-width="3.2"/>'
        '<circle cx="50" cy="68" r="3.8" fill="none" stroke="#e2c27a" stroke-width="1.4"/>'
        f'<path d="M37 87L41 76Q50 69 59 76L63 87Q50 92 37 87Z" fill="{grad("brass")}" {s()}/>'
        '<path d="M42 84L44 77" stroke="#ffffff" stroke-opacity=".6" stroke-width="2" stroke-linecap="round"/>'
    )
    return _cell(w, h, *o)


def _rocket(x, y, angle, length, body, band, nose):
    """A rocket rising from (x, y) inside the crate, leaning `angle` degrees from upright."""
    return (
        f'<g transform="translate({f(x)} {f(y)}) rotate({f(angle)})">'
        f'<rect x="-6.4" y="{f(-length)}" width="12.8" height="{f(length + 8)}" fill="{body}" {s()}/>'
        f'<rect x="-6.4" y="{f(-length + 8)}" width="12.8" height="6" fill="{band}" {s(1)}/>'
        f'<rect x="-6.4" y="{f(-length + 20)}" width="12.8" height="6" fill="{band}" {s(1)}/>'
        f'<path d="M-8.4 {f(-length)}L0 {f(-length - 16)}L8.4 {f(-length)}Z" fill="{nose}" {s()}/>'
        f'<path d="M-3.6 {f(-length + 2)}V{f(-length + 30)}" stroke="#ffffff" stroke-opacity=".35" stroke-width="2"/></g>'
    )


def firework_crate(w, h):
    x0, x1, top, front, bottom = 12, 80, 40, 54, 88
    o = [shadow(50, 87, 42, 7)]
    # Open top first, rockets in it, then the crate's front in front of them.
    o.append(
        f'<path d="M{x0} {front}L{x0 + 8} {top}H{x1 + 8}L{x1} {front}Z" fill="#4a2f1a" {s(1.8)}/>'
    )
    o.append(_rocket(36, 50, -3, 44, "#3f83d8", "#f6efe0", "#e23b33"))
    o.append(_rocket(62, 50, 8, 38, "#3fa873", "#f6efe0", "#f4c62f"))
    o.append(_rocket(22, 54, -16, 30, "#f4c62f", "#e23b33", "#3f83d8"))
    o.append(_rocket(49, 54, 2, 28, "#e23b33", "#f6efe0", "#3f83d8"))
    o.append(_rocket(74, 54, 18, 26, "#a55bc4", "#f6efe0", "#f4c62f"))
    o.append(
        f'<rect x="{x0}" y="{front}" width="{x1 - x0}" height="{bottom - front}" rx="2" fill="{grad("win-crate")}" {s()}/>'
        f'<path d="M{x0 + 2} {front + 11.5}H{x1 - 2}M{x0 + 2} {front + 23}H{x1 - 2}" stroke="#7d5131" stroke-width="1.6"/>'
        f'<path d="M{x0 + 7} {front}V{bottom}M{x1 - 7} {front}V{bottom}" stroke="#7d5131" stroke-width="1.6"/>'
        f'<path d="M{x1} {front}L{x1 + 8} {top}V{bottom - 8}L{x1} {bottom}Z" fill="#7d5131" {s(1.8)}/>'
    )
    # A stencilled burst in place of any lettering.
    burst = "".join(
        f"{'M' if i == 0 else 'L'}{f(46 + (13 if i % 2 == 0 else 5.4) * math.cos(math.radians(i * 30 - 90)))} "
        f"{f(71 + (13 if i % 2 == 0 else 5.4) * math.sin(math.radians(i * 30 - 90)))}"
        for i in range(12)
    )
    o.append(f'<path d="{burst}Z" fill="#c8362f" {s(1.2)}/>')
    return _cell(w, h, *o)


SKINS = {
    "black_cat": black_cat,
    "cracked_mirror": cracked_mirror,
    "cursed_idol": cursed_idol,
    "wheat_sheaf": wheat_sheaf,
    "cornucopia": cornucopia,
    "giant_pumpkin": giant_pumpkin,
    "christmas_tree": christmas_tree,
    "gift_pile": gift_pile,
    "plum_pudding": plum_pudding,
    "yule_log": yule_log,
    "champagne_tower": champagne_tower,
    "ice_bucket": ice_bucket,
    "party_balloons": party_balloons,
    "firework_crate": firework_crate,
}
# Every one of them reaches above the 26px wall face behind it.
TALL = set(SKINS)
