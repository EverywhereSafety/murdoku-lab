"""The Thornbury Glasshouses: raised beds, beehives, orchids, a fountain and a garden gnome."""

import math

from . import _kit as k
from ._kit import INK, f, grad, legs, s, shadow

GRADIENTS = {
    "can-green": ("#7dbb86", "#4a8a5c"),
    "soil": ("#7a5638", "#5c3f27"),
    "weathered": ("#dcc39a", "#b99a6a"),
    "porcelain": ("#f4f7fa", "#d6e0e8"),
}


def _seedling(x, y, i):
    if i % 3 == 0:
        return (
            f'<ellipse cx="{f(x - 4)}" cy="{f(y)}" rx="5" ry="3.4" fill="#8cc06e" stroke="#3f6b3a" stroke-width="1"/>'
            f'<ellipse cx="{f(x + 4)}" cy="{f(y)}" rx="5" ry="3.4" fill="#8cc06e" stroke="#3f6b3a" stroke-width="1"/>'
            f'<ellipse cx="{f(x)}" cy="{f(y - 2)}" rx="4" ry="4.4" fill="#a6d38c" stroke="#3f6b3a" stroke-width="1"/>'
        )
    if i % 3 == 1:
        return (
            f'<path d="M{f(x)} {f(y + 2)}V{f(y - 8)}" stroke="#4f8452" stroke-width="1.6"/>'
            f'<ellipse cx="{f(x - 3)}" cy="{f(y - 8)}" rx="3.4" ry="2" fill="#7fb86a" stroke="#3f6b3a" stroke-width=".9"/>'
            f'<ellipse cx="{f(x + 3)}" cy="{f(y - 9)}" rx="3.4" ry="2" fill="#7fb86a" stroke="#3f6b3a" stroke-width=".9"/>'
        )
    return (
        f'<path d="M{f(x - 4)} {f(y + 2)}q-2 -8 2 -11M{f(x)} {f(y + 2)}V{f(y - 11)}M{f(x + 4)} {f(y + 2)}q2 -8 -2 -11" stroke="#5d9154" stroke-width="2" fill="none" stroke-linecap="round"/>'
        f'<path d="M{f(x - 3)} {f(y + 2)}l3 6 3 -6Z" fill="#f08a2c" stroke="{INK}" stroke-width=".8"/>'
    )


def raised_bed(w, h):
    x0, x1 = 8, w - 8
    top, front, bottom = 8, h - 32, h - 12
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 9)]
    o.append(
        f'<rect x="{f(x0)}" y="{f(front)}" width="{f(x1 - x0)}" height="{f(bottom - front)}" rx="2" fill="{grad("wood-front")}" {s()}/>'
        f'<path d="M{f(x0 + 2)} {f((front + bottom) / 2)}H{f(x1 - 2)}" stroke="#6e4527" stroke-width="1.6"/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="{top}" width="{f(x1 - x0)}" height="{f(front - top)}" rx="3" fill="{grad("weathered")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 7)}" y="{top + 7}" width="{f(x1 - x0 - 14)}" height="{f(front - top - 14)}" rx="2" fill="{grad("soil")}" stroke="#4a3220" stroke-width="1.2"/>'
    )
    rows = max(1, int((front - top - 14) // 20))
    cols = max(1, int((x1 - x0 - 14) // 20))
    i = 0
    for r in range(rows):
        y = top + 7 + (front - top - 14) * (r + 0.6) / rows
        for c in range(cols):
            x = x0 + 7 + (x1 - x0 - 14) * (c + 0.5) / cols
            o.append(_seedling(x, y, i + r))
            i += 1
    return "".join(o)


def _terra_pot(cx, base, width=10, height=14):
    return (
        f'<path d="M{f(cx - width)} {f(base - height)}L{f(cx - width + 3)} {f(base)}H{f(cx + width - 3)}L{f(cx + width)} {f(base - height)}Z" fill="{grad("terra")}" {s(1.4)}/>'
        f'<rect x="{f(cx - width - 2)}" y="{f(base - height - 4)}" width="{f(2 * width + 4)}" height="5" rx="1.6" fill="#e39a69" {s(1.2)}/>'
    )


def potting_bench(w, h):
    x0, x1 = 8, w - 8
    top_y, front = 16, h - 36
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 9)]
    o.append(
        f'<rect x="{f(x0 + 2)}" y="-16" width="{f(x1 - x0 - 4)}" height="34" rx="2" fill="{grad("weathered")}" {s()}/>'
        f'<path d="M{f(x0 + 2)} -5H{f(x1 - 2)}M{f(x0 + 2)} 6H{f(x1 - 2)}" stroke="#a88a5c" stroke-width="1.2"/>'
        f'<rect x="{f(x0)}" y="-1" width="{f(x1 - x0)}" height="5" rx="1.5" fill="#b99a6a" {s(1.4)}/>'
    )
    for i in range(max(2, int((x1 - x0) // 24))):
        o.append(_terra_pot(x0 + 14 + i * 24, -1, 6, 9))
    o.append(legs(((x0 + 6, front + 8), (x1 - 6, front + 8)), h - 8, 5, "#6e4527"))
    o.append(
        f'<rect x="{f(x0 + 8)}" y="{f(h - 22)}" width="{f(x1 - x0 - 16)}" height="5" fill="#a88a5c" {s(1.2)}/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="{top_y}" width="{f(x1 - x0)}" height="{f(front - top_y)}" rx="3" fill="{grad("weathered")}" {s()}/>'
    )
    slats = "".join(
        f"M{f(x0 + 3)} {f(y)}H{f(x1 - 3)}"
        for y in range(top_y + 10, int(front) - 4, 10)
    )
    o.append(f'<path d="{slats}" stroke="#a88a5c" stroke-width="1.2"/>')
    o.append(
        f'<rect x="{f(x0)}" y="{f(front)}" width="{f(x1 - x0)}" height="10" rx="2" fill="#a88a5c" {s()}/>'
    )
    cols = max(1, int((x1 - x0) // 60))
    rows = max(1, int((front - top_y) // 52))
    for c in range(cols):
        for r in range(rows):
            bx = x0 + c * 60
            by = top_y + (front - top_y) * (r + 0.62) / rows
            o.append(
                f'<ellipse cx="{f(bx + 22)}" cy="{f(by + 4)}" rx="10" ry="4" fill="#5c3f27" fill-opacity=".8"/>'
            )
            o.append(_terra_pot(bx + 20, by + 6, 8, 12))
            o.append(_seedling(bx + 20, by - 9, 1))
            o.append(
                f'<path d="M{f(bx + 36)} {f(by + 6)}l12 -10" stroke="#9aa1a8" stroke-width="3" stroke-linecap="round"/>'
                f'<path d="M{f(bx + 36)} {f(by + 6)}l-5 4" stroke="#8a5a33" stroke-width="3.4" stroke-linecap="round"/>'
            )
    return "".join(o)


def _bee(x, y):
    return (
        f'<ellipse cx="{f(x - 1)}" cy="{f(y - 3)}" rx="2.6" ry="1.8" fill="#ffffff" fill-opacity=".85" stroke="{INK}" stroke-width=".6"/>'
        f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="3.4" ry="2.4" fill="#f2c13a" stroke="{INK}" stroke-width=".8"/>'
        f'<path d="M{f(x - 1)} {f(y - 2.2)}v4.4M{f(x + 1.2)} {f(y - 2.2)}v4.4" stroke="{INK}" stroke-width="1"/>'
    )


def beehive(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 30, 7)]
    o.append(legs(((cx - 22, 76), (cx + 22, 76)), 88, 4, "#5a3826"))
    o.append(
        f'<path d="M{f(cx - 26)} 76L{f(cx - 22)} 70H{f(cx + 22)}L{f(cx + 26)} 76Z" fill="#e8e2d2" {s(1.6)}/>'
    )
    for i in range(3):
        yb = 72 - i * 17
        yt = yb - 17
        o.append(
            f'<path d="M{f(cx - 28)} {yb}L{f(cx - 24)} {yt}H{f(cx + 24)}L{f(cx + 28)} {yb}Z" fill="#f6f3ea" {s()}/>'
            f'<path d="M{f(cx - 26)} {yt + 3}H{f(cx + 26)}" stroke="#d8d1c0" stroke-width="1.4"/>'
        )
    o.append(
        f'<rect x="{f(cx - 9)}" y="66" width="18" height="4" rx="1.5" fill="#2a221d"/>'
    )
    o.append(
        f'<path d="M{f(cx - 33)} 22L{f(cx)} 2L{f(cx + 33)} 22Z" fill="#8f9a96" {s()}/>'
        f'<path d="M{f(cx - 33)} 22H{f(cx + 33)}V26H{f(cx - 33)}Z" fill="#6f7a76" {s(1.4)}/>'
        f'<path d="M{f(cx - 22)} 15L{f(cx)} 6" stroke="#ffffff" stroke-opacity=".4" stroke-width="2" stroke-linecap="round"/>'
    )
    for x, y in ((cx - 30, 40), (cx + 32, 30), (cx + 18, 58), (cx - 16, 6)):
        o.append(_bee(x, y))
    return "".join(o)


def orchid(w, h):
    cx, base = w / 2, h - 14
    o = [shadow(cx, base + 2, 20, 5)]
    o.append(
        f'<path d="M{f(cx)} {base - 26}V{base - 100}" stroke="#c9a46a" stroke-width="2.2" stroke-linecap="round"/>'
    )
    stem = f"M{f(cx)} {base - 26}Q{f(cx - 2)} {base - 84} {f(cx + 6)} {base - 96}Q{f(cx + 20)} {base - 106} {f(cx + 32)} {base - 90}"
    o.append(f'<path d="{stem}" fill="none" stroke="#4f8452" stroke-width="2.2"/>')
    for side, rot in ((-1, -18), (1, 22)):
        o.append(
            f'<ellipse cx="{f(cx + side * 14)}" cy="{base - 30}" rx="16" ry="6" fill="#4f8a45" {s(1.4)} transform="rotate({rot} {f(cx + side * 14)} {base - 30})"/>'
        )
    for i, (x, y) in enumerate(
        (
            (cx + 2, base - 84),
            (cx + 8, base - 98),
            (cx + 20, base - 102),
            (cx + 31, base - 90),
        )
    ):
        r = 7 if i < 3 else 5.4
        petals = "".join(
            f'<ellipse cx="{f(x + r * 0.7 * math.cos(math.radians(a)))}" cy="{f(y + r * 0.7 * math.sin(math.radians(a)))}" '
            f'rx="{f(r * 0.62)}" ry="{f(r * 0.48)}" transform="rotate({a} {f(x + r * 0.7 * math.cos(math.radians(a)))} {f(y + r * 0.7 * math.sin(math.radians(a)))})"/>'
            for a in (-90, -18, 54, 126, 198)
        )
        o.append(
            f'<g fill="#e88bb8" stroke="{INK}" stroke-width=".9">{petals}</g>'
            f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r * 0.34)}" fill="#b03a7a"/>'
        )
    o.append(
        f'<path d="M{f(cx - 15)} {base - 28}L{f(cx - 12)} {base}H{f(cx + 12)}L{f(cx + 15)} {base - 28}Z" fill="{grad("porcelain")}" {s()}/>'
        f'<path d="M{f(cx - 14)} {base - 18}H{f(cx + 14)}" stroke="#4d7fa8" stroke-width="3"/>'
        f'<path d="M{f(cx - 14)} {base - 12}q3.5 -3 7 0t7 0t7 0t7 0" fill="none" stroke="#4d7fa8" stroke-width="1.2"/>'
    )
    return "".join(o)


def lemon_tree(w, h):
    cx, base = w / 2, h - 14
    o = [shadow(cx, base + 2, 26, 6)]
    o.append(
        f'<path d="M{f(cx - 2)} {base - 30}L{f(cx - 3)} {base - 62}M{f(cx + 2)} {base - 30}L{f(cx + 6)} {base - 58}" stroke="#7a4d33" stroke-width="4" stroke-linecap="round"/>'
    )
    blob = (
        f"M{f(cx - 30)} {base - 70}Q{f(cx - 38)} {base - 92} {f(cx - 20)} {base - 104}Q{f(cx - 6)} {base - 118} {f(cx + 12)} {base - 110}"
        f"Q{f(cx + 34)} {base - 106} {f(cx + 32)} {base - 84}Q{f(cx + 38)} {base - 64} {f(cx + 18)} {base - 58}"
        f"Q{f(cx)} {base - 50} {f(cx - 16)} {base - 56}Q{f(cx - 32)} {base - 56} {f(cx - 30)} {base - 70}Z"
    )
    o.append(f'<path d="{blob}" fill="{grad("leaf")}" {s()}/>')
    o.append(
        f'<path d="M{f(cx - 20)} {base - 94}Q{f(cx - 10)} {base - 106} {f(cx + 4)} {base - 104}" stroke="#bfe0a3" stroke-width="3" fill="none" stroke-linecap="round"/>'
    )
    for x, y in ((-16, -78), (4, -90), (18, -72), (-4, -66), (22, -96), (-22, -96)):
        o.append(
            f'<ellipse cx="{f(cx + x)}" cy="{base + y}" rx="5.6" ry="4.4" fill="#f5d33f" {s(1.2)} transform="rotate(-20 {f(cx + x)} {base + y})"/>'
            f'<circle cx="{f(cx + x - 2)}" cy="{base + y - 1.4}" r="1.3" fill="#ffffff" fill-opacity=".7"/>'
        )
    o.append(
        f'<path d="M{f(cx - 22)} {base - 34}L{f(cx - 17)} {base}H{f(cx + 17)}L{f(cx + 22)} {base - 34}Z" fill="{grad("terra")}" {s()}/>'
        f'<rect x="{f(cx - 25)}" y="{base - 40}" width="50" height="9" rx="3" fill="#e39a69" {s(1.8)}/>'
        f'<path d="M{f(cx - 14)} {base - 24}h8" stroke="#ffffff" stroke-opacity=".45" stroke-width="2.4" stroke-linecap="round"/>'
    )
    return "".join(o)


def pot_stack(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 8)]
    for sx, n in ((cx - 18, 4), (cx + 14, 3)):
        base = 82
        o.append(_terra_pot(sx, base, 13, 22))
        for i in range(1, n):
            y = base - 26 - i * 6
            o.append(
                f'<rect x="{f(sx - 15)}" y="{f(y)}" width="30" height="6" rx="2" fill="#e39a69" {s(1.2)}/>'
            )
    o.append(
        f'<g transform="rotate(-12 {f(cx + 30)} 78)">'
        f'<path d="M{f(cx + 20)} 70L{f(cx + 40)} 72V86L{f(cx + 22)} 84Z" fill="{grad("terra")}" {s(1.4)}/>'
        f'<ellipse cx="{f(cx + 20)}" cy="77" rx="4" ry="8" fill="#5c3f27" {s(1.4)}/></g>'
    )
    return "".join(o)


def watering_can(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 34, 7)]
    o.append(k.outlined(f"M{f(cx - 16)} 70L{f(cx - 40)} 34", "#5d9a6a", 5))
    o.append(
        f'<ellipse cx="{f(cx - 42)}" cy="31" rx="5" ry="7.4" fill="#d8b264" {s(1.4)} transform="rotate(-35 {f(cx - 42)} 31)"/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} 44V78Q{f(cx - 2)} 86 {f(cx + 18)} 78V44Z" fill="{grad("can-green")}" {s()}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx - 2)}" cy="44" rx="20" ry="6" fill="#9fd0a6" {s()}/>'
        f'<ellipse cx="{f(cx - 6)}" cy="44" rx="8" ry="2.6" fill="#2f4f3a"/>'
    )
    o.append(
        k.outlined(f"M{f(cx - 12)} 42Q{f(cx + 2)} 20 {f(cx + 16)} 46", "#5d9a6a", 4)
    )
    o.append(
        k.outlined(f"M{f(cx + 18)} 50Q{f(cx + 30)} 58 {f(cx + 18)} 72", "#5d9a6a", 3.6)
    )
    o.append(k.highlight(f"M{f(cx - 16)} 52V74", 0.5, 2.6))
    return "".join(o)


def gnome(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 22, 6)]
    o.append(
        f'<ellipse cx="{f(cx)}" cy="82" rx="19" ry="5.5" fill="#8fa48a" {s(1.6)}/>'
    )
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 7)}" cy="78" rx="6" ry="4" fill="#6b4527" {s(1.4)}/>'
        )
    o.append(
        f'<path d="M{f(cx - 16)} 78Q{f(cx - 18)} 52 {f(cx - 10)} 44H{f(cx + 10)}Q{f(cx + 18)} 52 {f(cx + 16)} 78Z" fill="#3f6fb0" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 16)}" y="60" width="32" height="5" fill="#2a221d"/>'
        f'<rect x="{f(cx - 3)}" y="59" width="6" height="7" rx="1" fill="none" stroke="#e2b44c" stroke-width="1.6"/>'
    )
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(cx + side * 17)}" cy="56" r="4" fill="#d9473a" {s(1.2)}/>'
        )
    o.append(
        f'<path d="M{f(cx - 12)} 34Q{f(cx - 14)} 56 {f(cx)} 62Q{f(cx + 14)} 56 {f(cx + 12)} 34Z" fill="#fbf8f0" {s(1.6)}/>'
        f'<path d="M{f(cx - 6)} 44q2 8 0 12M{f(cx + 5)} 44q-2 8 0 12" stroke="#d8cdbb" stroke-width="1.2" fill="none"/>'
    )
    o.append(
        f'<circle cx="{f(cx)}" cy="30" r="9" fill="#f2c9a6" {s(1.6)}/>'
        f'<circle cx="{f(cx - 4)}" cy="28" r="1.3" fill="{INK}"/><circle cx="{f(cx + 4)}" cy="28" r="1.3" fill="{INK}"/>'
        f'<circle cx="{f(cx)}" cy="33" r="3.2" fill="#e8907a" {s(1)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 13)} 28Q{f(cx - 10)} 12 {f(cx + 2)} -14Q{f(cx + 8)} 6 {f(cx + 13)} 28Z" fill="#d9473a" {s()}/>'
        f'<path d="M{f(cx - 6)} 14Q{f(cx - 2)} 0 {f(cx + 1)} -8" stroke="#ffffff" stroke-opacity=".35" stroke-width="2" fill="none" stroke-linecap="round"/>'
    )
    return "".join(o)


def fountain(w, h):
    cx = w / 2
    o = [shadow(cx, h - 10, 42, 9)]
    o.append(
        f'<path d="M{f(cx - 40)} 62V72Q{f(cx)} 90 {f(cx + 40)} 72V62Z" fill="{grad("stone-front")}" {s()}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="62" rx="40" ry="13" fill="{grad("stone")}" {s()}/>'
        f'<ellipse cx="{f(cx)}" cy="63" rx="33" ry="9" fill="{grad("water")}" stroke="#3e6f7c" stroke-width="1.4"/>'
        f'<path d="M{f(cx - 22)} 64q5 -2.4 10 0M{f(cx + 10)} 66q5 -2.4 10 0" stroke="#eaf8f8" stroke-width="1.4" fill="none"/>'
    )
    o.append(
        f'<rect x="{f(cx - 6)}" y="24" width="12" height="40" fill="{grad("stone")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 20)} 22V26Q{f(cx)} 36 {f(cx + 20)} 26V22Z" fill="{grad("stone-front")}" {s(1.8)}/>'
        f'<ellipse cx="{f(cx)}" cy="22" rx="20" ry="6" fill="{grad("stone")}" {s(1.8)}/>'
        f'<ellipse cx="{f(cx)}" cy="22.5" rx="15" ry="3.6" fill="#9fd0da"/>'
    )
    o.append(
        f'<path d="M{f(cx - 18)} 25Q{f(cx - 28)} 36 {f(cx - 26)} 58M{f(cx + 18)} 25Q{f(cx + 28)} 36 {f(cx + 26)} 58" fill="none" stroke="#bfe6f0" stroke-width="3" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx)} 20V-6M{f(cx)} -6Q{f(cx - 10)} -12 {f(cx - 14)} 18M{f(cx)} -6Q{f(cx + 10)} -12 {f(cx + 14)} 18" fill="none" stroke="#bfe6f0" stroke-width="2.6" stroke-linecap="round"/>'
        f'<path d="M{f(cx)} 18V-4" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round"/>'
    )
    o.append(f'<circle cx="{f(cx)}" cy="18" r="3.4" fill="{grad("stone")}" {s(1.2)}/>')
    return "".join(o)


def wardian_case(w, h):
    cx = w / 2
    x0, x1 = 14, w - 14
    o = [shadow(cx, h - 12, (x1 - x0) / 2 + 4, 8)]
    o.append(legs(((x0 + 6, 56), (x1 - 6, 56)), 88, 4.4, "#5a3826"))
    o.append(
        f'<rect x="{f(x0)}" y="48" width="{f(x1 - x0)}" height="10" rx="2" fill="{grad("walnut")}" {s()}/>'
    )
    for x, rot in (
        (cx - 10, -24),
        (cx, 0),
        (cx + 12, 26),
        (cx - 18, -40),
        (cx + 20, 42),
    ):
        o.append(
            f'<g transform="rotate({rot} {f(x)} 46)"><path d="M{f(x)} 46V14" stroke="#4f8452" stroke-width="1.6"/>'
            + "".join(
                f'<path d="M{f(x)} {y}l-5 3M{f(x)} {y}l5 3" stroke="#6fae63" stroke-width="2.4" stroke-linecap="round"/>'
                for y in range(18, 44, 5)
            )
            + "</g>"
        )
    o.append(
        f'<rect x="{f(x0 + 2)}" y="14" width="{f(x1 - x0 - 4)}" height="34" fill="#d6f1f6" fill-opacity=".22" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(x0)} 14L{f(cx)} -16L{f(x1)} 14Z" fill="#d6f1f6" fill-opacity=".3" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(cx)} 14V48M{f(x0 + 2)} 30H{f(x1 - 2)}M{f(cx)} -16V14M{f((x0 + cx) / 2)} -1V14M{f((x1 + cx) / 2)} -1V14" stroke="#f6f3ea" stroke-width="2"/>'
    )
    o.append(
        f'<path d="M{f(x0 + 6)} 44l12 -24M{f(cx + 4)} 44l8 -16" stroke="#ffffff" stroke-opacity=".6" stroke-width="2" stroke-linecap="round"/>'
    )
    o.append(f'<circle cx="{f(cx)}" cy="-18" r="3.4" fill="{grad("brass")}" {s(1.2)}/>')
    return "".join(o)


def rain_barrel(w, h):
    cx = w / 2
    top, bottom = 22, h - 12
    o = [shadow(cx, bottom + 2, 30, 8)]
    o.append(
        k.outlined(
            f"M{f(cx + 14)} -32V12Q{f(cx + 14)} 18 {f(cx + 8)} 20",
            "#8f9a96",
            5,
            cap="butt",
        )
    )
    o.append(f'<rect x="{f(cx + 10)}" y="-14" width="8" height="4" fill="#5a6066"/>')
    mid = (top + bottom) / 2
    o.append(
        f'<path d="M{f(cx - 26)} {top + 6}Q{f(cx - 32)} {f(mid)} {f(cx - 26)} {bottom}Q{f(cx)} {bottom + 8} {f(cx + 26)} {bottom}'
        f'Q{f(cx + 32)} {f(mid)} {f(cx + 26)} {top + 6}Z" fill="{grad("barrel")}" {s()}/>'
    )
    for sx in (-13, 0, 13):
        o.append(
            f'<path d="M{f(cx + sx)} {top + 8}Q{f(cx + sx * 1.15)} {f(mid)} {f(cx + sx)} {bottom + 2}" stroke="#8a5530" stroke-width="1.4" fill="none"/>'
        )
    for yy in (top + 18, bottom - 14):
        o.append(
            f'<path d="M{f(cx - 29)} {yy}Q{f(cx)} {yy + 7} {f(cx + 29)} {yy}" stroke="#3f6d5c" stroke-width="5" fill="none"/>'
        )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{top + 6}" rx="26" ry="8" fill="#d9a06a" {s()}/>'
        f'<ellipse cx="{f(cx)}" cy="{top + 7}" rx="21" ry="5.4" fill="{grad("water")}" stroke="#3e6f7c" stroke-width="1.2"/>'
        f'<path d="M{f(cx - 8)} {top + 7}q4 -2 8 0" stroke="#eaf8f8" stroke-width="1.2" fill="none"/>'
    )
    o.append(
        f'<rect x="{f(cx - 5)}" y="{bottom - 30}" width="10" height="6" rx="2" fill="{grad("brass")}" {s(1.2)}/>'
        f'<path d="M{f(cx)} {bottom - 24}v5" stroke="#d8b264" stroke-width="3"/>'
        f'<circle cx="{f(cx)}" cy="{bottom - 15}" r="1.8" fill="#9fd0da"/>'
    )
    return "".join(o)


def _glass_pane(pid):
    body = (
        '<rect width="100" height="26" fill="#cfe9e4"/>'
        '<path d="M8 19L22 6M58 19L70 7" stroke="#ffffff" stroke-opacity=".6" stroke-width="2.4"/>'
        '<path d="M80 19q-6 -4 -4 -10q5 2 4 10ZM35 19q4 -6 10 -5q-3 5 -10 5Z" fill="#7fb86a" fill-opacity=".8"/>'
        '<path d="M0 13H100M0 0V19M25 0V19M50 0V19M75 0V19" stroke="#f6f8f4" stroke-width="2"/>'
    )
    return k.face_pattern(pid, body)


def _trellis(pid):
    lattice = "".join(
        f"M{x} 6L{x + 13} 19M{x + 13} 6L{x} 19" for x in range(-13, 100, 13)
    )
    leaves = "".join(
        f'<path d="M{x} {y}q4 -4 7 0q-4 4 -7 0Z" fill="#5d9154"/>'
        for x, y in ((8, 12), (30, 9), (47, 15), (66, 11), (88, 16))
    )
    body = (
        '<rect width="100" height="26" fill="#efe8d6"/>'
        f'<path d="{lattice}" stroke="#7fa392" stroke-width="1.6"/>' + leaves
    )
    return k.face_pattern(pid, body)


def _whitewash(pid):
    body = (
        '<rect width="100" height="26" fill="#f1efe8"/>'
        + "".join(
            f'<path d="M{x} 0V19" stroke="#d8d4c8" stroke-width="1.2"/>'
            for x in range(0, 100, 14)
        )
        + '<path d="M22 10q4 2 8 0M70 15q3 2 6 0" stroke="#c9c4b6" stroke-width="1" fill="none"/>'
    )
    return k.face_pattern(pid, body)


SKINS = {
    "raised_bed": raised_bed,
    "potting_bench": potting_bench,
    "beehive": beehive,
    "orchid": orchid,
    "lemon_tree": lemon_tree,
    "pot_stack": pot_stack,
    "watering_can": watering_can,
    "gnome": gnome,
    "fountain": fountain,
    "wardian_case": wardian_case,
    "rain_barrel": rain_barrel,
}
WALLPAPERS = {"glass_pane": _glass_pane, "trellis": _trellis, "whitewash": _whitewash}
STRETCH = {"raised_bed", "potting_bench"}
TALL = {
    "potting_bench",
    "beehive",
    "orchid",
    "lemon_tree",
    "gnome",
    "fountain",
    "wardian_case",
    "rain_barrel",
}
