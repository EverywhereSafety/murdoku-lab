"""Spring holiday props: Lunar New Year and the Lantern Festival, Valentine's Day, St Patrick's Day.

On these dates the daily case renames and redraws a few prop kinds, so the board feels festive.
Every drawing here is a one-cell blocking landmark.
"""

import math

from . import _kit as k
from ._kit import INK, f, grad, s, shadow

GRADIENTS = {
    "spring-lantern": ("#ee4b3a", "#b81d1f"),
    "spring-gilt": ("#f6d873", "#c9932f"),
    "spring-paper": ("#fff3c4", "#f6c453"),
    "spring-glaze": ("#4f86c6", "#1f4f8f"),
    "spring-orange": ("#ffb347", "#ee7f16"),
    "spring-canopy": ("#5d9a55", "#2f6b3c"),
    "spring-rose": ("#e5303f", "#a9142a"),
    "spring-satin": ("#ec4650", "#bd2233"),
    "spring-iron": ("#54555b", "#1b1b20"),
}


# ------------------------------------------------------------------- shared little drawings
def _leaf(x, y, length, angle, fill="#4f8a45", line=1.4, fat=0.34):
    """A pointed leaf growing from (x, y) along `angle` degrees (0 is east, -90 is north)."""
    half = length * fat
    return (
        f'<path d="M0 0Q{f(length * 0.45)} {f(-half)} {f(length)} 0Q{f(length * 0.45)} {f(half)} 0 0Z" '
        f'transform="translate({f(x)} {f(y)}) rotate({angle})" fill="{fill}" {s(line)}/>'
    )


def _scallop(cx, cy, rx, ry, n, bulge=1.16):
    """A bumpy ellipse outline, for a head of foliage."""
    pts = [
        (
            cx + rx * math.cos(2 * math.pi * i / n),
            cy + ry * math.sin(2 * math.pi * i / n),
        )
        for i in range(n)
    ]
    d = [f"M{f(pts[0][0])} {f(pts[0][1])}"]
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        c = (cx + rx * bulge * math.cos(a), cy + ry * bulge * math.sin(a))
        p = pts[(i + 1) % n]
        d.append(f"Q{f(c[0])} {f(c[1])} {f(p[0])} {f(p[1])}")
    return "".join(d) + "Z"


def _tassel(x, top, bottom, half=7, fill="spring-gilt", thread="#a8742a"):
    """A knot on a cord above a tapering fringe, hanging from (x, top) down to (x, bottom)."""
    r = max(1.8, half * 0.48)
    knot = top + r + 1.5
    narrow = half * 0.56
    lines = "".join(
        f"M{f(x + half * t)} {f(knot + r + 2)}V{f(bottom - 1)}" for t in (-0.5, 0, 0.5)
    )
    return (
        f'<path d="M{f(x)} {f(top)}V{f(knot)}" stroke="{INK}" stroke-width="2"/>'
        f'<path d="M{f(x - narrow)} {f(knot + r)}L{f(x - half)} {f(bottom)}H{f(x + half)}L{f(x + narrow)} {f(knot + r)}Z" fill="{grad(fill)}" {s(1.4)}/>'
        f'<path d="{lines}" stroke="{thread}" stroke-width="1.1"/>'
        f'<circle cx="{f(x)}" cy="{f(knot)}" r="{f(r)}" fill="{grad(fill)}" {s(1.3)}/>'
    )


def _bow(x, y, r, fill, shade):
    """A ribbon bow tied at (x, y): two tails, two loops and a knot; r is one loop's reach."""
    o = []
    for side in (-1, 1):
        o.append(
            f'<path d="M{f(x)} {f(y)}L{f(x + side * r * 0.85)} {f(y + r * 1.2)}L{f(x + side * r * 0.5)} {f(y + r * 1.0)}'
            f'L{f(x + side * r * 0.3)} {f(y + r * 1.35)}Z" fill="{shade}" {s(1.5)}/>'
        )
    for side in (-1, 1):
        o.append(
            f'<path d="M{f(x)} {f(y)}C{f(x + side * r * 0.5)} {f(y - r * 0.9)} {f(x + side * r * 1.2)} {f(y - r * 0.8)} {f(x + side * r * 1.15)} {f(y - r * 0.05)}'
            f'C{f(x + side * r * 1.15)} {f(y + r * 0.55)} {f(x + side * r * 0.45)} {f(y + r * 0.45)} {f(x)} {f(y)}Z" fill="{fill}" {s(1.5)}/>'
        )
    o.append(
        f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r * 0.27)}" ry="{f(r * 0.32)}" fill="{shade}" {s(1.4)}/>'
    )
    return "".join(o)


def _heart(cx, top, half, height):
    """A heart's outline: lobes topping out at `top`, tip at `top + height`, `half` wide a side."""

    def p(u, v):
        return f"{f(cx + u * half)} {f(top + v * height)}"

    return (
        f"M{p(0, 0.2)}"
        f"C{p(0.1, 0.02)} {p(0.38, -0.03)} {p(0.6, 0)}"
        f"C{p(0.9, 0.03)} {p(1.03, 0.26)} {p(1, 0.42)}"
        f"C{p(0.96, 0.66)} {p(0.36, 0.88)} {p(0.08, 0.99)}"
        f"Q{p(0, 1.02)} {p(-0.08, 0.99)}"
        f"C{p(-0.36, 0.88)} {p(-0.96, 0.66)} {p(-1, 0.42)}"
        f"C{p(-1.03, 0.26)} {p(-0.9, 0.03)} {p(-0.6, 0)}"
        f"C{p(-0.38, -0.03)} {p(-0.1, 0.02)} {p(0, 0.2)}Z"
    )


# ------------------------------------------------------- Lunar New Year, Lantern Festival
def red_lantern(w, h):
    cx, base = w / 2, h - 12
    post, lx, ly, rx, ry = cx - 28, cx + 12, base - 52, 31, 26
    o = [shadow(cx, base, 36, 7)]
    o.append(
        f'<rect x="{f(post - 7)}" y="{f(base - 8)}" width="20" height="9" rx="2.5" fill="{grad("walnut")}" {s(1.8)}/>'
    )
    o.append(
        k.outlined(f"M{f(post)} {f(base - 6)}V{f(base - 94)}", "#9a6a43", 5, cap="butt")
    )
    o.append(
        k.outlined(
            f"M{f(post)} {f(base - 72)}L{f(post + 15)} {f(base - 92)}", "#9a6a43", 3
        )
    )
    o.append(
        k.outlined(
            f"M{f(post - 3)} {f(base - 94)}H{f(lx + 12)}q6 0 6 -5", "#b9824f", 4.4
        )
    )
    o.append(
        f'<ellipse cx="{f(lx)}" cy="{f(ly)}" rx="{rx + 6}" ry="{ry + 6}" fill="#ffd56b" fill-opacity=".55" filter="url(#mk-soft)"/>'
    )
    o.append(
        f'<path d="M{f(lx)} {f(base - 94)}V{f(ly - ry)}" stroke="{INK}" stroke-width="2"/>'
    )
    o.append(_tassel(lx, ly + ry + 2, base - 2))
    o.append(
        f'<ellipse cx="{f(lx)}" cy="{f(ly)}" rx="{rx}" ry="{ry}" fill="{grad("spring-lantern")}" {s()}/>'
    )
    ribs = "".join(
        f'<ellipse cx="{f(lx)}" cy="{f(ly)}" rx="{f(rx * t)}" ry="{ry}"/>'
        for t in (0.72, 0.36)
    )
    o.append(f'<g fill="none" stroke="#8c1418" stroke-width="1.5">{ribs}</g>')
    o.append(
        f'<path d="M{f(lx)} {f(ly - ry)}V{f(ly + ry)}" stroke="#8c1418" stroke-width="1.5"/>'
    )
    o.append(
        k.highlight(
            f"M{f(lx - rx + 7)} {f(ly - 8)}Q{f(lx - rx + 12)} {f(ly - ry + 6)} {f(lx - 8)} {f(ly - ry + 3)}",
            0.5,
            3,
        )
    )
    for y, wide, narrow in ((ly - ry - 5, 8, 12), (ly + ry - 3, 12, 8)):
        o.append(
            f'<path d="M{f(lx - wide)} {f(y)}H{f(lx + wide)}L{f(lx + narrow)} {f(y + 8)}H{f(lx - narrow)}Z" fill="{grad("spring-gilt")}" {s(1.7)}/>'
        )
    return "".join(o)


def _storey(cx, top, bottom, half):
    """One paper storey of a tiered lantern: a bulging drum with thin wooden ribs."""
    mid = (top + bottom) / 2
    ribs = "".join(
        f"M{f(cx + side * half * 0.42)} {f(top)}Q{f(cx + side * half * 0.56)} {f(mid)} {f(cx + side * half * 0.42)} {f(bottom)}"
        for side in (-1, 1)
    )
    return (
        f'<path d="M{f(cx - half)} {f(top)}Q{f(cx - half - 7)} {f(mid)} {f(cx - half)} {f(bottom)}H{f(cx + half)}Q{f(cx + half + 7)} {f(mid)} {f(cx + half)} {f(top)}Z" fill="{grad("spring-paper")}" {s(1.8)}/>'
        f'<path d="{ribs}" stroke="#b5702f" stroke-width="1.3" fill="none"/>'
    )


def _eave(cx, y, half):
    """A little upturned red roof with its underside at about y."""
    return (
        f'<path d="M{f(cx - half)} {f(y - 3)}Q{f(cx - half * 0.8)} {f(y + 3)} {f(cx - half * 0.55)} {f(y + 3)}'
        f"H{f(cx + half * 0.55)}Q{f(cx + half * 0.8)} {f(y + 3)} {f(cx + half)} {f(y - 3)}"
        f'L{f(cx + half * 0.6)} {f(y - 7)}H{f(cx - half * 0.6)}Z" fill="{grad("spring-lantern")}" {s(1.6)}/>'
    )


def lantern_stand(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx, base, 30, 7)]
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx + side * 20)} {f(base + 1)}L{f(cx)} {f(base - 26)}",
                "#7a4d33",
                4.4,
            )
        )
    o.append(k.outlined(f"M{f(cx)} {f(base - 1)}V{f(base - 58)}", "#9a6a43", 5.4))
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx)} {f(base - 42)}L{f(cx + side * 13)} {f(base - 56)}",
                "#9a6a43",
                2.8,
            )
        )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{f(base - 88)}" rx="33" ry="33" fill="#ffd56b" fill-opacity=".55" filter="url(#mk-soft)"/>'
    )
    o.append(_storey(cx, base - 82, base - 60, 24))
    o.append(
        f'<rect x="{f(cx - 26)}" y="{f(base - 62)}" width="52" height="6" rx="2.4" fill="{grad("spring-lantern")}" {s(1.6)}/>'
    )
    for side in (-1, 1):
        o.append(
            _tassel(
                cx + side * 33, base - 86, base - 66, 3.8, "spring-lantern", "#8c1418"
            )
        )
    o.append(_eave(cx, base - 82, 33))
    o.append(_storey(cx, base - 102, base - 84, 18))
    o.append(_eave(cx, base - 102, 25))
    o.append(_storey(cx, base - 115, base - 104, 12))
    o.append(_eave(cx, base - 115, 18))
    o.append(
        f'<circle cx="{f(cx)}" cy="{f(base - 121)}" r="2.6" fill="{grad("spring-gilt")}" {s(1.2)}/>'
    )
    return "".join(o)


def kumquat_tree(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx, base + 1, 28, 7)]
    for x, y, angle in ((-10, -108, -125), (5, -110, -80), (20, -106, -45)):
        o.append(_leaf(cx + x, base + y, 12, angle, "#4f8a45", fat=0.42))
    o.append(
        f'<path d="{_scallop(cx, base - 79, 36, 31, 13)}" fill="{grad("spring-canopy")}" {s()}/>'
    )
    for x, y, angle in (
        (-30, -92, -30),
        (-16, -65, 200),
        (-2, -96, 160),
        (11, -64, -20),
        (25, -80, 30),
        (-19, -78, 20),
    ):
        o.append(_leaf(cx + x, base + y, 10, angle, "#7fb86a", 1, 0.4))
    for x, y in (
        (0, -111),
        (-12, -100),
        (11, -100),
        (-36, -86),
        (-22, -87),
        (0, -87),
        (22, -88),
        (37, -87),
        (-31, -73),
        (-10, -74),
        (11, -75),
        (32, -72),
        (-34, -60),
        (-21, -59),
        (0, -61),
        (21, -59),
        (34, -59),
    ):
        px, py = cx + x, base + y
        o.append(
            f'<circle cx="{f(px)}" cy="{f(py)}" r="6.4" fill="{grad("spring-orange")}" {s(1.3)}/>'
            f'<circle cx="{f(px - 2)}" cy="{f(py - 2.2)}" r="1.5" fill="#ffffff" fill-opacity=".75"/>'
        )
    o.append(
        f'<path d="M{f(cx - 23)} {f(base - 36)}Q{f(cx - 30)} {f(base - 16)} {f(cx - 15)} {f(base)}H{f(cx + 15)}Q{f(cx + 30)} {f(base - 16)} {f(cx + 23)} {f(base - 36)}Z" fill="{grad("spring-glaze")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 24)} {f(base - 15)}Q{f(cx)} {f(base - 9)} {f(cx + 24)} {f(base - 15)}" stroke="#f3e3b0" stroke-width="2.2" fill="none"/>'
    )
    o.append(
        k.highlight(
            f"M{f(cx - 18)} {f(base - 30)}Q{f(cx - 22)} {f(base - 18)} {f(cx - 15)} {f(base - 8)}",
            0.7,
            3,
        )
    )
    o.append(
        f'<rect x="{f(cx - 26)}" y="{f(base - 42)}" width="52" height="8" rx="3" fill="#7fb0dc" {s(1.8)}/>'
    )
    o.append(_bow(cx, base - 46, 14, "#e23a33", "#b3201f"))
    return "".join(o)


def _orange(x, y, r):
    return (
        f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{grad("spring-orange")}" {s(1.8)}/>'
        + k.highlight(
            f"M{f(x - r * 0.6)} {f(y - r * 0.2)}Q{f(x - r * 0.5)} {f(y - r * 0.6)} {f(x - r * 0.1)} {f(y - r * 0.68)}",
            0.65,
            2.2,
        )
    )


def orange_pyramid(w, h):
    cx, base = w / 2, h - 12
    r, plate = 11, base - 14
    o = [shadow(cx, base, 42, 8)]
    o.append(
        f'<path d="M{f(cx - 20)} {f(base - 5)}L{f(cx - 24)} {f(base + 1)}H{f(cx + 24)}L{f(cx + 20)} {f(base - 5)}Z" fill="{grad("spring-gilt")}" {s(1.7)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 47)} {f(plate)}Q{f(cx - 34)} {f(base - 2)} {f(cx)} {f(base - 2)}Q{f(cx + 34)} {f(base - 2)} {f(cx + 47)} {f(plate)}Z" fill="#8f1a1c" {s()}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{f(plate)}" rx="47" ry="11" fill="{grad("spring-lantern")}" {s()}/>'
        f'<ellipse cx="{f(cx)}" cy="{f(plate)}" rx="41" ry="8.2" fill="none" stroke="#f6d873" stroke-width="1.8"/>'
    )
    for row in range(3, -1, -1):
        count = 4 - row
        y = plate - r + 3 - row * r * 1.72
        for i in range(count):
            o.append(_orange(cx + (i - (count - 1) / 2) * r * 2, y, r))
    top = plate - r + 3 - 3 * r * 1.72
    o.append(_leaf(cx + 1, top - r + 1, 12, -35, "#5d9a55"))
    return "".join(o)


def _rice_ball(x, y, r, pink):
    body, shade = ("#f8aec4", "#e5849f") if pink else ("#fffdf7", "#e4dccb")
    return (
        f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{body}" {s(1.8)}/>'
        f'<path d="M{f(x + r * 0.15)} {f(y + r * 0.72)}Q{f(x + r * 0.72)} {f(y + r * 0.6)} {f(x + r * 0.72)} {f(y + r * 0.1)}" stroke="{shade}" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
        f'<circle cx="{f(x - r * 0.34)}" cy="{f(y - r * 0.36)}" r="{f(r * 0.17)}" fill="#ffffff" fill-opacity=".9"/>'
    )


def rice_balls(w, h):
    cx, base = w / 2, h - 12
    rim, rx, ry = base - 42, 38, 11
    o = [shadow(cx, base, 36, 7)]
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{f(rim)}" rx="{rx}" ry="{ry}" fill="#f3e0b4" {s()}/>'
    )
    for x, y, r, pink in (
        (-4, -25, 11.5, False),
        (-23, -15, 11, True),
        (15, -17, 11, True),
        (-31, -3, 10, False),
        (-10, -6, 11.5, False),
        (29, -5, 10.5, False),
        (10, -2, 11, True),
    ):
        o.append(_rice_ball(cx + x, rim + y, r, pink))
    o.append(
        f'<path d="M{f(cx - rx)} {f(rim)}A{rx} {ry} 0 0 0 {f(cx + rx)} {f(rim)}'
        f'Q{f(cx + rx - 3)} {f(base - 8)} {f(cx + 16)} {f(base - 4)}H{f(cx - 16)}Q{f(cx - rx + 3)} {f(base - 8)} {f(cx - rx)} {f(rim)}Z" fill="{grad("spring-glaze")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 33)} {f(rim + 18)}Q{f(cx)} {f(rim + 29)} {f(cx + 33)} {f(rim + 18)}" stroke="#f6efe0" stroke-width="2.6" fill="none"/>'
    )
    o.append(
        k.highlight(
            f"M{f(cx - 31)} {f(rim + 11)}Q{f(cx - 26)} {f(rim + 22)} {f(cx - 17)} {f(rim + 28)}",
            0.6,
            2.8,
        )
    )
    o.append(
        f'<path d="M{f(cx - 16)} {f(base - 5)}L{f(cx - 19)} {f(base + 1)}H{f(cx + 19)}L{f(cx + 16)} {f(base - 5)}Z" fill="#7fb0dc" {s(1.7)}/>'
    )
    o.append(
        k.outlined(
            f"M{f(cx + 24)} {f(rim - 6)}L{f(cx + 44)} {f(rim - 38)}",
            "#7fb0dc",
            5,
            ink_width=8,
        )
    )
    o.append(
        f'<ellipse cx="{f(cx + 19)}" cy="{f(rim - 3)}" rx="13" ry="8.6" transform="rotate(-48 {f(cx + 19)} {f(rim - 3)})" fill="#7fb0dc" {s(1.8)}/>'
        f'<ellipse cx="{f(cx + 18.5)}" cy="{f(rim - 2.5)}" rx="8.4" ry="5" transform="rotate(-48 {f(cx + 18.5)} {f(rim - 2.5)})" fill="#e7f1f9"/>'
    )
    return "".join(o)


# ------------------------------------------------------------------------ Valentine's Day
def _rose(x, y, r, rot=0):
    """A full rose at three quarters: a cup of wrapped petals around a spiral heart."""

    def n(v):
        return f(v * r)

    return (
        f'<g transform="translate({f(x)} {f(y)}) rotate({rot})">'
        f'<path d="M{n(-1)} {n(-0.25)}C{n(-1.06)} {n(0.45)} {n(-0.55)} {n(1)} 0 {n(1)}C{n(0.55)} {n(1)} {n(1.06)} {n(0.45)} {n(1)} {n(-0.25)}'
        f'C{n(0.95)} {n(-0.82)} {n(0.45)} {n(-1)} 0 {n(-0.96)}C{n(-0.45)} {n(-1)} {n(-0.95)} {n(-0.82)} {n(-1)} {n(-0.25)}Z" fill="{grad("spring-rose")}" {s(1.5)}/>'
        f'<ellipse cy="{n(-0.3)}" rx="{n(0.66)}" ry="{n(0.44)}" fill="#8f1022" stroke="#6d0c1a" stroke-width="1.1"/>'
        f'<path d="M{n(-0.3)} {n(-0.32)}C{n(-0.24)} {n(-0.58)} {n(0.27)} {n(-0.6)} {n(0.32)} {n(-0.32)}C{n(0.35)} {n(-0.12)} {n(-0.1)} {n(-0.08)} {n(-0.12)} {n(-0.28)}C{n(-0.13)} {n(-0.42)} {n(0.1)} {n(-0.44)} {n(0.12)} {n(-0.3)}" fill="none" stroke="#ef6f78" stroke-width="1.5" stroke-linecap="round"/>'
        f'<path d="M{n(-0.97)} {n(-0.08)}C{n(-0.7)} {n(0.14)} {n(-0.2)} {n(0.42)} {n(0.22)} {n(0.94)}M{n(0.97)} {n(-0.08)}C{n(0.72)} {n(0.2)} {n(0.36)} {n(0.42)} {n(-0.08)} {n(0.56)}" fill="none" stroke="#7d0f1e" stroke-width="1.5" stroke-linecap="round"/>'
        f'<path d="M{n(-0.8)} {n(-0.42)}Q{n(-0.62)} {n(-0.8)} {n(-0.2)} {n(-0.82)}" fill="none" stroke="#f79aa2" stroke-width="1.8" stroke-linecap="round"/>'
        f"</g>"
    )


def rose_bouquet(w, h):
    cx, base = w / 2, h - 12
    lip = base - 43
    o = [shadow(cx, base + 1, 22, 6)]
    for x, y, angle in (
        (-30, -62, 150),
        (-33, -78, 180),
        (-18, -52, 118),
        (30, -62, 30),
        (33, -78, 0),
        (18, -52, 62),
        (-26, -102, -130),
        (26, -102, -50),
    ):
        o.append(_leaf(cx + x, base + y, 12.5, angle, fat=0.48))
    stems = "".join(
        f"M{f(cx + a)} {f(base - 8)}L{f(cx + b)} {f(base - 58)}"
        for a, b in ((-6, -14), (0, 0), (6, 14))
    )
    o.append(
        f'<path d="{stems}" stroke="#4f8452" stroke-width="2.8" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx - 20)} {f(lip)}L{f(cx - 12)} {f(base - 3)}Q{f(cx)} {f(base + 1)} {f(cx + 12)} {f(base - 3)}L{f(cx + 20)} {f(lip)}Z" fill="#cfe8f1" fill-opacity=".8" {s()}/>'
    )
    o.append(
        k.highlight(f"M{f(cx - 13)} {f(lip + 9)}L{f(cx - 9)} {f(base - 8)}", 0.8, 2.6)
    )
    for x, y, rot in (
        (-13, -99, -8),
        (13, -99, 8),
        (-27, -80, -16),
        (27, -80, 16),
        (0, -82, 0),
        (-14, -61, -8),
        (14, -61, 8),
    ):
        o.append(_rose(cx + x, base + y, 13.5, rot))
    band = base - 30
    o.append(
        f'<path d="M{f(cx - 16)} {f(band)}Q{f(cx)} {f(band + 5)} {f(cx + 16)} {f(band)}L{f(cx + 15)} {f(band + 6)}Q{f(cx)} {f(band + 11)} {f(cx - 15)} {f(band + 6)}Z" fill="#f28fb0" {s(1.5)}/>'
    )
    o.append(_bow(cx, band + 4, 13, "#f7a6c2", "#d9648f"))
    return "".join(o)


def chocolate_box(w, h):
    cx, base = w / 2, h - 12
    top, half, depth = base - 56, 42, 8
    o = [shadow(cx, base - 2, 40, 8)]
    lid = _heart(cx, top - 44, 36, 66)
    o.append(
        f'<g transform="rotate(-5 {f(cx)} {f(top)})">'
        f'<path d="{lid}" fill="{grad("spring-satin")}" {s()}/>'
        f'<path d="M{f(cx - 7)} {f(top - 38)}L{f(cx - 7)} {f(top + 20)}M{f(cx + 7)} {f(top - 38)}L{f(cx + 7)} {f(top + 20)}" stroke="#f6d873" stroke-width="3.4"/>'
        f"</g>"
    )
    o.append(_bow(cx - 3, top - 22, 14, "#f6d873", "#c9932f"))
    box = _heart(cx, top, half, 48)
    o.append(f'<path d="{box}" transform="translate(0 {depth})" fill="#8e1627" {s()}/>')
    o.append(f'<path d="{box}" fill="{grad("spring-satin")}" {s()}/>')
    o.append(
        f'<path d="{_heart(cx, top + 5, half - 7, 37)}" fill="#f8e7c0" stroke="#c9932f" stroke-width="1.6"/>'
    )
    for x, y, kind in (
        (-23, 15, 0),
        (-8, 14, 1),
        (8, 14, 0),
        (23, 15, 1),
        (-15, 26, 1),
        (0, 26, 0),
        (15, 26, 1),
        (0, 36, 1),
    ):
        px, py = cx + x, top + y
        colour = ("#4a2a1a", "#7b4a28")[kind]
        o.append(
            f'<ellipse cx="{f(px)}" cy="{f(py)}" rx="7" ry="6" fill="{colour}" {s(1.3)}/>'
            f'<path d="M{f(px - 3.6)} {f(py - 1.6)}Q{f(px - 2)} {f(py - 4)} {f(px + 1)} {f(py - 4)}" stroke="#ffffff" stroke-opacity=".5" stroke-width="1.5" fill="none" stroke-linecap="round"/>'
        )
        if kind == 0:
            o.append(
                f'<path d="M{f(px - 4)} {f(py + 2)}q2 -3.4 4 -0.6t4 -0.6" stroke="#f6e6c8" stroke-width="1.2" fill="none" stroke-linecap="round"/>'
            )
    return "".join(o)


def heart_cushion(w, h):
    cx, base = w / 2, h - 12
    top, half, height = base - 62, 39, 60
    o = [shadow(cx, base - 2, 40, 8)]
    heart = _heart(cx, top, half, height)
    o.append(
        f'<path d="{heart}" fill="none" stroke="{INK}" stroke-width="12" stroke-dasharray=".1 8.6" stroke-linecap="round"/>'
        f'<path d="{heart}" fill="none" stroke="#fbd5da" stroke-width="9" stroke-dasharray=".1 8.6" stroke-linecap="round"/>'
    )
    o.append(f'<path d="{heart}" fill="#ab1c2d" {s()}/>')
    o.append(
        f'<path d="{_heart(cx - 1, top + 5, half - 7, height - 14)}" fill="#ee4a53" filter="url(#mk-softer)"/>'
    )
    # The tuft under the button is a soft dent; the fold below the cleft a short crease.
    bx, by = cx, top + height * 0.5
    dent = "#a81b2c"
    o.append(
        f'<ellipse cx="{f(bx)}" cy="{f(by)}" rx="11" ry="8.6" fill="{dent}" fill-opacity=".6" filter="url(#mk-softer)"/>'
        f'<path d="M{f(cx)} {f(top + height * 0.21)}V{f(top + height * 0.31)}" stroke="{dent}" stroke-opacity=".6" stroke-width="2.2" stroke-linecap="round"/>'
        f'<ellipse cx="{f(bx)}" cy="{f(by)}" rx="4.6" ry="3.8" fill="#e0424c" {s(1.3)}/>'
        f'<circle cx="{f(bx - 1.4)}" cy="{f(by - 1.2)}" r="1.1" fill="#ffffff" fill-opacity=".7"/>'
    )
    o.append(
        k.highlight(
            f"M{f(cx - 28)} {f(top + 19)}Q{f(cx - 26)} {f(top + 8)} {f(cx - 14)} {f(top + 8)}",
            0.65,
            3.4,
        )
    )
    o.append(k.highlight(f"M{f(cx + 15)} {f(top + 9)}h5", 0.45, 2.6))
    return "".join(o)


# ----------------------------------------------------------------------- St Patrick's Day
def _shamrock(x, y, r, fill="#5fbf57", rot=0):
    """A three-lobed clover leaf centred on (x, y); each lobe is a small heart reaching r."""

    def n(v):
        return f(v * r)

    lobe = (
        f"M0 0C{n(-0.18)} {n(-0.3)} {n(-0.74)} {n(-0.42)} {n(-0.64)} {n(-0.82)}"
        f"C{n(-0.56)} {n(-1.14)} {n(-0.14)} {n(-1.14)} 0 {n(-0.78)}"
        f"C{n(0.14)} {n(-1.14)} {n(0.56)} {n(-1.14)} {n(0.64)} {n(-0.82)}"
        f"C{n(0.74)} {n(-0.42)} {n(0.18)} {n(-0.3)} 0 0Z"
    )
    lobes = "".join(
        f'<g transform="rotate({a})"><path d="{lobe}" fill="{fill}" {s(1.6)}/>'
        f'<path d="M{n(-0.28)} {n(-0.52)}L0 {n(-0.36)}L{n(0.28)} {n(-0.52)}" stroke="#d8f2bd" stroke-width="1.5" fill="none" stroke-linecap="round"/></g>'
        for a in (0, 120, 240)
    )
    return f'<g transform="translate({f(x)} {f(y)}) rotate({rot})">{lobes}</g>'


def shamrock_pot(w, h):
    cx, base = w / 2, h - 12
    rim = base - 36
    o = [shadow(cx, base + 1, 24, 6)]
    leaves = (
        (0, -86, 19, "#4fae4e", 0),
        (-28, -63, 16, "#5fbf57", -18),
        (28, -65, 16, "#5fbf57", 16),
        (0, -52, 12, "#6ccb62", 0),
    )
    stems = "".join(
        f"M{f(cx + x * 0.2)} {f(rim)}Q{f(cx + x * 0.5)} {f(base + y * 0.6 - 10)} {f(cx + x)} {f(base + y)}"
        for x, y, *_ in leaves
    )
    o.append(k.outlined(stems, "#4f9a4c", 2.6, ink_width=4.4))
    for x, y, r, fill, rot in leaves:
        o.append(_shamrock(cx + x, base + y, r, fill, rot))
    o.append(
        f'<path d="M{f(cx - 21)} {f(rim)}L{f(cx - 16)} {f(base)}H{f(cx + 16)}L{f(cx + 21)} {f(rim)}Z" fill="{grad("terra")}" {s()}/>'
        f'<rect x="{f(cx - 24)}" y="{f(rim - 6)}" width="48" height="9" rx="3" fill="#e39a69" {s(1.8)}/>'
        f'<path d="M{f(cx - 13)} {f(rim + 11)}h8" stroke="#ffffff" stroke-opacity=".45" stroke-width="2.4" stroke-linecap="round"/>'
    )
    return "".join(o)


def green_keg(w, h):
    cx, base = w / 2, h - 12
    kx, top, bottom = cx - 20, base - 68, base - 12
    half = 23
    mid = (top + bottom) / 2
    o = [shadow(cx - 4, base, 42, 8)]
    for side in (-1, 1):
        o.append(
            f'<path d="M{f(kx + side * 19)} {f(bottom)}L{f(kx + side * 16)} {f(base + 1)}H{f(kx + side * 8)}L{f(kx + side * 8)} {f(bottom)}Z" fill="{grad("walnut")}" {s(1.7)}/>'
        )
    o.append(
        f'<path d="M{f(kx - half)} {f(top + 7)}Q{f(kx - half - 7)} {f(mid)} {f(kx - half)} {f(bottom)}Q{f(kx)} {f(bottom + 8)} {f(kx + half)} {f(bottom)}'
        f'Q{f(kx + half + 7)} {f(mid)} {f(kx + half)} {f(top + 7)}Z" fill="{grad("barrel")}" {s()}/>'
    )
    for sx in (-11, 0, 11):
        o.append(
            f'<path d="M{f(kx + sx)} {f(top + 9)}Q{f(kx + sx * 1.15)} {f(mid)} {f(kx + sx)} {f(bottom + 2)}" stroke="#8a5530" stroke-width="1.4" fill="none"/>'
        )
    for yy in (top + 15, bottom - 12):
        o.append(
            f'<path d="M{f(kx - half - 3.5)} {f(yy)}Q{f(kx)} {f(yy + 7)} {f(kx + half + 3.5)} {f(yy)}" stroke="{INK}" stroke-width="8.6" fill="none"/>'
            f'<path d="M{f(kx - half - 3)} {f(yy)}Q{f(kx)} {f(yy + 7)} {f(kx + half + 3)} {f(yy)}" stroke="#2fa34f" stroke-width="6" fill="none"/>'
        )
    o.append(
        f'<ellipse cx="{f(kx)}" cy="{f(top + 7)}" rx="{half}" ry="7" fill="#d9a06a" {s()}/>'
        f'<ellipse cx="{f(kx)}" cy="{f(top + 7)}" rx="{half - 7}" ry="4.4" fill="none" stroke="#b07a48" stroke-width="1.4"/>'
        f'<ellipse cx="{f(kx + 7)}" cy="{f(top + 7)}" rx="3.2" ry="2" fill="#6f4a2c" {s(1)}/>'
    )
    o.append(_shamrock(kx - 8, mid + 3, 7.4, "#5fbf57"))
    # The tap sticks out over the mug: a brass pipe, a spout and a lever.
    mx, ty = cx + 16, top + 26
    o.append(
        k.outlined(
            f"M{f(mx - 3)} {f(ty - 1)}V{f(ty - 14)}", "#3a3f44", 3.2, ink_width=5.4
        )
    )
    o.append(
        f'<circle cx="{f(mx - 3)}" cy="{f(ty - 15)}" r="3.8" fill="#2fa34f" {s(1.3)}/>'
    )
    o.append(
        f'<path d="M{f(kx + half - 3)} {f(ty - 4)}H{f(mx + 3)}V{f(ty + 11)}H{f(mx - 3)}V{f(ty + 3)}H{f(kx + half - 3)}Z" fill="{grad("brass")}" {s(1.6)}/>'
    )
    # The mug under the tap, with a head of foam.
    mug_top, mug_bottom = ty + 21, base + 1
    o.append(
        k.outlined(
            f"M{f(mx + 12)} {f(mug_top + 5)}h4q7 0 7 7v2q0 7 -7 7h-4",
            "#e6dcc4",
            3.6,
            ink_width=6.4,
        )
    )
    o.append(
        f'<rect x="{f(mx - 13)}" y="{f(mug_top)}" width="26" height="{f(mug_bottom - mug_top)}" rx="3.6" fill="#3a2216" {s()}/>'
        f'<path d="M{f(mx - 9)} {f(mug_top + 7)}V{f(mug_bottom - 6)}" stroke="#ffffff" stroke-opacity=".4" stroke-width="2.6" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(mx - 15)} {f(mug_top + 5)}Q{f(mx - 18)} {f(mug_top - 3)} {f(mx - 9)} {f(mug_top - 4)}Q{f(mx - 6)} {f(mug_top - 10)} {f(mx + 1)} {f(mug_top - 7)}'
        f"Q{f(mx + 9)} {f(mug_top - 10)} {f(mx + 11)} {f(mug_top - 3)}Q{f(mx + 18)} {f(mug_top - 2)} {f(mx + 15)} {f(mug_top + 5)}"
        f'Q{f(mx + 11)} {f(mug_top + 8)} {f(mx + 7)} {f(mug_top + 5)}Q{f(mx + 3)} {f(mug_top + 12)} {f(mx - 1)} {f(mug_top + 5)}Q{f(mx - 8)} {f(mug_top + 9)} {f(mx - 15)} {f(mug_top + 5)}Z" fill="#fffdf6" {s(1.7)}/>'
    )
    return "".join(o)


def _coin(x, y, rx, ry, rot=0):
    return (
        f'<g transform="translate({f(x)} {f(y)}) rotate({rot})">'
        f'<ellipse rx="{f(rx)}" ry="{f(ry)}" fill="{grad("spring-gilt")}" {s(1.4)}/>'
        f'<ellipse rx="{f(rx * 0.62)}" ry="{f(ry * 0.62)}" fill="none" stroke="#a8742a" stroke-width="1.1"/>'
        f"</g>"
    )


def _glint(x, y, r):
    return (
        f'<path d="M{f(x)} {f(y - r)}Q{f(x)} {f(y)} {f(x + r)} {f(y)}Q{f(x)} {f(y)} {f(x)} {f(y + r)}'
        f'Q{f(x)} {f(y)} {f(x - r)} {f(y)}Q{f(x)} {f(y)} {f(x)} {f(y - r)}Z" fill="#ffffff"/>'
    )


def pot_of_gold(w, h):
    cx, base = w / 2, h - 12
    rim, rx, ry = base - 48, 36, 10
    o = [shadow(cx, base, 40, 8)]
    for side in (-1, 1):
        o.append(
            f'<path d="M{f(cx + side * 14)} {f(base - 8)}L{f(cx + side * 19)} {f(base + 1)}H{f(cx + side * 28)}L{f(cx + side * 27)} {f(base - 12)}Z" fill="#26262b" {s(1.8)}/>'
        )
        o.append(
            k.outlined(
                f"M{f(cx + side * 37)} {f(rim + 5)}q{f(side * 7)} 1 {f(side * 6)} 9q{f(side * -1)} 5 {f(side * -7)} 3",
                "#3a3b40",
                3.4,
            )
        )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{f(rim)}" rx="{rx}" ry="{ry}" fill="#111114" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 27)} {f(rim + 3)}Q{f(cx - 25)} {f(rim - 16)} {f(cx)} {f(rim - 20)}Q{f(cx + 25)} {f(rim - 16)} {f(cx + 27)} {f(rim + 3)}Z" fill="#c9932f"/>'
    )
    for x, y, a, b, rot in (
        (-1, -31, 8.4, 7, -12),
        (-14, -25, 8.4, 6.6, -24),
        (12, -26, 8.4, 6.6, 20),
        (-25, -15, 8.4, 6.4, -26),
        (-6, -18, 8.6, 6.8, 8),
        (20, -16, 8.4, 6.4, 26),
        (29, -6, 8, 5.6, 18),
        (-31, -6, 8, 5.6, -16),
        (-15, -7, 8.6, 6.2, -6),
        (6, -9, 8.6, 6.2, -14),
    ):
        o.append(_coin(cx + x, rim + y, a, b, rot))
    o.append(
        f'<path d="M{f(cx - rx)} {f(rim)}A{rx} {ry} 0 0 0 {f(cx + rx)} {f(rim)}'
        f"C{f(cx + 50)} {f(rim + 22)} {f(cx + 32)} {f(base - 4)} {f(cx)} {f(base - 4)}"
        f'C{f(cx - 32)} {f(base - 4)} {f(cx - 50)} {f(rim + 22)} {f(cx - rx)} {f(rim)}Z" fill="{grad("spring-iron")}" {s()}/>'
    )
    o.append(
        k.outlined(
            f"M{f(cx - rx - 2)} {f(rim)}A{rx + 2} {ry + 1} 0 0 0 {f(cx + rx + 2)} {f(rim)}",
            "#4a4b51",
            4.6,
        )
    )
    o.append(
        k.highlight(
            f"M{f(cx - 34)} {f(rim + 15)}Q{f(cx - 31)} {f(rim + 28)} {f(cx - 19)} {f(rim + 36)}",
            0.4,
            3.4,
        )
    )
    for x, y, a, b, rot in (
        (-7, 0, 8.6, 6, -6),
        (10, 2, 8.4, 5.8, 12),
        (24, -1, 7.6, 5.2, 18),
    ):
        o.append(_coin(cx + x, rim + y, a, b, rot))
    for x, y, a, b in ((-20, 4, 6.8, 3.8), (-3, 5.5, 7.4, 4), (13, 3.5, 6.8, 3.8)):
        o.append(_coin(cx + x, base + y, a, b))
    o.append(_glint(cx - 16, rim - 31, 6))
    o.append(_glint(cx + 19, rim - 30, 4.6))
    return "".join(o)


SKINS = {
    "red_lantern": red_lantern,
    "kumquat_tree": kumquat_tree,
    "orange_pyramid": orange_pyramid,
    "lantern_stand": lantern_stand,
    "rice_balls": rice_balls,
    "rose_bouquet": rose_bouquet,
    "chocolate_box": chocolate_box,
    "heart_cushion": heart_cushion,
    "shamrock_pot": shamrock_pot,
    "green_keg": green_keg,
    "pot_of_gold": pot_of_gold,
}
TALL = {
    "red_lantern",
    "kumquat_tree",
    "orange_pyramid",
    "lantern_stand",
    "rice_balls",
    "rose_bouquet",
    "chocolate_box",
    "shamrock_pot",
    "pot_of_gold",
}
