"""Edelweiss Lodge, snowed in: rocking chairs, a stone fireplace, skis, sleds and a snowman."""

import math

from . import _kit as k
from ._kit import INK, f, grad, legs, s, shadow

GRADIENTS = {
    "fir": ("#4f8a5c", "#2f5f3d"),
    "granite": ("#c5c8c2", "#8f948d"),
    "snowmobile": ("#e2523f", "#b23424"),
    "plaid": ("#c43b3f", "#9a2a2f"),
    "bark": ("#9a6a43", "#6f4a2c"),
}


def rocking_chair(w, h):
    cx = w / 2
    wood, dark = "#b9824f", "#8a5a33"
    o = [shadow(cx, h - 12, 34, 8)]
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx + side * 22)} 54Q{f(cx + side * 31)} 82 {f(cx + side * 20)} 92",
                dark,
                4.4,
            )
        )
    for side in (-1, 1):
        o.append(k.outlined(f"M{f(cx + side * 24)} -4V54", wood, 5, cap="butt"))
    for x in (cx - 14, cx - 5, cx + 5, cx + 14):
        o.append(k.outlined(f"M{f(x)} 4V46", wood, 2.8, ink_width=4.8, cap="butt"))
    o.append(
        f'<path d="M{f(cx - 27)} -2Q{f(cx)} -16 {f(cx + 27)} -2V6Q{f(cx)} -8 {f(cx - 27)} 6Z" fill="{grad("wood")}" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 20)} 2V36L{f(cx - 14)} 40L{f(cx - 8)} 36V0Z" fill="{grad("plaid")}" {s(1.4)}/>'
        f'<path d="M{f(cx - 20)} 14H{f(cx - 8)}M{f(cx - 20)} 26H{f(cx - 8)}M{f(cx - 14)} 2V38" stroke="#f3d68c" stroke-width="1.2"/>'
    )
    for side in (-1, 1):
        o.append(
            k.outlined(f"M{f(cx + side * 24)} 30L{f(cx + side * 33)} 44V62", wood, 3.6)
        )
    o.append(
        f'<path d="M{f(cx - 28)} 46H{f(cx + 28)}L{f(cx + 31)} 62H{f(cx - 31)}Z" fill="{grad("wood")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 24)}" y="44" width="48" height="12" rx="5" fill="{grad("plaid")}" {s(1.6)}/>'
        f'<path d="M{f(cx - 8)} 44v12M{f(cx + 8)} 44v12M{f(cx - 24)} 50h48" stroke="#f3d68c" stroke-width="1.2"/>'
    )
    o.append(
        f'<rect x="{f(cx - 31)}" y="62" width="62" height="6" rx="2" fill="{dark}" {s(1.6)}/>'
    )
    o.append(legs(((cx - 26, 66), (cx + 26, 66)), 82, 4.4, dark))
    return "".join(o)


def sheepskin(w, h):
    x0, y0, x1, y1 = 10, 12, w - 10, h - 10
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    n = max(14, int((rx + ry) / 5))
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
        c = (cx + rx * 1.16 * math.cos(a), cy + ry * 1.16 * math.sin(a))
        p = pts[(i + 1) % n]
        d.append(f"Q{f(c[0])} {f(c[1])} {f(p[0])} {f(p[1])}")
    path = "".join(d) + "Z"
    o = [
        f'<path d="{path}" fill="#1b130e" fill-opacity=".2" transform="translate(3 5)" filter="url(#mk-softer)"/>'
    ]
    o.append(f'<path d="{path}" fill="#f8f4ec" {s(2)}/>')
    curls = []
    for yy in range(int(y0 + 10), int(y1 - 6), 13):
        for xx in range(int(x0 + 12), int(x1 - 8), 15):
            jitter = 4 if (xx // 15 + yy // 13) % 2 else 0
            px, py = xx + jitter, yy
            if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 < 0.72:
                curls.append(f"M{f(px)} {f(py)}a3 3 0 1 1 3 3")
    o.append(
        f'<path d="{"".join(curls)}" fill="none" stroke="#d8cdbb" stroke-width="1.6" stroke-linecap="round"/>'
    )
    return "".join(o)


def snowmobile(w, h):
    if h > w * 1.15 or w < 150:
        if h > 100:
            return f'<g transform="translate(0 {f(h - 100)})">{_snowmobile_front(w, 100)}</g>'
        return _snowmobile_front(w, h)
    x0, x1 = 8, w - 8
    o = [shadow(w / 2, h - 12, (x1 - x0) / 2, 9)]
    o.append(
        k.outlined(
            f"M{f(x0 + 4)} 62Q{f(x0)} 78 {f(x0 + 18)} 78H{f(x0 + 86)}", "#3a3f44", 4
        )
    )
    o.append(k.outlined(f"M{f(x0 + 40)} 76V60", "#3a3f44", 3))
    o.append(
        f'<rect x="{f(x0 + 80)}" y="56" width="{f(x1 - x0 - 86)}" height="24" rx="12" fill="#26262b" {s()}/>'
    )
    treads = "".join(f"M{f(x)} 78v3" for x in range(int(x0 + 88), int(x1 - 10), 7))
    o.append(f'<path d="{treads}" stroke="#1b1b1f" stroke-width="2.4"/>')
    for wx in (x0 + 92, (x0 + x1) / 2 + 20, x1 - 20):
        o.append(
            f'<circle cx="{f(wx)}" cy="68" r="6" fill="#5a6066" stroke="#1b1b1f" stroke-width="1.4"/>'
        )
    o.append(
        f'<path d="M{f(x0 + 8)} 62Q{f(x0 + 4)} 44 {f(x0 + 30)} 40L{f(x0 + 80)} 32L{f(x0 + 96)} 58H{f(x1 - 8)}V64H{f(x0 + 8)}Z" '
        f'fill="{grad("snowmobile")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 12)} 54H{f(x1 - 12)}" stroke="#f6efe0" stroke-width="3"/>'
        f'<path d="M{f(x0 + 12)} 58H{f(x1 - 12)}" stroke="#e2b44c" stroke-width="2"/>'
    )
    o.append(
        f'<path d="M{f(x0 + 72)} 34L{f(x0 + 80)} 12L{f(x0 + 92)} 14L{f(x0 + 88)} 34Z" fill="#cfe8f1" fill-opacity=".85" {s(1.8)}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 94)}" y="38" width="{f(x1 - x0 - 112)}" height="13" rx="6" fill="#26262b" {s()}/>'
    )
    o.append(k.outlined(f"M{f(x0 + 84)} 32L{f(x0 + 90)} 22", "#3a3f44", 3))
    o.append(
        f'<ellipse cx="{f(x0 + 16)}" cy="48" rx="6" ry="4.5" fill="#fff3c8" {s(1.4)}/>'
    )
    o.append(k.highlight(f"M{f(x0 + 22)} 44L{f(x0 + 60)} 38", 0.45, 2.4))
    return "".join(o)


def _snowmobile_front(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 34, 8)]
    for side in (-1, 1):
        o.append(k.outlined(f"M{f(cx + side * 24)} 66V86", "#3a3f44", 5, cap="round"))
    o.append(
        f'<rect x="{f(cx - 22)}" y="54" width="44" height="14" rx="6" fill="#26262b" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 30)} 66Q{f(cx - 32)} 36 {f(cx - 16)} 30H{f(cx + 16)}Q{f(cx + 32)} 36 {f(cx + 30)} 66Z" fill="{grad("snowmobile")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 16)} 30L{f(cx - 12)} 8H{f(cx + 12)}L{f(cx + 16)} 30Z" fill="#cfe8f1" fill-opacity=".85" {s(1.8)}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="50" rx="9" ry="6" fill="#fff3c8" {s(1.4)}/>'
        f'<path d="M{f(cx - 28)} 60H{f(cx + 28)}" stroke="#f6efe0" stroke-width="3"/>'
    )
    return "".join(o)


def stone_fireplace(w, h):
    cx = w / 2
    o = [
        f'<ellipse cx="{f(cx)}" cy="{h - 6}" rx="42" ry="8" fill="#ffb85c" fill-opacity=".28"/>',
        shadow(cx, h - 12, 42, 8),
    ]
    o.append(
        f'<rect x="{f(cx - 24)}" y="-34" width="48" height="42" fill="#a9a597" {s()}/>'
    )
    stones = [
        (cx - 24, -34, 20, 11),
        (cx - 2, -34, 26, 11),
        (cx - 24, -21, 30, 12),
        (cx + 8, -21, 16, 12),
        (cx - 24, -7, 16, 13),
        (cx - 6, -7, 30, 13),
    ]
    for x, y, ww, hh in stones:
        o.append(
            f'<rect x="{f(x + 1.5)}" y="{f(y + 1.5)}" width="{f(ww - 3)}" height="{f(hh - 3)}" rx="3" fill="#bdb9ab" stroke="#7d796c" stroke-width="1"/>'
        )
    o.append(
        f'<rect x="{f(cx - 40)}" y="10" width="80" height="74" rx="4" fill="{grad("stone")}" {s()}/>'
    )
    for row, y in enumerate(range(12, 82, 14)):
        x = cx - 40 + (8 if row % 2 else 0)
        while x < cx + 38:
            ww = 18 + (int(x + y) % 3) * 4
            o.append(
                f'<rect x="{f(max(cx - 38, x + 1))}" y="{y + 1}" width="{f(min(ww - 2, cx + 38 - max(cx - 38, x + 1)))}" height="12" rx="3" '
                f'fill="#cfd1c6" stroke="#8f9386" stroke-width="1"/>'
            )
            x += ww
    o.append(
        f'<path d="M{f(cx - 22)} 84V50Q{f(cx - 22)} 32 {f(cx)} 32Q{f(cx + 22)} 32 {f(cx + 22)} 50V84Z" fill="#2a1d16" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 17)}" y="72" width="34" height="7" rx="3.5" fill="{grad("bark")}" {s(1.4)} transform="rotate(-8 {f(cx)} 75)"/>'
        f'<rect x="{f(cx - 17)}" y="72" width="34" height="7" rx="3.5" fill="{grad("bark")}" {s(1.4)} transform="rotate(10 {f(cx)} 75)"/>'
    )
    o.append(
        f'<path d="M{f(cx - 14)} 74Q{f(cx - 18)} 58 {f(cx - 8)} 50Q{f(cx - 6)} 60 {f(cx - 1)} 55Q{f(cx + 1)} 42 {f(cx + 9)} 48'
        f'Q{f(cx + 18)} 60 {f(cx + 14)} 74Z" fill="#f08a2c" stroke="#b5521c" stroke-width="1.4"/>'
        f'<path d="M{f(cx - 8)} 74Q{f(cx - 10)} 64 {f(cx - 3)} 60Q{f(cx)} 66 {f(cx + 3)} 58Q{f(cx + 10)} 66 {f(cx + 8)} 74Z" fill="#ffd166"/>'
    )
    o.append(
        f'<rect x="{f(cx - 46)}" y="14" width="92" height="9" rx="2" fill="{grad("walnut")}" {s()}/>'
    )
    for x in (cx - 36, cx + 32):
        o.append(
            f'<rect x="{f(x - 2.5)}" y="2" width="5" height="12" fill="#f6efe0" {s(1)}/>'
            f'<path d="M{f(x)} 1q2 -3 0 -6q-2 3 0 6" fill="#f4b740"/>'
        )
    o.append(
        f'<rect x="{f(cx - 44)}" y="82" width="88" height="8" rx="3" fill="#bdb9ab" {s(1.6)}/>'
    )
    return "".join(o)


def ski_rack(w, h):
    if h > w * 1.15:
        return "".join(
            f'<g transform="translate(0 {i * 100})">{ski_rack(w, 100)}</g>'
            for i in range(int(round(h / 100)))
        )
    x0, x1 = 10, w - 10
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 8)]
    for px in (x0 + 2, x1 - 2):
        o.append(k.outlined(f"M{f(px)} -8V84", "#9a6a43", 4.4, cap="butt"))
    o.append(k.outlined(f"M{f(x0)} 4H{f(x1)}", "#b9824f", 4, cap="butt"))
    colours = ("#d9473a", "#3f6fb0", "#e2b44c", "#2f8f83", "#7a4c9a")
    n = max(2, int((x1 - x0 - 12) // 16))
    step = (x1 - x0 - 16) / n
    for i in range(n):
        sx = x0 + 10 + step * (i + 0.5)
        colour = colours[i % len(colours)]
        for dx in (-3.2, 3.2):
            x = sx + dx
            o.append(
                f'<path d="M{f(x - 2.4)} 84V-16Q{f(x - 2.4)} -26 {f(x + 1)} -28Q{f(x + 2.6)} -24 {f(x + 2.4)} -16V84Z" '
                f'fill="{colour}" stroke="{INK}" stroke-width="1.4"/>'
            )
        o.append(
            f'<rect x="{f(sx - 6)}" y="40" width="12" height="7" rx="2" fill="#26262b"/>'
        )
    o.append(k.outlined(f"M{f(x0)} 62H{f(x1)}", "#b9824f", 4, cap="butt"))
    return "".join(o)


def fir_tree(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx, base, 30, 8)]
    o.append(
        f'<rect x="{f(cx - 4)}" y="{base - 32}" width="8" height="12" fill="#6f4a2c" {s(1.4)}/>'
    )
    tiers = ((34, 28, 70), (27, 52, 92), (19, 74, 112))
    for half, bottom, apex in tiers:
        yb, ya = base - bottom, base - apex
        scallop = "".join(
            f"Q{f(cx + half - (i + 0.5) * 2 * half / 5)} {f(yb + 6)} {f(cx + half - (i + 1) * 2 * half / 5)} {f(yb)}"
            for i in range(5)
        )
        o.append(
            f'<path d="M{f(cx)} {f(ya)}L{f(cx + half)} {f(yb)}{scallop}Z" fill="{grad("fir")}" {s()}/>'
        )
        snow = "".join(
            f"Q{f(cx + half - (i + 0.5) * 2 * half / 5)} {f(yb - 1)} {f(cx + half - (i + 1) * 2 * half / 5)} {f(yb - 5)}"
            for i in range(5)
        )
        o.append(
            f'<path d="M{f(cx + half - 2)} {f(yb - 1)}{snow}" fill="none" stroke="#fbfdff" stroke-width="3.6" stroke-linecap="round"/>'
        )
    o.append(
        f'<path d="M{f(cx - 6)} {base - 104}L{f(cx)} {base - 114}L{f(cx + 6)} {base - 104}Q{f(cx)} {base - 100} {f(cx - 6)} {base - 104}Z" fill="#fbfdff" {s(1.2)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 16)} {base - 22}L{f(cx - 13)} {base}H{f(cx + 13)}L{f(cx + 16)} {base - 22}Z" fill="{grad("barrel")}" {s()}/>'
        f'<path d="M{f(cx - 15)} {base - 15}H{f(cx + 15)}M{f(cx - 14)} {base - 6}H{f(cx + 14)}" stroke="#3d3a36" stroke-width="2.4"/>'
    )
    return "".join(o)


def snowman(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx, base, 30, 8)]
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{base - 4}" rx="30" ry="8" fill="#fbfdff" stroke="#9fb6c8" stroke-width="1.6"/>'
    )
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx + side * 13)} {base - 52}L{f(cx + side * 34)} {base - 68}M{f(cx + side * 27)} {base - 63}l{f(side * 2)} -8",
                "#6f4a2c",
                2.4,
            )
        )
    for r, y in ((21, base - 22), (15, base - 52), (11, base - 74)):
        o.append(
            f'<circle cx="{f(cx)}" cy="{f(y)}" r="{r}" fill="#fbfdff" {s()}/>'
            f'<path d="M{f(cx + r * 0.2)} {f(y + r * 0.95)}A{r} {r} 0 0 0 {f(cx + r * 0.95)} {f(y + r * 0.2)}" fill="none" stroke="#b9cfdd" stroke-width="3"/>'
        )
    for y in (base - 58, base - 50, base - 42):
        o.append(f'<circle cx="{f(cx)}" cy="{y}" r="2" fill="{INK}"/>')
    o.append(
        f'<circle cx="{f(cx - 4)}" cy="{base - 77}" r="1.8" fill="{INK}"/><circle cx="{f(cx + 4)}" cy="{base - 77}" r="1.8" fill="{INK}"/>'
        f'<path d="M{f(cx)} {base - 73}l12 3 -12 2Z" fill="#f08a2c" {s(1)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 12)} {base - 66}Q{f(cx)} {base - 60} {f(cx + 12)} {base - 66}V{base - 62}Q{f(cx)} {base - 56} {f(cx - 12)} {base - 62}Z" fill="#d9473a" {s(1.4)}/>'
        f'<path d="M{f(cx + 6)} {base - 62}l4 16h6l-3 -17Z" fill="#d9473a" {s(1.4)}/>'
    )
    o.append(
        f'<rect x="{f(cx - 14)}" y="{base - 87}" width="28" height="4" rx="2" fill="#26262b"/>'
        f'<rect x="{f(cx - 9)}" y="{base - 101}" width="18" height="15" rx="2" fill="#26262b"/>'
        f'<rect x="{f(cx - 9)}" y="{base - 91}" width="18" height="3" fill="#d9473a"/>'
    )
    return "".join(o)


def firewood(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 38, 8)]
    for side in (-1, 1):
        o.append(k.outlined(f"M{f(cx + side * 38)} 40V84", "#3a3f44", 3.4, cap="butt"))
    rows = ((4, 76), (3, 60), (2, 44))
    r = 8.5
    for count, y in rows:
        x_start = cx - (count - 1) * 8.5 - 4
        for i in range(count):
            x = x_start + i * 17
            o.append(
                f'<path d="M{f(x)} {f(y - r)}L{f(x + 8)} {f(y - r - 10)}A{r} {r} 0 0 1 {f(x + 8)} {f(y + r - 10)}L{f(x)} {f(y + r)}Z" '
                f'fill="{grad("bark")}" {s(1.4)}/>'
            )
            o.append(
                f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="#e3b985" {s(1.6)}/>'
                f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r * 0.55)}" fill="none" stroke="#b9895a" stroke-width="1"/>'
                f'<circle cx="{f(x)}" cy="{f(y)}" r="1.4" fill="#b9895a"/>'
            )
    o.append(k.outlined(f"M{f(cx - 40)} 84H{f(cx + 40)}", "#3a3f44", 3.4, cap="butt"))
    return "".join(o)


def sled(w, h):
    cx = w / 2
    red, wood = "#c4302b", "#d9a86c"
    o = [shadow(cx, h - 12, 38, 7)]
    far = f"M{f(cx - 30)} 66Q{f(cx - 40)} 62 {f(cx - 36)} 50Q{f(cx - 32)} 44 {f(cx - 26)} 50M{f(cx - 30)} 66H{f(cx + 38)}"
    o.append(k.outlined(far, "#9a2a26", 3.6))
    o.append(
        f'<path d="M{f(cx - 34)} 64L{f(cx - 26)} 52H{f(cx + 40)}L{f(cx + 32)} 64Z" fill="{wood}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 20)} 52L{f(cx - 28)} 64M{f(cx - 4)} 52L{f(cx - 12)} 64M{f(cx + 12)} 52L{f(cx + 4)} 64M{f(cx + 28)} 52L{f(cx + 20)} 64" stroke="#a87443" stroke-width="1.4"/>'
    )
    for x in (cx - 24, cx, cx + 24):
        o.append(k.outlined(f"M{f(x)} 64V74", red, 3, cap="butt"))
    near = f"M{f(cx - 38)} 76Q{f(cx - 50)} 72 {f(cx - 46)} 58Q{f(cx - 42)} 50 {f(cx - 34)} 58M{f(cx - 38)} 76H{f(cx + 32)}"
    o.append(k.outlined(near, red, 4.4))
    o.append(
        k.outlined(
            f"M{f(cx - 42)} 58Q{f(cx - 30)} 84 {f(cx - 8)} 84Q{f(cx + 8)} 84 {f(cx + 4)} 88",
            "#e2c48e",
            2.4,
        )
    )
    return "".join(o)


def cuckoo_clock(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 22, 6)]
    o.append(
        f'<rect x="{f(cx - 16)}" y="76" width="32" height="10" rx="3" fill="{grad("walnut")}" {s(1.8)}/>'
    )
    o.append(
        f'<rect x="{f(cx - 5)}" y="28" width="10" height="50" fill="{grad("walnut")}" {s()}/>'
    )
    for x, y in ((cx - 12, 60), (cx + 12, 68)):
        o.append(
            f'<path d="M{f(x)} 28V{y - 8}" stroke="#d8b264" stroke-width="1.4" stroke-dasharray="2 1.4"/>'
            f'<ellipse cx="{f(x)}" cy="{y}" rx="4.6" ry="8" fill="#8a5a33" {s(1.4)}/>'
            f'<path d="M{f(x - 3)} {y - 3}l3 2 3 -2M{f(x - 3)} {y + 1}l3 2 3 -2M{f(x - 3)} {y + 5}l3 2 3 -2" fill="none" stroke="#5a3826" stroke-width="1"/>'
        )
    o.append(
        f'<rect x="{f(cx - 20)}" y="-12" width="40" height="42" rx="2" fill="#c9945e" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 30)} -8L{f(cx)} -34L{f(cx + 30)} -8Z" fill="{grad("walnut")}" {s()}/>'
    )
    scallops = "".join(
        f"M{f(x)} {f(-8 - (x - (cx - 30)) * 26 / 30 if x <= cx else -8 - (cx + 30 - x) * 26 / 30)}"
        f"a2.6 2.6 0 0 0 4 2"
        for x in range(int(cx - 26), int(cx + 26), 6)
    )
    o.append(f'<path d="{scallops}" fill="none" stroke="#e8c79a" stroke-width="1.4"/>')
    o.append(
        f'<rect x="{f(cx - 5)}" y="-22" width="10" height="10" rx="1" fill="#3b2418" {s(1.2)}/>'
        f'<circle cx="{f(cx)}" cy="-16" r="3.4" fill="#e2b44c"/><path d="M{f(cx - 3)} -16l-4 1.6 4 1Z" fill="#f08a2c"/>'
        f'<circle cx="{f(cx + 1)}" cy="-17" r=".9" fill="{INK}"/>'
    )
    o.append(f'<circle cx="{f(cx)}" cy="10" r="12" fill="#fbf6e8" {s(1.6)}/>')
    ticks = "".join(
        f"M{f(cx + 9 * math.cos(math.radians(a)))} {f(10 + 9 * math.sin(math.radians(a)))}"
        f"L{f(cx + 11 * math.cos(math.radians(a)))} {f(10 + 11 * math.sin(math.radians(a)))}"
        for a in range(0, 360, 30)
    )
    o.append(f'<path d="{ticks}" stroke="#5a4a2c" stroke-width="1.2"/>')
    o.append(
        f'<path d="M{f(cx)} 10V3M{f(cx)} 10l5 3" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>'
    )
    for side in (-1, 1):
        o.append(
            f'<path d="M{f(cx + side * 20)} 24q{f(side * 6)} -4 {f(side * 4)} -12q{f(side * 4)} 6 {f(side * 2)} 12" fill="#5d9154" stroke="{INK}" stroke-width="1"/>'
        )
    return "".join(o)


def curling_stone(w, h):
    cx = w / 2
    o = [
        f'<ellipse cx="{f(cx)}" cy="78" rx="40" ry="11" fill="#e6f3f8" stroke="#b9d6e2" stroke-width="1.6"/>',
        f'<path d="M{f(cx - 30)} 80h14M{f(cx + 14)} 76h16" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round"/>',
        shadow(cx, 72, 30, 7),
    ]
    o.append(
        f'<path d="M{f(cx - 30)} 52V62Q{f(cx)} 80 {f(cx + 30)} 62V52Z" fill="{grad("granite")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 30)} 58Q{f(cx)} 74 {f(cx + 30)} 58" fill="none" stroke="#6f746e" stroke-width="2.4"/>'
    )
    o.append(f'<ellipse cx="{f(cx)}" cy="52" rx="30" ry="12" fill="#c9ccc5" {s()}/>')
    for x, y in ((-18, 50), (-8, 56), (6, 47), (16, 54), (-2, 50), (22, 49)):
        o.append(f'<circle cx="{f(cx + x)}" cy="{y}" r="1.1" fill="#7d827b"/>')
    o.append(f'<ellipse cx="{f(cx)}" cy="50" rx="9" ry="3.4" fill="#d9473a" {s(1.4)}/>')
    o.append(
        k.outlined(f"M{f(cx - 5)} 49V40H{f(cx + 18)}", "#d9473a", 5, ink_width=8.4)
    )
    return "".join(o)


def coat_stand(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 24, 6)]
    for fx, fy in ((cx - 22, 86), (cx + 22, 86), (cx + 2, 82)):
        o.append(
            k.outlined(
                f"M{f(cx)} 74Q{f((cx + fx) / 2)} {fy - 4} {f(fx)} {fy}", "#7a4d33", 3.6
            )
        )
    o.append(k.outlined(f"M{f(cx)} 82V-26", "#9a6a43", 4.6, cap="butt"))
    o.append(f'<circle cx="{f(cx)}" cy="-29" r="4.6" fill="#9a6a43" {s(1.6)}/>')
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx)} -16q{f(side * 10)} 0 {f(side * 12)} -8", "#3a3f44", 2.2
            )
        )
    o.append(
        f'<path d="M{f(cx + 6)} -14L{f(cx + 26)} -6L{f(cx + 30)} 44H{f(cx + 4)}Z" fill="#3f6d5c" {s()}/>'
        f'<path d="M{f(cx + 10)} -12L{f(cx + 18)} 10M{f(cx + 18)} 10V40" stroke="#2c4f42" stroke-width="1.4"/>'
        + "".join(
            f'<circle cx="{f(cx + 21)}" cy="{y}" r="1.6" fill="#e2c27a"/>'
            for y in (16, 26, 36)
        )
    )
    o.append(
        f'<path d="M{f(cx - 10)} -18Q{f(cx - 16)} 8 {f(cx - 14)} 38H{f(cx - 6)}Q{f(cx - 8)} 8 {f(cx - 2)} -18Z" fill="#d9473a" {s(1.6)}/>'
        f'<path d="M{f(cx - 14)} 38v6M{f(cx - 11)} 38v6M{f(cx - 8)} 38v6M{f(cx - 14)} 10h7M{f(cx - 14)} 24h7" stroke="#f6efe0" stroke-width="1.4"/>'
    )
    o.append(
        f'<path d="M{f(cx - 34)} 2Q{f(cx - 34)} -16 {f(cx - 22)} -16Q{f(cx - 10)} -16 {f(cx - 10)} 2Z" fill="#3f6fb0" {s(1.6)}/>'
        f'<path d="M{f(cx - 34)} -4H{f(cx - 10)}" stroke="#f6efe0" stroke-width="2.4"/>'
        f'<circle cx="{f(cx - 22)}" cy="-19" r="4.6" fill="#f6efe0" {s(1.2)}/>'
    )
    return "".join(o)


def _log_wall(pid):
    body = (
        '<rect width="100" height="26" fill="#8a5a37"/>'
        '<rect y="6" width="100" height="6.5" rx="3" fill="#a8774a"/>'
        '<rect y="13" width="100" height="6" rx="3" fill="#9d6c44"/>'
        '<path d="M0 7.5H100M0 14H100" stroke="#c99a68" stroke-width="1"/>'
        '<path d="M0 12.8H100M0 19H100" stroke="#5a3a22" stroke-width="1.2"/>'
        '<circle cx="3" cy="9.3" r="2.6" fill="#e3b985" stroke="#5a3a22" stroke-width=".8"/>'
        '<circle cx="3" cy="16" r="2.6" fill="#e3b985" stroke="#5a3a22" stroke-width=".8"/>'
    )
    return k.face_pattern(pid, body)


def _knotty_pine(pid):
    body = (
        '<rect width="100" height="26" fill="#d9a86c"/>'
        + "".join(
            f'<path d="M{x} 0V19" stroke="#b07a45" stroke-width="1.2"/>'
            for x in range(0, 100, 12)
        )
        + '<ellipse cx="18" cy="12" rx="1.8" ry="1.2" fill="#8a5a33"/><ellipse cx="55" cy="15" rx="1.6" ry="1.1" fill="#8a5a33"/>'
        '<ellipse cx="80" cy="10" rx="1.4" ry="1" fill="#8a5a33"/>'
    )
    return k.face_pattern(pid, body)


def _tartan(pid):
    body = (
        '<rect width="100" height="26" fill="#b8333a"/>'
        '<rect y="8.5" width="100" height="3" fill="#6f1d24" fill-opacity=".6"/>'
        '<rect y="14.5" width="100" height="3" fill="#6f1d24" fill-opacity=".6"/>'
        + "".join(
            f'<rect x="{x}" y="0" width="4" height="19" fill="#6f1d24" fill-opacity=".5"/>'
            f'<path d="M{x + 9} 0V19" stroke="#f3d68c" stroke-width=".8" stroke-opacity=".8"/>'
            for x in range(4, 100, 20)
        )
        + '<path d="M0 13H100" stroke="#2f5a3a" stroke-width="1.2"/>'
    )
    return k.face_pattern(pid, body)


SKINS = {
    "rocking_chair": rocking_chair,
    "sheepskin": sheepskin,
    "snowmobile": snowmobile,
    "stone_fireplace": stone_fireplace,
    "ski_rack": ski_rack,
    "fir_tree": fir_tree,
    "snowman": snowman,
    "firewood": firewood,
    "sled": sled,
    "cuckoo_clock": cuckoo_clock,
    "curling_stone": curling_stone,
    "coat_stand": coat_stand,
}
WALLPAPERS = {"log_wall": _log_wall, "knotty_pine": _knotty_pine, "tartan": _tartan}
STRETCH = {"sheepskin", "snowmobile", "ski_rack"}
TALL = {
    "rocking_chair",
    "stone_fireplace",
    "ski_rack",
    "fir_tree",
    "cuckoo_clock",
    "coat_stand",
}
