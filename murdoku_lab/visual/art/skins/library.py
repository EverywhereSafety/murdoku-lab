"""St Aldhelm's College library: chesterfields, banker's lamps, a card catalogue and an owl."""

import math

from . import _kit as k
from ._kit import INK, f, grad, legs, s, shadow

GRADIENTS = {
    "leather": ("#9a5634", "#6f3a22"),
    "leather-front": ("#6f3a22", "#56291a"),
    "oak": ("#d6a86e", "#b3844c"),
    "ocean": ("#79b2d1", "#3f7aa0"),
    "glass-green": ("#5fae7a", "#2f7a4f"),
}

BOOK_COLOURS = (
    "#7a2f3f",
    "#2f5c48",
    "#3f5f8a",
    "#b5703f",
    "#d9b866",
    "#5a3826",
    "#8a6aa8",
)


def chesterfield(w, h):
    if h > w * 1.15:
        return _chesterfield_side(w, h)
    x0, x1 = 8, w - 8
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 10)]
    o.append(
        f'<rect x="{f(x0 + 4)}" y="8" width="{f(x1 - x0 - 8)}" height="44" rx="10" fill="{grad("leather")}" {s()}/>'
    )
    for row, y in enumerate((18, 30, 42)):
        start = x0 + 22 + (8 if row % 2 else 0)
        for x in range(int(start), int(x1 - 18), 16):
            o.append(f'<circle cx="{x}" cy="{y}" r="1.8" fill="#3b1f14"/>')
            if row < 2:
                o.append(
                    f'<path d="M{x} {y}l8 12M{x} {y}l-8 12" stroke="#56291a" stroke-width="1" stroke-opacity=".7"/>'
                )
    seats = max(1, round((x1 - x0) / 80))
    span = (x1 - x0 - 24) / seats
    for i in range(seats):
        o.append(
            f'<rect x="{f(x0 + 12 + i * span + 1)}" y="46" width="{f(span - 2)}" height="18" rx="7" fill="#a8603a" {s()}/>'
        )
    o.append(
        f'<rect x="{f(x0 + 6)}" y="60" width="{f(x1 - x0 - 12)}" height="16" rx="4" fill="{grad("leather-front")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 10)} 72H{f(x1 - 10)}" stroke="#e2c27a" stroke-width="2" stroke-dasharray=".1 5" stroke-linecap="round"/>'
    )
    for ax in (x0 + 7, x1 - 7):
        o.append(
            f'<rect x="{f(ax - 10)}" y="20" width="20" height="58" rx="9" fill="{grad("leather")}" {s()}/>'
            f'<ellipse cx="{f(ax)}" cy="26" rx="8" ry="5" fill="none" stroke="#56291a" stroke-width="1.4"/>'
        )
    o.append(legs(((x0 + 12, 78), (x1 - 12, 78)), 86, 4.4, "#2a1a12"))
    o.append(k.highlight(f"M{f(x0 + 18)} 13H{f(x1 - 18)}", 0.25, 2.4))
    return "".join(o)


def _chesterfield_side(w, h):
    x0, x1 = 12, w - 12
    top, bottom = 4, h - 16
    o = [
        shadow(
            w / 2, (top + bottom) / 2 + 6, (x1 - x0) / 2 + 6, (bottom - top) / 2, 0.26
        )
    ]
    o.append(
        f'<rect x="{f(x0)}" y="{top}" width="24" height="{f(bottom - top)}" rx="10" fill="{grad("leather")}" {s()}/>'
    )
    for y in range(int(top + 22), int(bottom - 18), 14):
        o.append(f'<circle cx="{f(x0 + 12)}" cy="{y}" r="1.8" fill="#3b1f14"/>')
    seats = max(1, round((bottom - top - 40) / 80))
    span = (bottom - top - 44) / seats
    for i in range(seats):
        o.append(
            f'<rect x="{f(x0 + 20)}" y="{f(top + 22 + i * span + 1)}" width="{f(x1 - x0 - 32)}" height="{f(span - 2)}" rx="8" fill="#a8603a" {s()}/>'
        )
    o.append(
        f'<rect x="{f(x1 - 14)}" y="{top + 18}" width="14" height="{f(bottom - top - 36)}" rx="4" fill="{grad("leather-front")}" {s()}/>'
    )
    for y in (top, bottom - 22):
        o.append(
            f'<rect x="{f(x0 + 2)}" y="{f(y)}" width="{f(x1 - x0 - 2)}" height="22" rx="10" fill="{grad("leather")}" {s()}/>'
        )
    o.append(legs(((x0 + 10, bottom), (x1 - 8, bottom)), bottom + 8, 4.4, "#2a1a12"))
    return "".join(o)


def leather_armchair(w, h):
    return k.armchair(
        w,
        h,
        back=grad("leather"),
        seat="#a8603a",
        front=grad("leather-front"),
        arm=grad("leather"),
        studs="#e2c27a",
        leg="#2a1a12",
    )


def _book_row(x0, x1, base, height, seed=0):
    out, x, i = [], x0, seed
    while x < x1 - 3:
        bw = 4 + (i * 7) % 4
        bh = height * (0.7 + ((i * 5) % 4) * 0.09)
        out.append(
            f'<rect x="{f(x)}" y="{f(base - bh)}" width="{bw}" height="{f(bh)}" rx=".8" fill="{BOOK_COLOURS[i % len(BOOK_COLOURS)]}" stroke="#1d1410" stroke-width=".8"/>'
        )
        x += bw + 0.8
        i += 1
    return "".join(out)


def book_trolley(w, h):
    if h > w * 1.15 or w < 150:
        if h > 100:
            return (
                f'<g transform="translate(0 {f(h - 100)})">{_trolley_front(w, 100)}</g>'
            )
        return _trolley_front(w, h)
    x0, x1 = 10, w - 10
    o = [shadow(w / 2, h - 12, (x1 - x0) / 2, 9)]
    o.append(k.outlined(f"M{f(x1 - 4)} 30L{f(x1 + 2)} 4", "#7a4d33", 3.6))
    for y in (26, 62):
        o.append(_book_row(x0 + 10, x1 - 12, y + 2, 26, seed=y))
        o.append(
            f'<rect x="{f(x0)}" y="{y}" width="{f(x1 - x0 - 4)}" height="7" rx="2" fill="{grad("oak")}" {s(1.8)}/>'
        )
    for px in (x0 + 2, x1 - 6):
        o.append(k.outlined(f"M{f(px)} 4V74", "#9a6a43", 3.4, cap="butt"))
    for wx in (x0 + 10, x1 - 14):
        o.append(
            f'<circle cx="{f(wx)}" cy="80" r="5.4" fill="#2a2a2a" {s(1.4)}/><circle cx="{f(wx)}" cy="80" r="1.8" fill="#9aa1a8"/>'
        )
    return "".join(o)


def _trolley_front(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 30, 8)]
    for y in (28, 62):
        o.append(_book_row(cx - 24, cx + 24, y + 2, 24, seed=y))
        o.append(
            f'<rect x="{f(cx - 28)}" y="{y}" width="56" height="7" rx="2" fill="{grad("oak")}" {s(1.8)}/>'
        )
    for px in (cx - 28, cx + 28):
        o.append(k.outlined(f"M{f(px)} 6V74", "#9a6a43", 3.4, cap="butt"))
    for wx in (cx - 24, cx + 24):
        o.append(
            f'<circle cx="{f(wx)}" cy="80" r="5.4" fill="#2a2a2a" {s(1.4)}/><circle cx="{f(wx)}" cy="80" r="1.8" fill="#9aa1a8"/>'
        )
    return "".join(o)


def _bankers_lamp(x, y):
    return (
        f'<ellipse cx="{f(x)}" cy="{f(y + 6)}" rx="15" ry="7" fill="#fff3c8" fill-opacity=".3"/>'
        f'<ellipse cx="{f(x)}" cy="{f(y + 6)}" rx="7" ry="2.6" fill="{grad("brass")}" {s(1.1)}/>'
        f'<path d="M{f(x)} {f(y + 5)}V{f(y - 10)}" stroke="#b58a3c" stroke-width="2.2"/>'
        f'<path d="M{f(x - 13)} {f(y - 8)}Q{f(x - 13)} {f(y - 18)} {f(x)} {f(y - 18)}Q{f(x + 13)} {f(y - 18)} {f(x + 13)} {f(y - 8)}Z" fill="{grad("glass-green")}" {s(1.4)}/>'
        f'<path d="M{f(x - 8)} {f(y - 14)}q4 -2 8 -2" stroke="#ffffff" stroke-opacity=".6" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
    )


def _open_book(x, y):
    return (
        f'<path d="M{f(x - 14)} {f(y - 6)}Q{f(x - 7)} {f(y - 9)} {f(x)} {f(y - 6)}Q{f(x + 7)} {f(y - 9)} {f(x + 14)} {f(y - 6)}'
        f'V{f(y + 5)}Q{f(x + 7)} {f(y + 2)} {f(x)} {f(y + 5)}Q{f(x - 7)} {f(y + 2)} {f(x - 14)} {f(y + 5)}Z" fill="#fbf8f1" {s(1.2)}/>'
        f'<path d="M{f(x)} {f(y - 6)}V{f(y + 5)}M{f(x - 11)} {f(y - 3)}h8M{f(x - 11)} {f(y)}h8M{f(x + 3)} {f(y - 3)}h8M{f(x + 3)} {f(y)}h7" stroke="#b8ad98" stroke-width=".9"/>'
    )


def reading_table(w, h):
    x0, x1 = 8, w - 8
    tall = h > w * 1.15
    top_y, top_h = 18, (h - 70 if tall else 40)
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 10)]
    for lx in (x0 + 10, x1 - 10):
        o.append(
            f'<rect x="{f(lx - 4)}" y="{f(top_y + top_h)}" width="8" height="{f(h - 8 - top_y - top_h)}" fill="#7a4d33" {s(1.6)}/>'
        )
    o.append(
        f'<rect x="{f(x0)}" y="{top_y}" width="{f(x1 - x0)}" height="{f(top_h)}" rx="4" fill="{grad("oak")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 6)}" y="{top_y + 5}" width="{f(x1 - x0 - 12)}" height="{f(top_h - 10)}" rx="2" fill="#3f6d5c" fill-opacity=".85"/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="{f(top_y + top_h)}" width="{f(x1 - x0)}" height="10" rx="3" fill="{grad("wood-front")}" {s()}/>'
    )
    if tall:
        n = max(1, int(top_h // 60))
        spots = [(w / 2, top_y + top_h * (i + 0.5) / n) for i in range(n)]
    else:
        n = max(1, int((x1 - x0) // 90))
        spots = [
            (x0 + (x1 - x0) * (i + 0.5) / n, top_y + top_h * 0.55) for i in range(n)
        ]
    for x, y in spots:
        o.append(_open_book(x + 16, y + 6))
        o.append(_bankers_lamp(x - 16, y + 2))
    return "".join(o)


def grandfather_clock(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 24, 7)]
    o.append(
        f'<rect x="{f(cx - 18)}" y="64" width="36" height="22" rx="2" fill="{grad("walnut")}" {s()}/>'
        f'<rect x="{f(cx - 12)}" y="68" width="24" height="13" rx="1.5" fill="none" stroke="#b07a52" stroke-width="1.2"/>'
    )
    o.append(
        f'<rect x="{f(cx - 13)}" y="16" width="26" height="50" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 7)} 58V30Q{f(cx - 7)} 24 {f(cx)} 24Q{f(cx + 7)} 24 {f(cx + 7)} 30V58Z" fill="#2a1a12" {s(1.4)}/>'
        f'<path d="M{f(cx)} 26V48" stroke="#d8b264" stroke-width="1.4"/>'
        f'<circle cx="{f(cx)}" cy="50" r="4.6" fill="{grad("brass")}" {s(1)}/>'
    )
    o.append(
        f'<rect x="{f(cx - 18)}" y="-18" width="36" height="36" rx="2" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 19)} -18Q{f(cx)} -36 {f(cx + 19)} -18Z" fill="{grad("walnut-top")}" {s()}/>'
    )
    for x, y in ((cx - 18, -20), (cx, -32), (cx + 18, -20)):
        o.append(f'<circle cx="{f(x)}" cy="{y}" r="3" fill="{grad("brass")}" {s(1)}/>')
    o.append(f'<circle cx="{f(cx)}" cy="0" r="13" fill="#fbf6e8" {s(1.6)}/>')
    ticks = "".join(
        f"M{f(cx + 10 * math.cos(math.radians(a)))} {f(10 * math.sin(math.radians(a)))}"
        f"L{f(cx + 12 * math.cos(math.radians(a)))} {f(12 * math.sin(math.radians(a)))}"
        for a in range(0, 360, 30)
    )
    o.append(f'<path d="{ticks}" stroke="#5a4a2c" stroke-width="1.3"/>')
    o.append(
        f'<path d="M{f(cx)} 0V-8M{f(cx)} 0l6 2" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<circle cx="{f(cx)}" cy="0" r="1.6" fill="{INK}"/>'
    )
    return "".join(o)


def card_catalogue(w, h):
    x0, x1 = 12, w - 22
    top, front, bottom = 26, 38, h - 12
    o = [shadow((x0 + x1) / 2 + 4, bottom + 2, 38, 8)]
    o.append(
        k.block(
            x0,
            x1,
            top,
            front,
            bottom,
            lid=grad("oak"),
            face=grad("wood-front"),
            side="#7a4d33",
        )
    )
    cols, rows = 4, 3
    dw, dh = (x1 - x0 - 6) / cols, (bottom - front - 6) / rows
    for r in range(rows):
        for c in range(cols):
            dx, dy = x0 + 3 + c * dw, front + 3 + r * dh
            o.append(
                f'<rect x="{f(dx + 1)}" y="{f(dy + 1)}" width="{f(dw - 2)}" height="{f(dh - 2)}" rx="1.2" fill="#c08a52" stroke="#5a3826" stroke-width="1"/>'
                f'<rect x="{f(dx + dw / 2 - 4)}" y="{f(dy + 3)}" width="8" height="4.4" fill="#fbf6e8" stroke="#d8b264" stroke-width=".9"/>'
                f'<circle cx="{f(dx + dw / 2)}" cy="{f(dy + dh - 4.6)}" r="1.6" fill="#d8b264" stroke="{INK}" stroke-width=".6"/>'
            )
    return "".join(o)


def book_stack(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 8)]

    def stack(x, base, heights, widths, seed):
        out, y = [], base
        for i, (bh, bw) in enumerate(zip(heights, widths)):
            colour = BOOK_COLOURS[(seed + i * 3) % len(BOOK_COLOURS)]
            shift = ((i * 5) % 3 - 1) * 2
            out.append(
                f'<rect x="{f(x - bw / 2 + shift)}" y="{f(y - bh)}" width="{f(bw)}" height="{f(bh)}" rx="1.6" fill="{colour}" {s(1.4)}/>'
                f'<path d="M{f(x - bw / 2 + shift + 4)} {f(y - bh / 2)}h{f(bw - 8)}" stroke="#e2c27a" stroke-width="1" stroke-opacity=".8"/>'
            )
            y -= bh
        top_bw = widths[-1]
        out.append(
            f'<path d="M{f(x - top_bw / 2)} {f(y)}l4 -5h{f(top_bw)}l-4 5Z" fill="#efe6d2" {s(1.2)}/>'
        )
        return "".join(out)

    o.append(stack(cx - 14, 84, (9, 8, 10, 7, 9), (44, 40, 46, 38, 42), 0))
    o.append(stack(cx + 22, 84, (10, 8, 9), (34, 30, 36), 2))
    o.append(
        f'<circle cx="{f(cx + 16)}" cy="48" r="4" fill="none" stroke="{INK}" stroke-width="1.6"/>'
        f'<circle cx="{f(cx + 26)}" cy="48" r="4" fill="none" stroke="{INK}" stroke-width="1.6"/>'
        f'<path d="M{f(cx + 20)} 48h2" stroke="{INK}" stroke-width="1.4"/>'
    )
    return "".join(o)


def circulation_desk(w, h):
    cx = w / 2
    x0, x1 = cx - 38, cx + 30
    o = [shadow(cx, h - 12, 40, 8)]
    o.append(
        k.block(
            x0, x1, 36, 50, 86, lid=grad("oak"), face=grad("wood-front"), side="#7a4d33"
        )
    )
    for px in (x0 + 4, (x0 + x1) / 2 + 2):
        o.append(
            f'<rect x="{f(px)}" y="56" width="{f((x1 - x0) / 2 - 8)}" height="24" rx="2" fill="none" stroke="#6e4527" stroke-width="1.4"/>'
        )
    o.append(
        f'<ellipse cx="{f(x0 + 14)}" cy="44" rx="7" ry="2.6" fill="#3a3f44" {s(1)}/>'
        f'<path d="M{f(x0 + 7)} 44Q{f(x0 + 7)} 34 {f(x0 + 14)} 34Q{f(x0 + 21)} 34 {f(x0 + 21)} 44" fill="{grad("brass")}" {s(1.2)}/>'
        f'<circle cx="{f(x0 + 14)}" cy="32" r="1.8" fill="{grad("brass")}" {s(.8)}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 28)}" y="34" width="10" height="7" rx="1" fill="#26262b"/>'
        f'<rect x="{f(x0 + 31)}" y="26" width="4" height="9" rx="2" fill="#7a2f3f" {s(.8)}/>'
    )
    o.append(_book_row(x1 - 22, x1 + 4, 46, 18, seed=3))
    return "".join(o)


def owl(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 24, 6)]
    o.append(
        f'<ellipse cx="{f(cx)}" cy="82" rx="18" ry="5.4" fill="{grad("walnut")}" {s(1.6)}/>'
    )
    o.append(k.outlined(f"M{f(cx + 6)} 82V66", "#6f4a2c", 4, cap="butt"))
    o.append(k.outlined(f"M{f(cx - 26)} 66Q{f(cx)} 62 {f(cx + 24)} 66", "#7a4d33", 4.6))
    o.append(
        f'<path d="M{f(cx - 18)} 64Q{f(cx - 24)} 34 {f(cx - 12)} 22L{f(cx - 14)} 12L{f(cx - 5)} 19Q{f(cx)} 17 {f(cx + 5)} 19'
        f'L{f(cx + 14)} 12L{f(cx + 12)} 22Q{f(cx + 24)} 34 {f(cx + 18)} 64Z" fill="#b07a45" {s()}/>'
    )
    o.append(f'<ellipse cx="{f(cx)}" cy="48" rx="11" ry="14" fill="#e8cf9f" {s(1.2)}/>')
    marks = "".join(
        f"M{f(cx + dx - 2)} {y}l2 2.4 2 -2.4"
        for dx, y in ((-5, 42), (4, 42), (0, 48), (-5, 54), (4, 54), (0, 59))
    )
    o.append(f'<path d="{marks}" fill="none" stroke="#8a5a33" stroke-width="1.2"/>')
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(cx + side * 7)}" cy="29" r="7.4" fill="#f3e3c3" {s(1.2)}/>'
            f'<circle cx="{f(cx + side * 7)}" cy="29" r="4.6" fill="#f2b33d" stroke="{INK}" stroke-width="1"/>'
            f'<circle cx="{f(cx + side * 7)}" cy="29" r="2.6" fill="{INK}"/>'
            f'<circle cx="{f(cx + side * 7 - 1)}" cy="28" r=".9" fill="#ffffff"/>'
        )
        o.append(
            f'<path d="M{f(cx + side * 16)} 40Q{f(cx + side * 21)} 52 {f(cx + side * 15)} 62" fill="none" stroke="#7a4d33" stroke-width="2"/>'
        )
    o.append(
        f'<path d="M{f(cx - 2.6)} 34L{f(cx)} 39L{f(cx + 2.6)} 34Z" fill="#3b2a1e"/>'
        f'<path d="M{f(cx - 6)} 64l-2 4M{f(cx - 3)} 64v4M{f(cx + 3)} 64v4M{f(cx + 6)} 64l2 4" stroke="#d9a441" stroke-width="1.6" stroke-linecap="round"/>'
    )
    return "".join(o)


def globe(w, h):
    cx = w / 2
    gy, r = 20, 26
    o = [shadow(cx, h - 12, 26, 7)]
    for fx, fy in ((cx - 22, 86), (cx + 22, 86), (cx + 2, 80)):
        o.append(k.outlined(f"M{f(cx)} 56L{f(fx)} {fy}", "#7a4d33", 3.6))
    o.append(k.outlined(f"M{f(cx)} 58V{gy + r}", "#7a4d33", 4, cap="butt"))
    o.append(f'<circle cx="{f(cx)}" cy="{gy}" r="{r}" fill="{grad("ocean")}" {s()}/>')
    lands = (
        f"M{f(cx - 16)} {gy - 14}Q{f(cx - 6)} {gy - 20} {f(cx - 2)} {gy - 10}Q{f(cx - 8)} {gy - 2} {f(cx - 4)} {gy + 8}Q{f(cx - 12)} {gy + 4} {f(cx - 16)} {gy - 4}Q{f(cx - 22)} {gy - 8} {f(cx - 16)} {gy - 14}Z",
        f"M{f(cx + 6)} {gy - 18}Q{f(cx + 18)} {gy - 18} {f(cx + 20)} {gy - 6}Q{f(cx + 14)} {gy - 4} {f(cx + 12)} {gy + 6}Q{f(cx + 18)} {gy + 14} {f(cx + 8)} {gy + 18}Q{f(cx + 4)} {gy + 6} {f(cx + 4)} {gy - 4}Q{f(cx)} {gy - 12} {f(cx + 6)} {gy - 18}Z",
    )
    for d, colour in zip(lands, ("#c9b98a", "#8fbf6a")):
        o.append(f'<path d="{d}" fill="{colour}" stroke="#4a5a3a" stroke-width="1.2"/>')
    o.append(
        k.highlight(
            f"M{f(cx - 18)} {gy - 8}Q{f(cx - 14)} {gy - 20} {f(cx - 2)} {gy - 22}",
            0.55,
            3,
        )
    )
    o.append(
        f'<path d="M{f(cx + 3)} {gy - r - 5}A{r + 5} {r + 5} 0 0 1 {f(cx + 3)} {gy + r + 5}" fill="none" stroke="{INK}" stroke-width="5"/>'
        f'<path d="M{f(cx + 3)} {gy - r - 5}A{r + 5} {r + 5} 0 0 1 {f(cx + 3)} {gy + r + 5}" fill="none" stroke="#d8b264" stroke-width="2.6"/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{gy + 6}" rx="{r + 7}" ry="7" fill="none" stroke="{INK}" stroke-width="6"/>'
        f'<ellipse cx="{f(cx)}" cy="{gy + 6}" rx="{r + 7}" ry="7" fill="none" stroke="#a8723f" stroke-width="3.4"/>'
    )
    return "".join(o)


def telescope(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 28, 7)]
    for fx, fy in ((cx - 24, 86), (cx + 22, 86), (cx + 4, 80)):
        o.append(k.outlined(f"M{f(cx)} 40L{f(fx)} {fy}", "#7a4d33", 3.4))
    o.append(
        f'<rect x="{f(cx - 5)}" y="34" width="10" height="9" rx="2" fill="#5a3826" {s(1.4)}/>'
    )
    o.append(f'<g transform="rotate(-32 {f(cx)} 26)">')
    o.append(
        f'<path d="M{f(cx - 34)} 21H{f(cx - 14)}V31H{f(cx - 34)}Z" fill="{grad("brass")}" {s(1.6)}/>'
        f'<path d="M{f(cx - 14)} 18H{f(cx + 18)}V34H{f(cx - 14)}Z" fill="{grad("brass")}" {s()}/>'
        f'<path d="M{f(cx + 18)} 15H{f(cx + 32)}V37H{f(cx + 18)}Z" fill="{grad("brass")}" {s()}/>'
        f'<ellipse cx="{f(cx + 32)}" cy="26" rx="3" ry="11" fill="#3f6d8a" {s(1.4)}/>'
        f'<path d="M{f(cx - 14)} 18V34M{f(cx + 18)} 15V37" stroke="#9a6b1e" stroke-width="2.4"/>'
        f'<path d="M{f(cx - 10)} 21H{f(cx + 14)}" stroke="#ffffff" stroke-opacity=".5" stroke-width="2" stroke-linecap="round"/>'
    )
    o.append("</g>")
    return "".join(o)


def umbrella_stand(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 24, 6)]
    for x, top, colour, rot in (
        (cx - 8, -14, "#26262b", -8),
        (cx + 6, -6, "#7a2f3f", 6),
        (cx - 1, -2, "#2f5c48", 0),
    ):
        o.append(
            f'<g transform="rotate({rot} {f(x)} 40)">'
            f'<path d="M{f(x - 4)} 40L{f(x - 2)} {top + 10}H{f(x + 2)}L{f(x + 4)} 40Z" fill="{colour}" {s(1.4)}/>'
            + k.outlined(
                f"M{f(x)} {top + 10}V{top + 2}Q{f(x)} {top - 4} {f(x + 5)} {top - 4}Q{f(x + 9)} {top - 3} {f(x + 8)} {top + 2}",
                "#8a5a33",
                2.6,
            )
            + "</g>"
        )
    o.append(k.outlined(f"M{f(cx + 14)} 40L{f(cx + 18)} -18", "#5a3826", 2.6))
    o.append(f'<circle cx="{f(cx + 18)}" cy="-20" r="3" fill="#d6dcdb" {s(1)}/>')
    o.append(
        f'<path d="M{f(cx - 18)} 38V80Q{f(cx)} 88 {f(cx + 18)} 80V38Z" fill="#eef3f7" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 18)} 48Q{f(cx)} 54 {f(cx + 18)} 48M{f(cx - 18)} 72Q{f(cx)} 78 {f(cx + 18)} 72" fill="none" stroke="#3f6fb0" stroke-width="2.4"/>'
        f'<path d="M{f(cx - 10)} 62q4 -6 8 0t8 0" fill="none" stroke="#3f6fb0" stroke-width="1.6"/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="38" rx="18" ry="6" fill="#d6e0e8" {s(1.6)}/>'
        f'<ellipse cx="{f(cx)}" cy="38.6" rx="13" ry="3.6" fill="#2a2f33"/>'
    )
    return "".join(o)


def _book_wall(pid):
    body = '<rect width="100" height="26" fill="#4a2c1d"/>' + _book_row(1, 100, 19, 11)
    return k.face_pattern(pid, body)


def _oak_panel(pid):
    body = (
        '<rect width="100" height="26" fill="#b98a55"/>'
        '<rect x="5" y="8" width="40" height="10" rx="1.5" fill="#c99a62" stroke="#8a5a33" stroke-width="1"/>'
        '<rect x="55" y="8" width="40" height="10" rx="1.5" fill="#c99a62" stroke="#8a5a33" stroke-width="1"/>'
    )
    return k.face_pattern(pid, body)


def _gothic_window(pid):
    body = (
        '<rect width="100" height="26" fill="#a9a493"/>'
        '<path d="M0 12H100M30 7V12M70 12V19" stroke="#8a8676" stroke-width="1"/>'
        '<path d="M42 19V12Q42 6 50 5Q58 6 58 12V19Z" fill="#3f6d8a" stroke="#4a463b" stroke-width="1.6"/>'
        '<path d="M50 5V19M42 13H58" stroke="#d9b866" stroke-width="1"/>'
        '<path d="M44 18V13Q44 9 47 8" stroke="#a9cfe0" stroke-width="1" fill="none"/>'
    )
    return k.face_pattern(pid, body)


def _crimson(pid):
    body = '<rect width="100" height="26" fill="#7d2a2e"/>' + "".join(
        f'<path d="M{x} 8.5l2 3-2 3-2 -3ZM{x + 12.5} 13.5l2 3-2 3-2 -3Z" fill="#d9b45f" fill-opacity=".85"/>'
        for x in range(6, 100, 25)
    )
    return k.face_pattern(pid, body)


SKINS = {
    "chesterfield": chesterfield,
    "leather_armchair": leather_armchair,
    "book_trolley": book_trolley,
    "reading_table": reading_table,
    "grandfather_clock": grandfather_clock,
    "card_catalogue": card_catalogue,
    "book_stack": book_stack,
    "circulation_desk": circulation_desk,
    "owl": owl,
    "globe": globe,
    "telescope": telescope,
    "umbrella_stand": umbrella_stand,
}
WALLPAPERS = {
    "book_wall": _book_wall,
    "oak_panel": _oak_panel,
    "gothic_window": _gothic_window,
    "crimson": _crimson,
}
STRETCH = {"chesterfield", "book_trolley", "reading_table"}
TALL = {"grandfather_clock", "globe", "telescope", "umbrella_stand", "book_trolley"}
