"""Casebook props in a 3/4 dollhouse view: tops lit from the upper left, fronts in shade.

A drawer works in its footprint's local frame: (0, 0)–(w, h) are the cells the formal prop
occupies (w, h are multiples of 100). Tall furniture may rise up to `OVERHANG` above the
footprint, as it would in front of a wall; the base always sits inside the footprint, so the
square a prop occupies stays readable. A theme may swap the drawing for a kind ("skin") so the
picture matches the noun its clues use.

Every drawer references the shared gradients and filters in `defs()`.
"""

import math

INK = "#2a221d"
OVERHANG = 36

# --------------------------------------------------------------------------- shared defs
_GRADIENTS = {
    "wood": ("#dcab75", "#b9824f"),
    "wood-front": ("#a8723f", "#87582f"),
    "walnut": ("#7a4d33", "#5a3826"),
    "walnut-top": ("#9a6847", "#7f5136"),
    "velvet": ("#e2b45a", "#c38d33"),
    "velvet-front": ("#b98327", "#9a6b1e"),
    "plum": ("#b06f90", "#874a69"),
    "plum-front": ("#7a3f5c", "#5f2f47"),
    "teal": ("#5fa49b", "#3f7f78"),
    "teal-front": ("#3a746d", "#2c5c57"),
    "terra": ("#d88b5c", "#b56a3f"),
    "brass": ("#e2c27a", "#b58a3c"),
    "barrel": ("#c88a55", "#9f6638"),
    "stone": ("#d9dbd0", "#a7ab9e"),
    "stone-front": ("#a3a798", "#82877a"),
    "leaf": ("#8dbd73", "#5a8f55"),
    "navy": ("#5a7a96", "#3d5a73"),
    "cream": ("#fbf5e6", "#e8dcc2"),
    "cardboard": ("#e1b582", "#c79560"),
    "metal": ("#9fb0aa", "#71817b"),
    "water": ("#9fd0da", "#6aaab8"),
    "sand": ("#f1dfac", "#dcc285"),
    "grass": ("#a7cf8a", "#7fae68"),
}


def gid(name):
    return f"mk-g-{name}"


def grad(name):
    return f"url(#{gid(name)})"


def defs():
    """Gradients and filters every drawer relies on. Include once per SVG document."""
    out = []
    for name, (top, bottom) in {**_GRADIENTS, **_theme().GRADIENTS}.items():
        out.append(
            f'<linearGradient id="{gid(name)}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>'
        )
    out.append(
        '<filter id="mk-soft" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="4"/></filter>'
        '<filter id="mk-softer" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="2.2"/></filter>'
    )
    return "".join(out)


def s(width=2.2):
    return f'stroke="{INK}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"'


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def shadow(cx, cy, rx, ry, o=0.32):
    return (
        f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="#1b130e" '
        f'fill-opacity="{o}" filter="url(#mk-soft)"/>'
    )


def box_shadow(x, y, w, h, o=0.25):
    return (
        f'<rect x="{f(x + 3)}" y="{f(y + 5)}" width="{f(w)}" height="{f(h)}" rx="4" fill="#1b130e" '
        f'fill-opacity="{o}" filter="url(#mk-softer)"/>'
    )


def legs(points, bottom, width=5, colour="#3b2418"):
    return "".join(
        f'<path d="M{f(x)} {f(y)}V{f(bottom)}" stroke="{colour}" stroke-width="{width}" stroke-linecap="round"/>'
        for x, y in points
    )


# ------------------------------------------------------------------------------ seating
def chair(w, h, *, fabric="velvet", tufted=True):
    cx = w / 2
    o = [shadow(cx, h - 12, 34, 9)]
    o.append(
        f'<path d="M{f(cx - 30)} 50Q{f(cx - 32)} 6 {f(cx)} 4Q{f(cx + 32)} 6 {f(cx + 30)} 50Z" fill="{grad(fabric)}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} 15Q{f(cx)} 7 {f(cx + 22)} 15" stroke="#ffffff" stroke-opacity=".35" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
    )
    if tufted:
        for bx in (cx - 14, cx, cx + 14):
            o.append(
                f'<circle cx="{f(bx)}" cy="27" r="1.9" fill="{INK}" fill-opacity=".45"/>'
            )
    seat_top = {"velvet": "#efc364", "plum": "#c98aa9", "teal": "#7cc0b6"}.get(
        fabric, "#efc364"
    )
    o.append(
        f'<rect x="{f(cx - 28)}" y="44" width="56" height="22" rx="9" fill="{seat_top}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 28)}" y="60" width="56" height="16" rx="5" fill="{grad(fabric + "-front")}" {s()}/>'
    )
    for side in (-1, 1):
        ax = cx + side * 34
        o.append(
            f'<rect x="{f(ax - 8)}" y="38" width="16" height="40" rx="7" fill="{grad(fabric)}" {s()}/>'
        )
    o.append(legs(((cx - 26, 76), (cx + 26, 76)), 84))
    return "".join(o)


def wingback(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 9)]
    o.append(
        f'<path d="M{f(cx - 34)} 56Q{f(cx - 40)} 20 {f(cx - 26)} 8Q{f(cx)} -4 {f(cx + 26)} 8Q{f(cx + 40)} 20 {f(cx + 34)} 56Z" fill="{grad("plum")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 20)} 12Q{f(cx)} 4 {f(cx + 20)} 12" stroke="#ffffff" stroke-opacity=".3" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
    )
    for bx, by in ((cx - 12, 22), (cx + 12, 22), (cx, 32)):
        o.append(
            f'<circle cx="{f(bx)}" cy="{by}" r="1.9" fill="{INK}" fill-opacity=".45"/>'
        )
    o.append(
        f'<rect x="{f(cx - 26)}" y="46" width="52" height="20" rx="8" fill="#c98aa9" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 26)}" y="60" width="52" height="16" rx="5" fill="{grad("plum-front")}" {s()}/>'
    )
    for side in (-1, 1):
        ax = cx + side * 33
        o.append(
            f'<path d="M{f(ax - 9)} 40Q{f(ax)} 32 {f(ax + 9)} 40V76H{f(ax - 9)}Z" fill="{grad("plum")}" {s()}/>'
        )
    o.append(legs(((cx - 26, 76), (cx + 26, 76)), 86, 5, "#3b2418"))
    return "".join(o)


def sofa(w, h, fabric="teal"):
    if h > w * 1.15:
        return _sofa_side(w, h, fabric)
    x0, x1 = 8, w - 8
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 10)]
    o.append(
        f'<path d="M{f(x0 + 4)} 50Q{f(x0)} 8 {f(x0 + 18)} 6H{f(x1 - 18)}Q{f(x1)} 8 {f(x1 - 4)} 50Z" fill="{grad(fabric)}" {s()}/>'
    )
    for bx in range(int(x0 + 24), int(x1 - 20), 22):
        o.append(f'<circle cx="{bx}" cy="26" r="1.8" fill="{INK}" fill-opacity=".4"/>')
    o.append(
        f'<path d="M{f(x0 + 14)} 14H{f(x1 - 14)}" stroke="#ffffff" stroke-opacity=".3" stroke-width="2.4" stroke-linecap="round"/>'
    )
    seats = max(1, round((x1 - x0) / 80))
    span = (x1 - x0 - 20) / seats
    for i in range(seats):
        sx0 = x0 + 10 + i * span + 1
        o.append(
            f'<rect x="{f(sx0)}" y="44" width="{f(span - 2)}" height="22" rx="8" fill="#7cc0b6" {s()}/>'
        )
    o.append(
        f'<rect x="{f(x0 + 8)}" y="60" width="{f(x1 - x0 - 16)}" height="16" rx="5" fill="{grad(fabric + "-front")}" {s()}/>'
    )
    for ax in (x0 + 6, x1 - 6):
        o.append(
            f'<rect x="{f(ax - 9)}" y="34" width="18" height="44" rx="8" fill="{grad(fabric)}" {s()}/>'
        )
    o.append(legs(((x0 + 10, 76), (x1 - 10, 76)), 84))
    o.append(
        f'<rect x="{f(x1 - 46)}" y="32" width="22" height="18" rx="6" fill="#e9c27a" {s(1.6)} transform="rotate(-12 {f(x1 - 35)} 41)"/>'
    )
    return "".join(o)


def chaise(w, h):
    if h > w * 1.15:
        return _sofa_side(w, h, "teal", scroll=True)
    x0, x1 = 8, w - 8
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 10)]
    # a scrolled backrest rising at the left, the seat running to the right
    o.append(
        f'<path d="M{f(x0 + 2)} 60Q{f(x0 - 4)} 6 {f(x0 + 22)} 8Q{f(x0 + 40)} 12 {f(x0 + 40)} 40H{f(x1 - 8)}Q{f(x1 + 2)} 42 {f(x1)} 60Z" fill="{grad("teal")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 10)} 16Q{f(x0 + 22)} 10 {f(x0 + 32)} 20" stroke="#ffffff" stroke-opacity=".35" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    )
    o.append(
        f'<rect x="{f(x0 + 38)}" y="44" width="{f(x1 - x0 - 46)}" height="20" rx="8" fill="#7cc0b6" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 4)}" y="58" width="{f(x1 - x0 - 8)}" height="18" rx="5" fill="{grad("teal-front")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 4)} 66H{f(x1 - 4)}" stroke="#e9c27a" stroke-width="2" stroke-dasharray="2 5"/>'
    )
    o.append(legs(((x0 + 12, 76), (x1 - 12, 76), ((x0 + x1) / 2, 76)), 84, 4.5))
    o.append(
        f'<rect x="{f(x0 + 16)}" y="24" width="20" height="16" rx="6" fill="#e9c27a" {s(1.6)} transform="rotate(-18 {f(x0 + 26)} 32)"/>'
    )
    return "".join(o)


def _sofa_side(w, h, fabric, scroll=False):
    """A sofa running down a column: its back along the left, its seat facing east."""
    x0, x1 = 12, w - 12
    top, bottom = 4, h - 16
    o = [
        shadow(
            w / 2, (top + bottom) / 2 + 6, (x1 - x0) / 2 + 6, (bottom - top) / 2, 0.26
        )
    ]
    o.append(
        f'<rect x="{f(x0)}" y="{top}" width="22" height="{f(bottom - top)}" rx="10" fill="{grad(fabric)}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 7)} {top + 14}V{f(bottom - 14)}" stroke="#ffffff" stroke-opacity=".3" stroke-width="2.4" stroke-linecap="round"/>'
    )
    seats = max(1, round((bottom - top - 40) / 80))
    span = (bottom - top - 44) / seats
    for i in range(seats):
        y0 = top + 22 + i * span
        o.append(
            f'<rect x="{f(x0 + 18)}" y="{f(y0 + 1)}" width="{f(x1 - x0 - 30)}" height="{f(span - 2)}" rx="8" fill="#7cc0b6" {s()}/>'
        )
    o.append(
        f'<rect x="{f(x1 - 14)}" y="{top + 18}" width="14" height="{f(bottom - top - 36)}" rx="4" fill="{grad(fabric + "-front")}" {s()}/>'
    )
    if scroll:
        o.append(
            f'<path d="M{f(x0)} {top + 30}Q{f(x0 - 2)} {top} {f(x0 + 26)} {top + 2}Q{f(x1)} {top + 4} {f(x1)} {top + 24}H{f(x0 + 18)}Z" fill="{grad(fabric)}" {s()}/>'
        )
    else:
        o.append(
            f'<rect x="{f(x0 + 4)}" y="{top}" width="{f(x1 - x0 - 4)}" height="22" rx="9" fill="{grad(fabric)}" {s()}/>'
        )
    o.append(
        f'<rect x="{f(x0 + 4)}" y="{f(bottom - 22)}" width="{f(x1 - x0 - 4)}" height="22" rx="9" fill="{grad(fabric)}" {s()}/>'
    )
    o.append(legs(((x0 + 10, bottom), (x1 - 8, bottom)), bottom + 8, 5))
    o.append(
        f'<rect x="{f(x0 + 26)}" y="{top + 40}" width="20" height="16" rx="6" fill="#e9c27a" {s(1.6)} transform="rotate(10 {f(x0 + 36)} {top + 48})"/>'
    )
    return "".join(o)


def bed(w, h):
    if w > h * 1.15:
        return _bed_side(w, h)
    x0, x1 = 10, w - 10
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 9)]
    o.append(
        f'<rect x="{f(x0)}" y="-6" width="{f(x1 - x0)}" height="34" rx="10" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 8)} 4H{f(x1 - 8)}" stroke="#b07a52" stroke-width="2.4" stroke-linecap="round"/>'
    )
    o.append(
        f'<rect x="{f(x0 + 4)}" y="20" width="{f(x1 - x0 - 8)}" height="{f(h - 46)}" rx="6" fill="{grad("cream")}" {s()}/>'
    )
    pw = (x1 - x0 - 24) / (2 if x1 - x0 > 70 else 1)
    for i in range(2 if x1 - x0 > 70 else 1):
        o.append(
            f'<rect x="{f(x0 + 10 + i * (pw + 4))}" y="26" width="{f(pw)}" height="18" rx="7" fill="#ffffff" {s(1.8)}/>'
        )
    blanket_top = 50
    o.append(
        f'<rect x="{f(x0 + 2)}" y="{blanket_top}" width="{f(x1 - x0 - 4)}" height="{f(h - blanket_top - 22)}" rx="6" fill="{grad("teal")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 2)} {blanket_top + 10}H{f(x1 - 2)}" stroke="#f5e9cc" stroke-width="3"/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="{f(h - 26)}" width="{f(x1 - x0)}" height="14" rx="4" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(legs(((x0 + 6, h - 14), (x1 - 6, h - 14)), h - 8, 5))
    return "".join(o)


def _bed_side(w, h):
    x0, x1 = 8, w - 8
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 9)]
    o.append(
        f'<rect x="{f(x0)}" y="-4" width="20" height="78" rx="6" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x1 - 16)}" y="22" width="16" height="52" rx="5" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 16)}" y="30" width="{f(x1 - x0 - 30)}" height="26" rx="9" fill="{grad("cream")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 22)}" y="24" width="34" height="18" rx="8" fill="#ffffff" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 60)} 30H{f(x1 - 16)}V58H{f(x0 + 60)}Q{f(x0 + 52)} 44 {f(x0 + 60)} 30Z" fill="{grad("teal")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 14)}" y="54" width="{f(x1 - x0 - 26)}" height="18" rx="4" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(legs(((x0 + 8, 72), (x1 - 8, 72)), 84, 5))
    return "".join(o)


def _turned(draw, w, h, **kw):
    """A long piece in a vertical run: drawn for the turned footprint and rotated a quarter."""
    inner = draw(h, w, **kw)
    return f'<g transform="translate({f(w)} 0) rotate(90)">{inner}</g>'


# ------------------------------------------------------------------------------ surfaces
def table(w, h, *, cloth=None, items=True):
    x0, x1 = 8, w - 8
    tall = h > w * 1.15
    top_y, top_h = 18, (h - 70 if tall else 40)
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 10)]
    for lx in (x0 + 10, x1 - 10):
        o.append(
            f'<rect x="{f(lx - 4)}" y="{f(top_y + top_h)}" width="8" height="{f(h - 8 - top_y - top_h)}" fill="#7a4d33" {s(1.6)}/>'
        )
    if cloth:
        o.append(
            f'<rect x="{f(x0)}" y="{top_y}" width="{f(x1 - x0)}" height="{f(top_h)}" rx="4" fill="#f7f1e3" {s()}/>'
        )
        for xx in range(int(x0 + 4), int(x1 - 6), 14):
            o.append(
                f'<rect x="{xx}" y="{top_y + 1}" width="7" height="{f(top_h - 2)}" fill="{cloth}" fill-opacity=".45"/>'
            )
        for yy in range(int(top_y + 4), int(top_y + top_h - 6), 14):
            o.append(
                f'<rect x="{f(x0 + 1)}" y="{yy}" width="{f(x1 - x0 - 2)}" height="7" fill="{cloth}" fill-opacity=".45"/>'
            )
        n = max(1, int((x1 - x0) // 16))
        drape = f"M{f(x0)} {f(top_y + top_h)}" + "".join(
            f"q{f((x1 - x0) / n / 2)} 14 {f((x1 - x0) / n)} 0" for _ in range(n)
        )
        o.append(
            f'<path d="{drape}V{f(top_y + top_h - 2)}H{f(x0)}Z" fill="{cloth}" {s(1.8)}/>'
        )
        o.append(
            f'<rect x="{f(x0)}" y="{top_y}" width="{f(x1 - x0)}" height="{f(top_h)}" rx="4" fill="none" {s()}/>'
        )
    else:
        o.append(
            f'<rect x="{f(x0)}" y="{top_y}" width="{f(x1 - x0)}" height="{f(top_h)}" rx="5" fill="{grad("wood")}" {s()}/>'
        )
        if tall:
            for i in range(1, 3):
                xx = x0 + (x1 - x0) * i / 3
                o.append(
                    f'<path d="M{f(xx)} {top_y + 4}V{f(top_y + top_h - 4)}" stroke="#a87443" stroke-width="1.2" stroke-opacity=".7"/>'
                )
        else:
            for i in range(1, 3):
                yy = top_y + top_h * i / 3
                o.append(
                    f'<path d="M{f(x0 + 4)} {f(yy)}H{f(x1 - 4)}" stroke="#a87443" stroke-width="1.2" stroke-opacity=".7"/>'
                )
        o.append(
            f'<rect x="{f(x0)}" y="{f(top_y + top_h)}" width="{f(x1 - x0)}" height="10" rx="3" fill="{grad("wood-front")}" {s()}/>'
        )
    if items:
        cx = x0 + (x1 - x0) * 0.32
        cy = top_y + top_h * 0.5
        o.append(
            f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="13" ry="9" fill="#ffffff" {s(1.6)}/><ellipse cx="{f(cx)}" cy="{f(cy - 1)}" rx="8" ry="5" fill="#f1e6cc"/>'
        )
        o.append(
            f'<path d="M{f(cx - 5)} {f(cy - 1)}q5 -6 10 0" fill="#e3b26a" {s(1.2)}/>'
        )
        if x1 - x0 > 70 or tall:
            tx, ty = x0 + (x1 - x0) * 0.7, top_y + top_h * (0.3 if tall else 0.42)
            o.append(
                f'<path d="M{f(tx - 4)} {f(ty + 8)}h8l-1 -14h-6Z" fill="#f3efe4" {s(1.4)}/><path d="M{f(tx)} {f(ty - 6)}v-6" stroke="#f7e7b5" stroke-width="3" stroke-linecap="round"/><path d="M{f(tx)} {f(ty - 13)}q2 -3 0 -6q-2 3 0 6" fill="#f4b740"/>'
            )
    return "".join(o)


def kitchen_table(w, h):
    return table(w, h, cloth="#d65a4a")


def writing_desk(w, h):
    x0, x1 = 10, w - 10
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 9)]
    o.append(
        f'<rect x="{f(x0 + 4)}" y="-4" width="{f(x1 - x0 - 8)}" height="26" rx="4" fill="{grad("walnut")}" {s()}/>'
    )
    cubby = (x1 - x0 - 16) / 4
    for i in range(4):
        o.append(
            f'<rect x="{f(x0 + 8 + i * cubby)}" y="0" width="{f(cubby - 2)}" height="16" rx="1.5" fill="#3b2418"/>'
        )
        o.append(
            f'<rect x="{f(x0 + 10 + i * cubby)}" y="6" width="{f(cubby - 7)}" height="9" fill="#f3ead2" fill-opacity=".9"/>'
        )
    o.append(
        f'<rect x="{f(x0)}" y="22" width="{f(x1 - x0)}" height="26" rx="4" fill="{grad("walnut-top")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 10)}" y="26" width="30" height="18" rx="1.5" fill="#fbf5e6" {s(1.4)} transform="rotate(-6 {f(x0 + 25)} 35)"/>'
    )
    o.append(
        f'<path d="M{f(x0 + 15)} 31h18M{f(x0 + 15)} 36h14" stroke="#9a8f7c" stroke-width="1.2" transform="rotate(-6 {f(x0 + 25)} 35)"/>'
    )
    o.append(
        f'<ellipse cx="{f(x1 - 20)}" cy="36" rx="6" ry="4" fill="#1f2a3a" {s(1.4)}/><path d="M{f(x1 - 22)} 34l-10 -16" stroke="#f3ead2" stroke-width="2.4" stroke-linecap="round"/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="48" width="{f(x1 - x0)}" height="30" rx="3" fill="{grad("walnut")}" {s()}/>'
    )
    for dx in (0.25, 0.75):
        xx = x0 + (x1 - x0) * dx
        o.append(
            f'<rect x="{f(xx - 14)}" y="54" width="28" height="16" rx="2" fill="#6a4128" {s(1.4)}/><circle cx="{f(xx)}" cy="62" r="2" fill="{grad("brass")}"/>'
        )
    o.append(legs(((x0 + 6, 78), (x1 - 6, 78)), 86, 5))
    return "".join(o)


def register(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 32, 8)]
    o.append(
        f'<rect x="{f(cx - 34)}" y="54" width="68" height="26" rx="4" fill="{grad("wood-front")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 28)} 54L{f(cx - 22)} 18H{f(cx + 22)}L{f(cx + 28)} 54Z" fill="{grad("brass")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 14)}" y="22" width="28" height="12" rx="2" fill="#fbf3dc" {s(1.4)}/>'
    )
    o.append(
        f'<text x="{f(cx)}" y="31.5" font-size="9" font-family="DM Mono" text-anchor="middle" fill="#7a4d33">4.20</text>'
    )
    keys = "".join(
        f'<rect x="{f(cx - 22 + c * 9)}" y="{38 + r * 7}" width="7" height="5" rx="1.4" fill="#fbf5e6" stroke="{INK}" stroke-width=".9"/>'
        for r in range(2)
        for c in range(5)
    )
    o.append(keys)
    o.append(
        f'<rect x="{f(cx - 30)}" y="62" width="60" height="10" rx="2" fill="#6a4128" {s(1.4)}/><circle cx="{f(cx)}" cy="67" r="2" fill="{grad("brass")}"/>'
    )
    return "".join(o)


def tv(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 32, 8)]
    o.append(legs(((cx - 22, 64), (cx + 22, 64)), 84, 4, "#5a3826"))
    o.append(
        f'<path d="M{f(cx - 34)} 12H{f(cx + 34)}V66H{f(cx - 34)}Z" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 28)}" y="18" width="40" height="40" rx="9" fill="#c9ded8" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} 26q8 -4 16 0" stroke="#ffffff" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    )
    for yy in (26, 42):
        o.append(
            f'<circle cx="{f(cx + 22)}" cy="{yy}" r="4.5" fill="{grad("brass")}" {s(1.4)}/>'
        )
    o.append(
        f'<path d="M{f(cx - 6)} 12L{f(cx - 16)} -6M{f(cx + 6)} 12L{f(cx + 18)} -4" {s(2)}/>'
    )
    return "".join(o)


def cabinet_radio(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 30, 8)]
    o.append(
        f'<path d="M{f(cx - 30)} 82V10Q{f(cx - 30)} -12 {f(cx)} -12Q{f(cx + 30)} -12 {f(cx + 30)} 10V82Z" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} 34V12Q{f(cx - 22)} -2 {f(cx)} -2Q{f(cx + 22)} -2 {f(cx + 22)} 12V34Z" fill="#d8c08f" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 14)} 6v26M{f(cx - 5)} 1v31M{f(cx + 5)} 1v31M{f(cx + 14)} 6v26" stroke="#9c7b4c" stroke-width="1.4"/>'
    )
    o.append(
        f'<rect x="{f(cx - 22)}" y="42" width="44" height="12" rx="3" fill="#f6e7bf" {s(1.4)}/><path d="M{f(cx - 16)} 48h32" stroke="#b38a52" stroke-width="1.2"/><path d="M{f(cx - 4)} 44v8" stroke="#c4573f" stroke-width="1.6"/>'
    )
    for xx in (cx - 12, cx + 12):
        o.append(
            f'<circle cx="{f(xx)}" cy="66" r="5" fill="{grad("brass")}" {s(1.4)}/>'
        )
    return "".join(o)


# ------------------------------------------------------------------------------- storage
def shelf(w, h):
    if h > w * 1.15:
        return "".join(
            f'<g transform="translate(0 {i * 100})">{shelf(w, 100)}</g>'
            for i in range(int(round(h / 100)))
        )
    x0, x1 = 10, w - 10
    top, bottom = -6, h - 12
    o = [shadow(w / 2, bottom + 2, (x1 - x0) / 2 + 4, 8)]
    o.append(
        f'<rect x="{f(x0)}" y="{top}" width="{f(x1 - x0)}" height="{f(bottom - top)}" rx="4" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 - 3)}" y="{top - 7}" width="{f(x1 - x0 + 6)}" height="10" rx="3" fill="{grad("walnut-top")}" {s(2)}/>'
    )
    inner_top, inner_bottom = top + 8, bottom - 14
    colours = (
        "#c75d4a",
        "#e0b04d",
        "#4d7fa8",
        "#6f9a63",
        "#a36a9a",
        "#e48c55",
        "#3f6a5b",
        "#d9c7a0",
    )
    i = 0
    for row in range(3):
        y0 = inner_top + row * (inner_bottom - inner_top) / 3
        y1 = inner_top + (row + 1) * (inner_bottom - inner_top) / 3
        o.append(
            f'<rect x="{f(x0 + 6)}" y="{f(y0)}" width="{f(x1 - x0 - 12)}" height="{f(y1 - y0 - 3)}" fill="#3b2418"/>'
        )
        bx = x0 + 9
        while bx < x1 - 14:
            bw = 6 + (i * 7) % 5
            bh = (y1 - y0 - 6) * (0.72 + ((i * 5) % 4) * 0.07)
            lean = 8 if i % 9 == 4 else 0
            o.append(
                f'<rect x="{f(bx)}" y="{f(y1 - 3 - bh)}" width="{bw}" height="{f(bh)}" rx="1" fill="{colours[i % len(colours)]}" '
                f'stroke="#2a1a12" stroke-width="1" transform="rotate({lean} {f(bx)} {f(y1 - 3)})"/>'
            )
            o.append(
                f'<path d="M{f(bx + 1.5)} {f(y1 - bh + 2)}h{bw - 3}" stroke="#fff6dc" stroke-opacity=".6" stroke-width="1.2"/>'
            )
            bx += bw + 1.5 + (4 if lean else 0)
            i += 1
        o.append(
            f'<rect x="{f(x0 + 3)}" y="{f(y1 - 3)}" width="{f(x1 - x0 - 6)}" height="5" fill="#9a6847" stroke="#2a1a12" stroke-width="1"/>'
        )
    o.append(
        f'<rect x="{f(x0 + 2)}" y="{f(bottom - 12)}" width="{f(x1 - x0 - 4)}" height="10" rx="2" fill="#5a3826" {s(1.6)}/>'
    )
    return "".join(o)


def crate(w, h, *, apples=False):
    x0, x1 = 16, w - 22
    top_y, front_y, bottom = 28, 44, h - 12
    o = [shadow((x0 + x1) / 2 + 4, bottom + 2, 34, 8)]
    o.append(
        f'<path d="M{f(x0)} {front_y}L{f(x0 + 8)} {top_y}H{f(x1 + 8)}L{f(x1)} {front_y}Z" fill="#6e4527" {s(1.8)}/>'
        if apples
        else f'<path d="M{f(x0)} {front_y}L{f(x0 + 8)} {top_y}H{f(x1 + 8)}L{f(x1)} {front_y}Z" fill="#c99764" {s(1.8)}/>'
    )
    if apples:
        for ax, col in (
            (x0 + 12, "#d64b3c"),
            (x0 + 26, "#e0a33a"),
            (x0 + 40, "#c63c33"),
            (x0 + 54, "#7fae4f"),
            (x0 + 20, "#e4593f"),
            (x0 + 47, "#d9a03a"),
        ):
            ay = top_y + (10 if ax in (x0 + 20, x0 + 47) else 14)
            o.append(
                f'<circle cx="{f(ax)}" cy="{ay}" r="8" fill="{col}" {s(1.6)}/><path d="M{f(ax)} {ay - 8}v-4" stroke="#5a3826" stroke-width="2"/><circle cx="{f(ax - 3)}" cy="{ay - 3}" r="2" fill="#ffffff" fill-opacity=".5"/>'
            )
    o.append(
        f'<rect x="{f(x0)}" y="{front_y}" width="{f(x1 - x0)}" height="{f(bottom - front_y)}" rx="2" fill="{grad("wood-front")}" {s()}/>'
    )
    for yy in (front_y + 12, front_y + 25):
        o.append(
            f'<path d="M{f(x0 + 2)} {yy}H{f(x1 - 2)}" stroke="#6e4527" stroke-width="2"/>'
        )
    if not apples:
        o.append(
            f'<path d="M{f(x0 + 4)} {front_y + 3}L{f(x1 - 4)} {f(bottom - 3)}M{f(x1 - 4)} {front_y + 3}L{f(x0 + 4)} {f(bottom - 3)}" stroke="#6e4527" stroke-width="3"/>'
        )
    o.append(
        f'<path d="M{f(x1)} {front_y}L{f(x1 + 8)} {top_y}V{f(bottom - 8)}L{f(x1)} {f(bottom)}Z" fill="#7d5131" {s(1.8)}/>'
    )
    return "".join(o)


def apple_crate(w, h):
    return crate(w, h, apples=True)


def box(w, h):
    x0, x1 = 20, w - 26
    top_y, front_y, bottom = 30, 44, h - 12
    o = [shadow((x0 + x1) / 2 + 4, bottom + 2, 30, 7)]
    o.append(
        f'<path d="M{f(x0)} {front_y}L{f(x0 + 8)} {top_y}H{f(x1 + 8)}L{f(x1)} {front_y}Z" fill="#ecc896" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f((x0 + x1) / 2 - 4)} {front_y}L{f((x0 + x1) / 2 + 4)} {top_y}" stroke="#f6e7c6" stroke-width="7"/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="{front_y}" width="{f(x1 - x0)}" height="{f(bottom - front_y)}" rx="2" fill="{grad("cardboard")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f((x0 + x1) / 2 - 5)}" y="{front_y}" width="10" height="{f(bottom - front_y)}" fill="#f6e7c6" stroke="#b58b5c" stroke-width="1"/>'
    )
    o.append(
        f'<path d="M{f(x0 + 8)} {front_y + 12}h12M{f(x0 + 8)} {front_y + 18}h8" stroke="#8d6a43" stroke-width="1.6" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(x1)} {front_y}L{f(x1 + 8)} {top_y}V{f(bottom - 8)}L{f(x1)} {f(bottom)}Z" fill="#b98957" {s(1.8)}/>'
    )
    return "".join(o)


def hatbox(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 32, 8)]
    o.append(
        f'<path d="M{f(cx - 30)} 42V70Q{f(cx)} 86 {f(cx + 30)} 70V42Z" fill="#c7718a" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 30)} 56Q{f(cx)} 70 {f(cx + 30)} 56" stroke="#f7d7df" stroke-width="3" fill="none"/>'
    )
    o.append(f'<ellipse cx="{f(cx)}" cy="40" rx="32" ry="12" fill="#e9a6b7" {s()}/>')
    o.append(
        f'<path d="M{f(cx - 32)} 40V46Q{f(cx)} 60 {f(cx + 32)} 46V40" fill="#d98aa0" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 8)} 34q-12 -12 -4 -16 6 2 8 12M{f(cx + 2)} 34q12 -12 4 -16 -6 2 -8 12" fill="#7f2f4a" {s(1.6)}/>'
    )
    return "".join(o)


def barrel(w, h):
    cx = w / 2
    top, bottom = 8, h - 12
    o = [shadow(cx, bottom + 2, 30, 8)]
    mid = (top + bottom) / 2
    o.append(
        f'<path d="M{f(cx - 26)} {top + 8}Q{f(cx - 32)} {f(mid)} {f(cx - 26)} {bottom}Q{f(cx)} {bottom + 8} {f(cx + 26)} {bottom}Q{f(cx + 32)} {f(mid)} {f(cx + 26)} {top + 8}Z" fill="{grad("barrel")}" {s()}/>'
    )
    for sx in (-13, 0, 13):
        o.append(
            f'<path d="M{f(cx + sx)} {top + 10}Q{f(cx + sx * 1.15)} {f(mid)} {f(cx + sx)} {bottom + 2}" stroke="#8a5530" stroke-width="1.4" fill="none"/>'
        )
    for yy in (top + 22, bottom - 16):
        o.append(
            f'<path d="M{f(cx - 29)} {yy}Q{f(cx)} {yy + 7} {f(cx + 29)} {yy}" stroke="#3d3a36" stroke-width="5" fill="none"/>'
        )
        o.append(
            f'<path d="M{f(cx - 29)} {yy - 1}Q{f(cx)} {yy + 6} {f(cx + 29)} {yy - 1}" stroke="#77736b" stroke-width="1.4" fill="none"/>'
        )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{top + 8}" rx="26" ry="8" fill="#d9a06a" {s()}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{top + 8}" rx="18" ry="5" fill="none" stroke="#b07a48" stroke-width="1.4"/>'
    )
    return "".join(o)


def wine_cask(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 8)]
    o.append(
        f'<path d="M{f(cx - 34)} 82L{f(cx - 26)} 62H{f(cx + 26)}L{f(cx + 34)} 82Z" fill="{grad("walnut")}" {s(1.8)}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="44" rx="34" ry="28" fill="{grad("barrel")}" {s()}/>'
    )
    for rr in (24, 13):
        o.append(
            f'<ellipse cx="{f(cx)}" cy="44" rx="{rr + 6}" ry="{rr}" fill="none" stroke="#8a5530" stroke-width="1.4"/>'
        )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="44" rx="34" ry="28" fill="none" stroke="#3d3a36" stroke-width="4.5"/>'
    )
    o.append(f'<ellipse cx="{f(cx)}" cy="44" rx="5" ry="4" fill="#7a2f3f" {s(1.4)}/>')
    o.append(f'<path d="M{f(cx)} 48v8" stroke="{grad("brass")}" stroke-width="3"/>')
    return "".join(o)


# --------------------------------------------------------------------------------- plants
def _pot(cx, base, colour="terra", rim="#e39a69", width=20):
    return (
        f'<path d="M{f(cx - width)} {base - 32}L{f(cx - width + 5)} {base}H{f(cx + width - 5)}L{f(cx + width)} {base - 32}Z" fill="{grad(colour) if colour in _GRADIENTS else colour}" {s()}/>'
        f'<rect x="{f(cx - width - 3)}" y="{base - 38}" width="{2 * width + 6}" height="9" rx="3" fill="{rim}" {s(1.8)}/>'
        f'<path d="M{f(cx - width + 8)} {base - 22}h8" stroke="#ffffff" stroke-opacity=".45" stroke-width="2.4" stroke-linecap="round"/>'
    )


def plant(w, h):
    cx, base = w / 2, h - 14
    o = [shadow(cx, base + 2, 22, 6)]
    for d, col in (
        (
            f"M{f(cx)} {base - 30}Q{f(cx - 34)} {base - 40} {f(cx - 30)} {base - 70}Q{f(cx - 8)} {base - 58} {f(cx)} {base - 30}Z",
            "#5d9154",
        ),
        (
            f"M{f(cx)} {base - 30}Q{f(cx + 34)} {base - 44} {f(cx + 26)} {base - 76}Q{f(cx + 4)} {base - 60} {f(cx)} {base - 30}Z",
            "#6ea65f",
        ),
        (
            f"M{f(cx)} {base - 30}Q{f(cx - 8)} {base - 70} {f(cx + 4)} {base - 96}Q{f(cx + 16)} {base - 64} {f(cx)} {base - 30}Z",
            "#7fb86a",
        ),
        (
            f"M{f(cx)} {base - 30}Q{f(cx - 40)} {base - 26} {f(cx - 40)} {base - 46}Q{f(cx - 18)} {base - 44} {f(cx)} {base - 30}Z",
            "#4f8452",
        ),
        (
            f"M{f(cx)} {base - 30}Q{f(cx + 40)} {base - 24} {f(cx + 42)} {base - 46}Q{f(cx + 18)} {base - 46} {f(cx)} {base - 30}Z",
            "#5d9154",
        ),
    ):
        o.append(f'<path d="{d}" fill="{col}" {s(1.8)}/>')
    o.append(_pot(cx, base))
    return "".join(o)


def fern(w, h):
    cx, base = w / 2, h - 14
    o = [shadow(cx, base + 2, 24, 6)]
    for angle in (-70, -45, -22, 0, 22, 45, 70):
        o.append(f'<g transform="rotate({angle} {f(cx)} {base - 34})">')
        o.append(
            f'<path d="M{f(cx)} {base - 34}V{base - 84}" stroke="#4f8452" stroke-width="2.2"/>'
        )
        for i, yy in enumerate(range(base - 80, base - 38, 7)):
            span = 4 + i * 1.6
            o.append(
                f'<path d="M{f(cx)} {yy}l-{f(span)} 5M{f(cx)} {yy}l{f(span)} 5" stroke="#6fae63" stroke-width="3.2" stroke-linecap="round"/>'
            )
        o.append("</g>")
    o.append(_pot(cx, base, colour="#e7e2d4", rim="#f6f1e4", width=19))
    o.append(
        f'<path d="M{f(cx - 12)} {base - 18}h24" stroke="#4d7fa8" stroke-width="3"/>'
    )
    return "".join(o)


def palm(w, h):
    cx, base = w / 2, h - 14
    o = [shadow(cx, base + 2, 22, 6)]
    o.append(
        f'<path d="M{f(cx)} {base - 30}Q{f(cx - 4)} {base - 60} {f(cx + 2)} {base - 84}" stroke="#8a5a37" stroke-width="7" fill="none" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx)} {base - 30}Q{f(cx - 4)} {base - 60} {f(cx + 2)} {base - 84}" stroke="#b07a4c" stroke-width="3" fill="none" stroke-dasharray="4 4"/>'
    )
    tx, ty = cx + 2, base - 84
    for dx, dy, col in (
        (-46, 10, "#5d9154"),
        (-30, -14, "#6ea65f"),
        (0, -26, "#7fb86a"),
        (30, -14, "#6ea65f"),
        (46, 10, "#5d9154"),
    ):
        ex, ey = tx + dx, ty + dy + 18
        mx, my = tx + dx * 0.5, ty + dy - 6
        o.append(
            f'<path d="M{f(tx)} {ty}Q{f(mx)} {my} {f(ex)} {ey}Q{f(mx + 2)} {my + 14} {f(tx)} {ty}Z" fill="{col}" {s(1.6)}/>'
        )
    o.append(_pot(cx, base, colour="#e6d9bf", rim="#f3ead6", width=18))
    o.append(
        f'<path d="M{f(cx - 12)} {base - 18}h24" stroke="#4d7fa8" stroke-width="3"/>'
    )
    return "".join(o)


def flowers(w, h):
    cx, base = w / 2, h - 14
    o = [shadow(cx, base + 2, 22, 6)]
    o.append(
        f'<path d="M{f(cx - 12)} {base - 30}Q{f(cx - 18)} {base - 50} {f(cx - 20)} {base - 62}M{f(cx)} {base - 30}V{base - 70}M{f(cx + 12)} {base - 30}Q{f(cx + 18)} {base - 50} {f(cx + 22)} {base - 58}" stroke="#4f8452" stroke-width="3" fill="none"/>'
    )
    for x, y, col in (
        (cx - 20, base - 64, "#d9667b"),
        (cx, base - 74, "#f0bf4c"),
        (cx + 22, base - 60, "#e58f6f"),
        (cx - 8, base - 52, "#f3d4e3"),
    ):
        petals = "".join(
            f'<circle cx="{f(x + 6 * math.cos(math.radians(a)))}" cy="{f(y + 6 * math.sin(math.radians(a)))}" r="5.4"/>'
            for a in range(0, 360, 72)
        )
        o.append(
            f'<g fill="{col}" stroke="{INK}" stroke-width="1.2">{petals}</g><circle cx="{f(x)}" cy="{f(y)}" r="3.4" fill="#f7da8a" {s(1)}/>'
        )
    o.append(_pot(cx, base, width=18))
    return "".join(o)


def lilies(w, h):
    cx, base = w / 2, h - 14
    o = [shadow(cx, base + 2, 18, 5)]
    o.append(
        f'<path d="M{f(cx - 4)} {base - 34}Q{f(cx - 16)} {base - 60} {f(cx - 22)} {base - 76}M{f(cx)} {base - 34}V{base - 88}M{f(cx + 4)} {base - 34}Q{f(cx + 16)} {base - 60} {f(cx + 24)} {base - 72}" stroke="#4f8452" stroke-width="2.6" fill="none"/>'
    )
    for x, y, rot in (
        (cx - 22, base - 78, -30),
        (cx, base - 90, 0),
        (cx + 24, base - 74, 30),
    ):
        o.append(
            f'<g transform="rotate({rot} {f(x)} {f(y)})"><path d="M{f(x)} {f(y + 6)}l-11 -14 11 5 11 -5Z" fill="#fffdf6" {s(1.4)}/>'
            f'<path d="M{f(x)} {f(y + 6)}l-14 -2 14 -5 14 5Z" fill="#ffffff" {s(1.2)}/><path d="M{f(x)} {f(y + 4)}v-9" stroke="#d9a441" stroke-width="1.6"/></g>'
        )
    o.append(
        f'<path d="M{f(cx - 12)} {base - 36}Q{f(cx - 20)} {base - 16} {f(cx - 12)} {base}H{f(cx + 12)}Q{f(cx + 20)} {base - 16} {f(cx + 12)} {base - 36}Z" fill="#a9d3cf" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 8)} {base - 30}q-4 12 0 24" stroke="#ffffff" stroke-opacity=".7" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    )
    return "".join(o)


def tree(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx + 6, base, 34, 9)]
    o.append(
        f'<path d="M{f(cx - 6)} {base}L{f(cx - 4)} {base - 40}H{f(cx + 4)}L{f(cx + 7)} {base}Z" fill="#8a5a37" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 34)} {base - 46}Q{f(cx - 48)} {base - 66} {f(cx - 30)} {base - 80}Q{f(cx - 30)} {base - 104} {f(cx - 6)} {base - 104}Q{f(cx + 12)} {base - 118} {f(cx + 28)} {base - 100}Q{f(cx + 48)} {base - 96} {f(cx + 44)} {base - 72}Q{f(cx + 54)} {base - 52} {f(cx + 34)} {base - 42}Q{f(cx)} {base - 30} {f(cx - 34)} {base - 46}Z" fill="{grad("leaf")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} {base - 84}Q{f(cx - 12)} {base - 98} {f(cx + 4)} {base - 96}" stroke="#bfe0a3" stroke-width="3.4" fill="none" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx - 10)} {base - 56}q12 8 28 -2" stroke="#4a7a46" stroke-width="2" fill="none" stroke-linecap="round"/>'
    )
    return "".join(o)


def potted_bay(w, h):
    cx, base = w / 2, h - 14
    o = [shadow(cx, base + 2, 22, 6)]
    o.append(
        f'<path d="M{f(cx)} {base - 36}V{base - 62}" stroke="#7a4d33" stroke-width="4"/>'
    )
    o.append(
        f'<circle cx="{f(cx)}" cy="{base - 76}" r="24" fill="{grad("leaf")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 14)} {base - 86}q8 -8 18 -6" stroke="#bfe0a3" stroke-width="3" fill="none" stroke-linecap="round"/>'
    )
    o.append(_pot(cx, base, colour="#e7e2d4", rim="#f6f1e4", width=17))
    return "".join(o)


def shrub(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx, base, 36, 9)]
    o.append(
        f'<path d="M{f(cx - 38)} {base - 6}Q{f(cx - 48)} {base - 24} {f(cx - 32)} {base - 36}Q{f(cx - 28)} {base - 56} {f(cx - 6)} {base - 54}Q{f(cx + 10)} {base - 70} {f(cx + 26)} {base - 52}Q{f(cx + 46)} {base - 48} {f(cx + 40)} {base - 26}Q{f(cx + 48)} {base - 8} {f(cx + 34)} {base - 4}Z" fill="{grad("leaf")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} {base - 40}q8 -8 16 -4M{f(cx + 8)} {base - 48}q8 -2 12 6" stroke="#bfe0a3" stroke-width="3" fill="none" stroke-linecap="round"/>'
    )
    for x, y in (
        (cx - 20, base - 26),
        (cx + 14, base - 34),
        (cx + 26, base - 18),
        (cx - 2, base - 14),
    ):
        o.append(
            f'<circle cx="{f(x)}" cy="{f(y)}" r="5" fill="#e0717b" {s(1.4)}/><circle cx="{f(x)}" cy="{f(y)}" r="1.8" fill="#f7c1c6"/>'
        )
    return "".join(o)


def box_hedge(w, h):
    x0, x1 = 10, w - 10
    top, front, bottom = 14, 40, h - 12
    o = [box_shadow(x0, top, x1 - x0, bottom - top)]
    o.append(
        f'<rect x="{f(x0)}" y="{top}" width="{f(x1 - x0)}" height="{front - top + 6}" rx="8" fill="#8fc078" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="{front}" width="{f(x1 - x0)}" height="{f(bottom - front)}" rx="6" fill="#5f9455" {s()}/>'
    )
    for xx in range(int(x0 + 10), int(x1 - 6), 14):
        o.append(
            f'<path d="M{xx} {front + 8}q4 6 0 12" stroke="#4a7a46" stroke-width="2" fill="none" stroke-linecap="round"/>'
        )
        o.append(
            f'<path d="M{xx} {top + 8}q5 -3 9 1" stroke="#c4e2ad" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
        )
    return "".join(o)


# --------------------------------------------------------------------------- landmarks
def statue(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 30, 8)]
    o.append(
        f'<rect x="{f(cx - 24)}" y="60" width="48" height="22" rx="3" fill="{grad("stone-front")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 28)}" y="54" width="56" height="9" rx="3" fill="{grad("stone")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 18)} 54Q{f(cx - 16)} 34 {f(cx)} 32Q{f(cx + 16)} 34 {f(cx + 18)} 54Z" fill="{grad("stone")}" {s()}/>'
    )
    o.append(f'<circle cx="{f(cx)}" cy="14" r="15" fill="{grad("stone")}" {s()}/>')
    o.append(
        f'<path d="M{f(cx - 14)} 8Q{f(cx - 6)} -6 {f(cx + 10)} 0Q{f(cx + 16)} 4 {f(cx + 14)} 10" fill="#c6c9bc" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 6)} 14q2 -2 4 0M{f(cx + 2)} 14q2 -2 4 0M{f(cx - 3)} 22q3 2 6 0" stroke="#7f8579" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx - 10)} 4q4 -4 10 -4" stroke="#ffffff" stroke-opacity=".6" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    )
    return "".join(o)


def piano(w, h):
    x0, x1 = 10, w - 10
    top, bottom = -2, h - 12
    o = [shadow(w / 2, bottom + 2, 42, 9)]
    o.append(
        f'<rect x="{f(x0)}" y="{top}" width="{f(x1 - x0)}" height="{f(bottom - top)}" rx="5" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 - 3)}" y="{top - 6}" width="{f(x1 - x0 + 6)}" height="9" rx="3" fill="{grad("walnut-top")}" {s(2)}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 8)}" y="{top + 8}" width="{f(x1 - x0 - 16)}" height="28" rx="3" fill="#5a3826" stroke="#2a1a12" stroke-width="1.4"/>'
    )
    o.append(
        f'<rect x="{f(x0 + 18)}" y="{top + 12}" width="{f(x1 - x0 - 36)}" height="20" fill="#f7f1e3" stroke="#2a1a12" stroke-width="1"/>'
    )
    o.append(
        f'<path d="M{f(x0 + 22)} {top + 18}h{f(x1 - x0 - 44)}M{f(x0 + 22)} {top + 23}h{f(x1 - x0 - 44)}M{f(x0 + 22)} {top + 28}h{f(x1 - x0 - 50)}" stroke="#7a6a5a" stroke-width="1"/>'
    )
    ky = top + 44
    o.append(
        f'<rect x="{f(x0 - 4)}" y="{ky}" width="{f(x1 - x0 + 8)}" height="16" rx="2" fill="#fbf7ee" {s(1.8)}/>'
    )
    step = (x1 - x0 + 4) / 11
    o.append(
        "".join(
            f'<path d="M{f(x0 - 2 + i * step)} {ky + 1}v14" stroke="#9a9086" stroke-width=".9"/>'
            for i in range(1, 11)
        )
    )
    o.append(
        "".join(
            f'<rect x="{f(x0 + 2 + i * step)}" y="{ky + 1}" width="4" height="9" fill="#1f1a17"/>'
            for i in (0, 1, 3, 4, 5, 7, 8)
        )
    )
    o.append(
        f'<rect x="{f(x0 - 4)}" y="{ky + 16}" width="{f(x1 - x0 + 8)}" height="7" fill="#5a3826" {s(1.6)}/>'
    )
    o.append(legs(((x0 + 6, bottom - 10), (x1 - 6, bottom - 10)), bottom, 5))
    o.append(
        f'<circle cx="{f(x0 + 12)}" cy="{top + 2}" r="3" fill="{grad("brass")}" {s(1.2)}/><path d="M{f(x0 + 12)} {top - 1}v-8" stroke="#f7e7b5" stroke-width="3" stroke-linecap="round"/><path d="M{f(x0 + 12)} {top - 11}q2 -3 0 -6q-2 3 0 6" fill="#f4b740"/>'
    )
    return "".join(o)


def boulder(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx + 4, base, 36, 9)]
    o.append(
        f'<path d="M{f(cx - 36)} {base - 4}Q{f(cx - 42)} {base - 30} {f(cx - 22)} {base - 50}Q{f(cx - 2)} {base - 64} {f(cx + 22)} {base - 54}Q{f(cx + 42)} {base - 40} {f(cx + 38)} {base - 6}Z" fill="{grad("stone")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 36)} {base - 4}Q{f(cx)} {base - 18} {f(cx + 38)} {base - 6}" fill="{grad("stone-front")}" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} {base - 40}q10 -12 26 -10" stroke="#f3f4ee" stroke-width="3.4" fill="none" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx + 6)} {base - 46}l-6 18 12 10" stroke="#8b9187" stroke-width="1.6" fill="none"/>'
    )
    return "".join(o)


def millstone(w, h):
    cx = w / 2
    o = [shadow(cx, h - 14, 38, 9)]
    o.append(
        f'<path d="M{f(cx - 38)} 50V62Q{f(cx)} 84 {f(cx + 38)} 62V50" fill="{grad("stone-front")}" {s()}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="50" rx="38" ry="20" fill="{grad("stone")}" {s()}/>'
    )
    o.append(f'<ellipse cx="{f(cx)}" cy="50" rx="9" ry="5" fill="#6f7568" {s(1.6)}/>')
    o.append(
        f'<path d="M{f(cx - 30)} 50H{f(cx - 12)}M{f(cx + 12)} 50H{f(cx + 30)}M{f(cx - 20)} 38l8 6M{f(cx + 20)} 38l-8 6M{f(cx - 20)} 62l8 -6M{f(cx + 20)} 62l-8 -6" stroke="#9ea395" stroke-width="1.6"/>'
    )
    return "".join(o)


def bear(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 28, 7)]
    fur = "#c68d5e"
    o.append(f'<ellipse cx="{f(cx)}" cy="62" rx="22" ry="20" fill="{fur}" {s()}/>')
    o.append(f'<ellipse cx="{f(cx)}" cy="66" rx="12" ry="11" fill="#e8c9a0" {s(1.4)}/>')
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 20)}" cy="80" rx="10" ry="7" fill="{fur}" {s()}/>'
        )
        o.append(
            f'<ellipse cx="{f(cx + side * 24)}" cy="54" rx="7" ry="11" fill="{fur}" {s()} transform="rotate({side * -24} {f(cx + side * 24)} 54)"/>'
        )
        o.append(
            f'<circle cx="{f(cx + side * 14)}" cy="14" r="8" fill="{fur}" {s()}/><circle cx="{f(cx + side * 14)}" cy="14" r="3.6" fill="#e8c9a0"/>'
        )
    o.append(f'<circle cx="{f(cx)}" cy="28" r="19" fill="{fur}" {s()}/>')
    o.append(f'<ellipse cx="{f(cx)}" cy="34" rx="9" ry="7" fill="#e8c9a0" {s(1.4)}/>')
    o.append(f'<ellipse cx="{f(cx)}" cy="31" rx="3.4" ry="2.4" fill="{INK}"/>')
    o.append(
        f'<circle cx="{f(cx - 7)}" cy="24" r="2.2" fill="{INK}"/><circle cx="{f(cx + 7)}" cy="24" r="2.2" fill="{INK}"/>'
    )
    o.append(
        f'<path d="M{f(cx - 10)} 46l10 5 10 -5-4 8h-12Z" fill="#c4573f" {s(1.4)}/>'
    )
    return "".join(o)


def bearskin(w, h):
    cx = w / 2
    o = [
        f'<ellipse cx="{f(cx + 3)}" cy="{f(h / 2 + 6)}" rx="40" ry="30" fill="#1b130e" fill-opacity=".2" filter="url(#mk-softer)"/>'
    ]
    o.append(
        f'<path d="M{f(cx)} 22Q{f(cx + 12)} 14 {f(cx + 20)} 22Q{f(cx + 34)} 18 {f(cx + 38)} 32Q{f(cx + 50)} 36 {f(cx + 44)} 50Q{f(cx + 50)} 64 {f(cx + 38)} 68Q{f(cx + 40)} 82 {f(cx + 24)} 82Q{f(cx + 14)} 90 {f(cx)} 84Q{f(cx - 14)} 90 {f(cx - 24)} 82Q{f(cx - 40)} 82 {f(cx - 38)} 68Q{f(cx - 50)} 64 {f(cx - 44)} 50Q{f(cx - 50)} 36 {f(cx - 38)} 32Q{f(cx - 34)} 18 {f(cx - 20)} 22Q{f(cx - 12)} 14 {f(cx)} 22Z" fill="#efe2c6" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 24)} 56q24 14 48 0" stroke="#d9c7a0" stroke-width="2.4" fill="none"/>'
    )
    o.append(f'<circle cx="{f(cx)}" cy="30" r="13" fill="#f6ecd8" {s()}/>')
    o.append(
        f'<circle cx="{f(cx - 5)}" cy="28" r="1.9" fill="{INK}"/><circle cx="{f(cx + 5)}" cy="28" r="1.9" fill="{INK}"/><ellipse cx="{f(cx)}" cy="34" rx="3" ry="2" fill="{INK}"/>'
    )
    return "".join(o)


# ------------------------------------------------------------------------- ground items
def carpet(w, h):
    x0, y0, x1, y1 = 8, 12, w - 8, h - 10
    o = [
        f'<rect x="{x0 + 3}" y="{y0 + 5}" width="{f(x1 - x0)}" height="{f(y1 - y0)}" rx="3" fill="#1b130e" fill-opacity=".25" filter="url(#mk-softer)"/>'
    ]
    if x1 - x0 >= y1 - y0:
        fringe = "".join(
            f"M{x0 - 4} {yy}h4M{f(x1)} {yy}h4"
            for yy in range(int(y0 + 5), int(y1 - 2), 6)
        )
    else:
        fringe = "".join(
            f"M{xx} {y0 - 4}v4M{xx} {f(y1)}v4"
            for xx in range(int(x0 + 5), int(x1 - 2), 6)
        )
    o.append(
        f'<path d="{fringe}" stroke="#e8d7b1" stroke-width="2" stroke-linecap="round"/>'
    )
    o.append(
        f'<rect x="{x0}" y="{y0}" width="{f(x1 - x0)}" height="{f(y1 - y0)}" rx="3" fill="#a8423b" {s(2)}/>'
    )
    o.append(
        f'<rect x="{x0 + 6}" y="{y0 + 6}" width="{f(x1 - x0 - 12)}" height="{f(y1 - y0 - 12)}" rx="2" fill="#c9604e" stroke="#e9c27a" stroke-width="2"/>'
    )
    o.append(
        f'<rect x="{x0 + 12}" y="{y0 + 12}" width="{f(x1 - x0 - 24)}" height="{f(y1 - y0 - 24)}" rx="2" fill="none" stroke="#7f2f2b" stroke-width="1.4" stroke-dasharray="4 3"/>'
    )
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = min(34, (x1 - x0) * 0.32), min(18, (y1 - y0) * 0.3)
    o.append(
        f'<path d="M{f(cx)} {f(cy - ry)}L{f(cx + rx)} {f(cy)}L{f(cx)} {f(cy + ry)}L{f(cx - rx)} {f(cy)}Z" fill="#e9c27a" stroke="#7f2f2b" stroke-width="1.6"/>'
    )
    o.append(
        f'<path d="M{f(cx)} {f(cy - ry / 2)}L{f(cx + rx / 2)} {f(cy)}L{f(cx)} {f(cy + ry / 2)}L{f(cx - rx / 2)} {f(cy)}Z" fill="#2f6b62"/>'
    )
    return "".join(o)


def car(w, h):
    if h > w * 1.15 or w < 150:
        if h > 100:
            return f'<g transform="translate(0 {f(h - 100)})">{_car_front(w, 100)}</g>'
        return _car_front(w, h)
    x0, x1 = 6, w - 6
    o = [shadow(w / 2, h - 12, (x1 - x0) / 2, 9)]
    body = f"M{f(x0 + 4)} 66Q{f(x0)} 46 {f(x0 + 24)} 42L{f(x0 + 52)} 40Q{f(x0 + 66)} 14 {f(x0 + 96)} 14H{f(x1 - 70)}Q{f(x1 - 50)} 14 {f(x1 - 40)} 40L{f(x1 - 10)} 44Q{f(x1 + 2)} 48 {f(x1 - 2)} 66Z"
    o.append(f'<path d="{body}" fill="{grad("navy")}" {s()}/>')
    o.append(
        f'<path d="M{f(x0 + 60)} 40Q{f(x0 + 70)} 20 {f(x0 + 94)} 20H{f(x0 + 110)}V40Z" fill="#cfe1ea" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 118)} 20H{f(x1 - 72)}Q{f(x1 - 56)} 20 {f(x1 - 48)} 40H{f(x0 + 118)}Z" fill="#cfe1ea" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 10)} 54H{f(x1 - 10)}" stroke="#e8d7b1" stroke-width="2.4"/>'
    )
    for wx in (x0 + 36, x1 - 40):
        o.append(
            f'<circle cx="{f(wx)}" cy="68" r="13" fill="#2a2a2a" {s()}/><circle cx="{f(wx)}" cy="68" r="5" fill="#c9cfd2"/>'
        )
    o.append(f'<circle cx="{f(x1 - 6)}" cy="50" r="4" fill="#f7e7a7" {s(1.4)}/>')
    return "".join(o)


def _car_front(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 34, 8)]
    o.append(
        f'<path d="M{f(cx - 34)} 74V46Q{f(cx - 32)} 34 {f(cx - 22)} 32L{f(cx - 16)} 14H{f(cx + 16)}L{f(cx + 22)} 32Q{f(cx + 32)} 34 {f(cx + 34)} 46V74Z" fill="{grad("navy")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 14)} 18H{f(cx + 14)}L{f(cx + 18)} 32H{f(cx - 18)}Z" fill="#cfe1ea" {s(1.6)}/>'
    )
    o.append(
        f'<rect x="{f(cx - 12)}" y="48" width="24" height="16" rx="3" fill="#c9cfd2" {s(1.6)}/><path d="M{f(cx - 8)} 52v8M{f(cx - 3)} 52v8M{f(cx + 2)} 52v8M{f(cx + 7)} 52v8" stroke="#7d8a86" stroke-width="1.2"/>'
    )
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(cx + side * 24)}" cy="50" r="6" fill="#f7e7a7" {s(1.6)}/>'
        )
        o.append(
            f'<rect x="{f(cx + side * 28 - 6)}" y="70" width="12" height="14" rx="3" fill="#2a2a2a" {s(1.6)}/>'
        )
    return "".join(o)


def golf_cart(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 34, 8)]
    o.append(
        f'<path d="M{f(cx - 34)} 12H{f(cx + 34)}" stroke="#2f3b37" stroke-width="2"/>'
    )
    o.append(
        f'<rect x="{f(cx - 36)}" y="4" width="72" height="10" rx="4" fill="#f2f0e6" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 30)} 14V48M{f(cx + 30)} 14V48" stroke="#5d6b66" stroke-width="3"/>'
    )
    o.append(
        f'<rect x="{f(cx - 34)}" y="46" width="68" height="26" rx="8" fill="#7fb08f" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 26)}" y="34" width="52" height="14" rx="5" fill="#f2f0e6" {s(1.8)}/>'
    )
    o.append(
        f'<rect x="{f(cx + 16)}" y="22" width="10" height="26" rx="3" fill="#b3492f" {s(1.4)}/><path d="M{f(cx + 18)} 22l-2 -10M{f(cx + 23)} 22l2 -12" stroke="#7d8a86" stroke-width="2"/>'
    )
    for side in (-1, 1):
        o.append(
            f'<rect x="{f(cx + side * 26 - 6)}" y="70" width="12" height="14" rx="3" fill="#2a2a2a" {s(1.6)}/>'
        )
    return "".join(o)


def sand_prop(w, h):
    x0, y0, x1, y1 = 8, 10, w - 8, h - 10
    path = (
        f"M{f(x0 + (x1 - x0) * .1)} {f(y0 + (y1 - y0) * .55)}Q{f(x0)} {f(y0 + (y1 - y0) * .12)} {f(x0 + (x1 - x0) * .42)} {f(y0 + (y1 - y0) * .1)}"
        f"Q{f(x0 + (x1 - x0) * .78)} {f(y0)} {f(x0 + (x1 - x0) * .92)} {f(y0 + (y1 - y0) * .34)}Q{f(x1 + 2)} {f(y0 + (y1 - y0) * .7)} {f(x0 + (x1 - x0) * .7)} {f(y0 + (y1 - y0) * .9)}"
        f"Q{f(x0 + (x1 - x0) * .36)} {f(y1 + 2)} {f(x0 + (x1 - x0) * .12)} {f(y0 + (y1 - y0) * .8)}Q{f(x0 - 2)} {f(y0 + (y1 - y0) * .7)} {f(x0 + (x1 - x0) * .1)} {f(y0 + (y1 - y0) * .55)}Z"
    )
    o = [
        f'<path d="{path}" fill="#1b130e" fill-opacity=".18" transform="translate(2 4)" filter="url(#mk-softer)"/>'
    ]
    o.append(
        f'<path d="{path}" fill="{grad("sand")}" stroke="#a5884f" stroke-width="3"/>'
    )
    for i in range(3):
        yy = y0 + (y1 - y0) * (0.34 + i * 0.17)
        o.append(
            f'<path d="M{f(x0 + (x1 - x0) * .22)} {f(yy)}q{f((x1 - x0) * .14)} -5 {f((x1 - x0) * .28)} 0t{f((x1 - x0) * .28)} 0" stroke="#cdb176" stroke-width="1.8" fill="none"/>'
        )
    return "".join(o)


def water_prop(w, h):
    x0, y0, x1, y1 = 6, 8, w - 6, h - 8
    path = (
        f"M{f(x0 + (x1 - x0) * .1)} {f(y0 + (y1 - y0) * .55)}Q{f(x0)} {f(y0 + (y1 - y0) * .12)} {f(x0 + (x1 - x0) * .4)} {f(y0 + (y1 - y0) * .1)}"
        f"Q{f(x0 + (x1 - x0) * .78)} {f(y0)} {f(x0 + (x1 - x0) * .92)} {f(y0 + (y1 - y0) * .34)}Q{f(x1 + 3)} {f(y0 + (y1 - y0) * .7)} {f(x0 + (x1 - x0) * .7)} {f(y0 + (y1 - y0) * .9)}"
        f"Q{f(x0 + (x1 - x0) * .36)} {f(y1 + 3)} {f(x0 + (x1 - x0) * .12)} {f(y0 + (y1 - y0) * .8)}Q{f(x0 - 3)} {f(y0 + (y1 - y0) * .7)} {f(x0 + (x1 - x0) * .1)} {f(y0 + (y1 - y0) * .55)}Z"
    )
    o = [
        f'<path d="{path}" fill="#c9b78f" stroke="{INK}" stroke-width="2.2" transform="translate(0 4)"/>'
    ]
    o.append(
        f'<path d="{path}" fill="{grad("water")}" stroke="#3e6f7c" stroke-width="3"/>'
    )
    o.append(
        f'<path d="M{f(x0 + (x1 - x0) * .25)} {f(y0 + (y1 - y0) * .4)}q{f((x1 - x0) * .1)} -6 {f((x1 - x0) * .2)} 0M{f(x0 + (x1 - x0) * .5)} {f(y0 + (y1 - y0) * .66)}q{f((x1 - x0) * .1)} -6 {f((x1 - x0) * .2)} 0" stroke="#eaf8f8" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    )
    lx, ly = x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.36
    o.append(
        f'<path d="M{f(lx)} {f(ly)}m-9 0a9 6 0 1 0 18 0l-9 0Z" fill="#7aa36a" {s(1.4)}/><circle cx="{f(lx - 3)}" cy="{f(ly - 3)}" r="3" fill="#f3a6b6" {s(1)}/>'
    )
    return "".join(o)


def flag(w, h):
    cx = w / 2
    o = [shadow(cx, h - 14, 24, 6)]
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{h - 18}" rx="24" ry="9" fill="#8cc07a" {s(1.6)}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx - 2)}" cy="{h - 18}" rx="8" ry="3.5" fill="#24342f"/>'
    )
    o.append(
        f'<path d="M{f(cx - 2)} {h - 18}V-4" stroke="#f3f0e6" stroke-width="3.4" stroke-linecap="round"/><path d="M{f(cx - 2)} {h - 18}V-4" stroke="{INK}" stroke-width="1" stroke-opacity=".6"/>'
    )
    o.append(
        f'<path d="M{f(cx)} -4L{f(cx + 34)} 6 {f(cx)} 18Z" fill="#d65a4a" {s(1.8)}/>'
    )
    return "".join(o)


def tee(w, h):
    cx = w / 2
    o = [shadow(cx, h - 14, 26, 7)]
    o.append(
        f'<rect x="{f(cx - 34)}" y="{h - 34}" width="68" height="22" rx="9" fill="{grad("grass")}" {s(1.6)}/>'
    )
    o.append(f'<path d="M{f(cx - 4)} {h - 46}h8l-2 22h-4Z" fill="#e2b98a" {s(1.4)}/>')
    o.append(f'<circle cx="{f(cx)}" cy="{h - 56}" r="12" fill="#ffffff" {s()}/>')
    o.append(
        '<g fill="#c9ccc2">'
        + "".join(
            f'<circle cx="{f(cx + dx)}" cy="{f(h - 56 + dy)}" r="1.6"/>'
            for dx, dy in ((-4, -4), (4, -4), (0, 1), (-5, 4), (5, 4))
        )
        + "</g>"
    )
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(cx + side * 26)}" cy="{h - 24}" r="5" fill="#d65a4a" {s(1.4)}/>'
        )
    return "".join(o)


def void(w, h):
    x0, y0, x1, y1 = 6, 6, w - 6, h - 6
    return (
        f'<rect x="{x0}" y="{y0}" width="{f(x1 - x0)}" height="{f(y1 - y0)}" rx="10" fill="#1c1714" stroke="{INK}" stroke-width="2.4"/>'
        f'<rect x="{x0 + 4}" y="{y0 + 4}" width="{f(x1 - x0 - 8)}" height="16" rx="6" fill="#3a2f28"/>'
        f'<path d="M{x0 + 10} {f(y1 - 10)}H{f(x1 - 10)}" stroke="#2c2420" stroke-width="2"/>'
    )


def generic(w, h):
    x0, x1 = 14, w - 20
    o = [shadow(w / 2, h - 12, (x1 - x0) / 2, 7)]
    o.append(
        f'<path d="M{f(x0)} 42L{f(x0 + 8)} 28H{f(x1 + 8)}L{f(x1)} 42Z" fill="#e6dbc3" {s(1.8)}/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="42" width="{f(x1 - x0)}" height="{f(h - 54)}" rx="3" fill="#d4c6ae" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x1)} 42L{f(x1 + 8)} 28V{f(h - 20)}L{f(x1)} {f(h - 12)}Z" fill="#b9aa8e" {s(1.8)}/>'
    )
    return "".join(o)


BASE = {
    "bed": bed,
    "chair": chair,
    "carpet": carpet,
    "car": car,
    "table": table,
    "tv": tv,
    "shelf": shelf,
    "plant": plant,
    "tree": tree,
    "flowers": flowers,
    "shrub": shrub,
    "crate": crate,
    "box": box,
    "register": register,
    "palm": palm,
    "bear": bear,
    "sand": sand_prop,
    "flag": flag,
    "tee": tee,
    "golf_cart": golf_cart,
    "water": water_prop,
    "statue": statue,
    "piano": piano,
    "boulder": boulder,
    "barrel": barrel,
    "void": void,
    "generic": generic,
}

SKINS = {
    "wingback": wingback,
    "chaise": chaise,
    "sofa": sofa,
    "writing_desk": writing_desk,
    "kitchen_table": kitchen_table,
    "cabinet_radio": cabinet_radio,
    "fern": fern,
    "potted_bay": potted_bay,
    "lilies": lilies,
    "box_hedge": box_hedge,
    "hatbox": hatbox,
    "bearskin": bearskin,
    "millstone": millstone,
    "wine_cask": wine_cask,
    "apple_crate": apple_crate,
    "packing_crate": crate,
}

# Drawn once over a filled rectangular footprint; every other kind repeats per cell, which keeps
# a non-rectangular footprint honest about its exact cells.
STRETCH = {
    "table",
    "kitchen_table",
    "writing_desk",
    "carpet",
    "bed",
    "chaise",
    "sofa",
    "car",
    "water",
    "sand",
    "shelf",
    "generic",
    "void",
    "box_hedge",
    "bearskin",
}
# Kinds whose drawing rises in front of the wall behind them.
TALL = {
    "shelf",
    "piano",
    "plant",
    "palm",
    "tree",
    "statue",
    "flowers",
    "cabinet_radio",
    "fern",
    "potted_bay",
    "lilies",
    "flag",
    "tv",
    "barrel",
    "writing_desk",
    "bed",
    "wingback",
}


def _theme():
    from . import skins

    return skins


def all_skins():
    return {**SKINS, **_theme().SKINS}


def drawer(kind, skin=None):
    if skin:
        theme = _theme().SKINS
        if skin in SKINS:
            return SKINS[skin], skin
        if skin in theme:
            return theme[skin], skin
    return BASE.get(kind, generic), kind


def draw(kind, w, h, skin=None):
    fn, name = drawer(kind, skin)
    if h > 100 and not stretches(kind, skin):
        # Fixed-size pieces stand at the bottom of a tall footprint, like real furniture.
        return f'<g transform="translate(0 {f(h - 100)})">{fn(w, 100)}</g>'
    return fn(w, h)


def stretches(kind, skin=None):
    name = skin or kind
    return name in STRETCH or name in _theme().STRETCH


def is_tall(kind, skin=None):
    name = skin or kind
    return name in TALL or name in _theme().TALL


def glyph(kind, size, skin=None):
    """A key/legend glyph: one cell's drawing, scaled so overhanging tops stay in the box."""
    scale = size / (100 + OVERHANG)
    inner = draw(kind, 100, 100, skin=skin)
    return f'<g transform="scale({scale:.4f}) translate(0 {OVERHANG})">{inner}</g>'
