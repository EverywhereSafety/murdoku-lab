"""The Halloway Museum after hours: sarcophagi, vitrines, a gramophone and a meteorite.

Also the antique four-poster bed, for written themes that keep the noun "bed" in a museum or a
country house (see setter/restyles/)."""

import math

from . import _kit as k
from ._kit import INK, f, grad, legs, s, shadow

GRADIENTS = {
    "gold": ("#f3d27a", "#c8952f"),
    "lacquer": ("#7e2534", "#51141f"),
    "velvet-red": ("#c23a4c", "#8e2132"),
    "meteor": ("#64636d", "#2f2e36"),
    "marble": ("#f6f3ec", "#d4cdbf"),
    "bedpost": ("#7b4a2b", "#4b2817"),
}


def four_poster(w, h):
    """An antique four-poster: carved posts, a fringed tester and tied-back velvet curtains."""
    out = [
        k.bed(
            w,
            h,
            frame=grad("bedpost"),
            frame_light="#a8714a",
            sheet="#fbf6ea",
            blanket=grad("velvet-red"),
            band="#e2b54f",
            leg="#3b1f14",
        )
    ]

    def post(x, top, bottom):
        return (
            f'<rect x="{f(x - 3)}" y="{f(top)}" width="6" height="{f(bottom - top)}" rx="2" '
            f'fill="{grad("bedpost")}" {s(1.4)}/>'
            f'<path d="M{f(x - 3)} {f(top + 8)}h6M{f(x - 3)} {f(bottom - 10)}h6" stroke="#c99a5f" stroke-width="1.4"/>'
        )

    def finial(x, y):
        return (
            f'<circle cx="{f(x)}" cy="{f(y)}" r="4.2" fill="{grad("gold")}" {s(1.2)}/>'
        )

    def curtain(x, side, top, bottom):
        # A drape hanging from the tester, gathered by a gold tie a third of the way down.
        inner = x + side * 11
        tie = top + (bottom - top) * 0.55
        return (
            f'<path d="M{f(x)} {f(top)}H{f(inner)}Q{f(inner - side * 6)} {f(tie)} {f(inner - side * 2)} {f(bottom)}'
            f'H{f(x)}Z" fill="{grad("velvet-red")}" {s(1.6)}/>'
            f'<path d="M{f(x + side * 4)} {f(top + 4)}Q{f(x + side * 6)} {f(tie)} {f(x + side * 4)} {f(bottom - 4)}" '
            f'fill="none" stroke="#6d1726" stroke-width="1.2"/>'
            f'<rect x="{f(min(x, inner - side * 3) - 1)}" y="{f(tie - 2)}" width="{f(abs(inner - side * 3 - x) + 2)}" '
            f'height="4" rx="2" fill="{grad("gold")}" {s(1)}/>'
        )

    def tester(x0, x1, y):
        scallops = "".join(
            f"Q{f(x0 + (i + 0.5) * (x1 - x0) / n)} {f(y + 15)} {f(x0 + (i + 1) * (x1 - x0) / n)} {f(y + 9)}"
            for i, n in (
                (i, max(3, round((x1 - x0) / 18)))
                for i in range(max(3, round((x1 - x0) / 18)))
            )
        )
        return (
            f'<path d="M{f(x0)} {f(y + 9)}{scallops}V{f(y + 6)}H{f(x0)}Z" fill="{grad("velvet-red")}" {s(1.4)}/>'
            f'<rect x="{f(x0 - 3)}" y="{f(y)}" width="{f(x1 - x0 + 6)}" height="8" rx="2" fill="{grad("bedpost")}" {s(1.6)}/>'
            f'<path d="M{f(x0)} {f(y + 4)}H{f(x1)}" stroke="#e2b54f" stroke-width="1.4"/>'
        )

    if w > h * 1.15:
        # Head to the west, as the bed helper draws it: the tester crowns the headboard.
        x0, x1 = 8, w - 8
        out.append(curtain(x0 + 2, 1, -22, 48))
        out.append(post(x0 + 2, -26, 74) + post(x0 + 22, -26, 60))
        out.append(tester(x0 - 2, x0 + 26, -32))
        out.append(post(x1 - 4, 18, 74) + finial(x1 - 4, 16))
        return "".join(out)
    # Head to the north: the tester spans the headboard, short posts mark the foot.
    x0, x1 = 10, w - 10
    out.append(curtain(x0, 1, -24, 38) + curtain(x1, -1, -24, 38))
    out.append(post(x0, -28, 30) + post(x1, -28, 30))
    out.append(tester(x0 - 2, x1 + 2, -34))
    out.append(post(x0, h - 40, h - 12) + post(x1, h - 40, h - 12))
    out.append(finial(x0, h - 42) + finial(x1, h - 42))
    return "".join(out)


def sarcophagus(w, h):
    def draw(length, width):
        half = min(30, width / 2)
        sh = min(40, length * 0.42)
        outline = (
            f"M0 0Q{f(half * 0.74)} 0 {f(half * 0.8)} {f(sh * 0.45)}Q{f(half)} {f(sh * 0.75)} {f(half)} {f(sh)}"
            f"L{f(half * 0.6)} {f(length - 6)}Q{f(half * 0.52)} {f(length)} 0 {f(length)}"
            f"Q{f(-half * 0.52)} {f(length)} {f(-half * 0.6)} {f(length - 6)}L{f(-half)} {f(sh)}"
            f"Q{f(-half)} {f(sh * 0.75)} {f(-half * 0.8)} {f(sh * 0.45)}Q{f(-half * 0.74)} 0 0 0Z"
        )
        d = []
        for side in (-1, 1):
            d.append(
                f'<path d="M{f(side * 10)} 8L{f(side * half * 0.8)} {f(sh * 0.5)}L{f(side * half * 0.78)} {f(sh * 1.05)}'
                f'L{f(side * 9)} {f(sh * 0.95)}Z" fill="#2f5aa8" {s(1.4)}/>'
            )
            d.append(
                "".join(
                    f'<path d="M{f(side * 10)} {f(sh * t)}L{f(side * half * 0.79)} {f(sh * t + 2)}" stroke="#f3d27a" stroke-width="1.8"/>'
                    for t in (0.55, 0.72, 0.89)
                )
            )
        d.append(
            f'<ellipse cx="0" cy="{f(sh * 0.48)}" rx="10" ry="12" fill="#e9b867" {s(1.6)}/>'
            f'<path d="M-6 {f(sh * 0.42)}h4M2 {f(sh * 0.42)}h4" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>'
            f'<path d="M-2 {f(sh * 0.62)}h4" stroke="#8a4b2a" stroke-width="1.4" stroke-linecap="round"/>'
        )
        for i, colour in enumerate(("#2f5aa8", "#c43c3c", "#2f8f83")):
            r = 14 + i * 4
            d.append(
                f'<path d="M{f(-r)} {f(sh + 1)}Q0 {f(sh + 2 + r * 0.9)} {f(r)} {f(sh + 1)}" fill="none" stroke="{colour}" stroke-width="3"/>'
            )
        if length - sh > 34:
            col_top, col_bottom = sh + 22, length - 10
            d.append(
                f'<rect x="-5" y="{f(col_top)}" width="10" height="{f(col_bottom - col_top)}" rx="2" fill="#f6e7c0" {s(1.2)}/>'
            )
            y = col_top + 4
            i = 0
            while y < col_bottom - 6:
                shape = (
                    f'<circle cx="0" cy="{f(y + 2)}" r="2" fill="#2f5aa8"/>',
                    f'<path d="M-2.5 {f(y + 4)}h5M0 {f(y)}v4" stroke="#c43c3c" stroke-width="1.4"/>',
                    f'<path d="M-2.5 {f(y + 4)}L0 {f(y)}L2.5 {f(y + 4)}" fill="none" stroke="{INK}" stroke-width="1.2"/>',
                )[i % 3]
                d.append(shape)
                y += 8
                i += 1
        return outline, "".join(d)

    return k.lying(w, h, draw, fill=grad("gold"), band="#7a5a22")


def throne(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 9)]
    o.append(
        f'<path d="M{f(cx - 30)} 54V0Q{f(cx - 30)} -22 {f(cx)} -24Q{f(cx + 30)} -22 {f(cx + 30)} 0V54Z" fill="{grad("gold")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} 50V4Q{f(cx - 22)} -12 {f(cx)} -14Q{f(cx + 22)} -12 {f(cx + 22)} 4V50Z" fill="{grad("velvet-red")}" {s(1.6)}/>'
    )
    for bx, by in ((cx - 10, 6), (cx + 10, 6), (cx, 18), (cx - 10, 30), (cx + 10, 30)):
        o.append(f'<circle cx="{f(bx)}" cy="{by}" r="1.8" fill="#f3d27a"/>')
    o.append(
        f'<circle cx="{f(cx)}" cy="-28" r="5" fill="{grad("gold")}" {s(1.6)}/>'
        f'<path d="M{f(cx - 7)} -24h14" stroke="{INK}" stroke-width="1.6"/>'
    )
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(cx + side * 30)}" cy="-3" r="5" fill="{grad("gold")}" {s(1.6)}/>'
        )
    o.append(
        f'<rect x="{f(cx - 28)}" y="44" width="56" height="20" rx="8" fill="#d44a5c" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 31)}" y="60" width="62" height="16" rx="4" fill="{grad("gold")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 24)} 68h48" stroke="#9a6b1e" stroke-width="1.4" stroke-dasharray="3 3"/>'
    )
    for side in (-1, 1):
        ax = cx + side * 35
        o.append(
            f'<path d="M{f(ax - 7)} 78V44Q{f(ax - 7)} 34 {f(ax)} 34Q{f(ax + 7)} 34 {f(ax + 7)} 44V78Z" fill="{grad("gold")}" {s()}/>'
        )
        o.append(
            f'<circle cx="{f(ax)}" cy="42" r="3" fill="none" stroke="#9a6b1e" stroke-width="1.6"/>'
        )
        o.append(
            f'<ellipse cx="{f(cx + side * 26)}" cy="82" rx="6" ry="4" fill="{grad("gold")}" {s(1.4)}/>'
        )
    return "".join(o)


def carriage(w, h):
    if h > w * 1.15 or w < 150:
        if h > 100:
            return f'<g transform="translate(0 {f(h - 100)})">{_carriage_front(w, 100)}</g>'
        return _carriage_front(w, h)
    x0, x1 = 6, w - 6
    o = [shadow(w / 2, h - 12, (x1 - x0) / 2, 9)]
    o.append(
        k.outlined(f"M{f(x0 + 50)} 64L{f(x0 + 4)} 74", "#8a5a33", 4)
        + k.outlined(f"M{f(x0 + 50)} 58L{f(x0 + 2)} 64", "#a8723f", 4)
    )
    o.append(
        f'<path d="M{f(x0 + 46)} 60Q{f(x0 + 40)} 30 {f(x0 + 56)} 14H{f(x1 - 34)}Q{f(x1 - 22)} 22 {f(x1 - 26)} 60'
        f'Q{f((x0 + x1) / 2)} 70 {f(x0 + 46)} 60Z" fill="{grad("lacquer")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 52)}" y="6" width="{f(x1 - x0 - 84)}" height="9" rx="3" fill="#2a1a1d" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 58)} 6V0H{f(x1 - 36)}V6" fill="none" stroke="#d8b264" stroke-width="1.8"/>'
    )
    wx0, wx1 = x0 + 62, x0 + 100
    o.append(
        f'<rect x="{f(wx0)}" y="20" width="{f(wx1 - wx0)}" height="20" rx="4" fill="#cfe1ea" {s(1.6)}/>'
        f'<path d="M{f(wx0 + 4)} 26l8 -4" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(wx1 + 8)} 18V56M{f(x1 - 34)} 18V56" stroke="#d8b264" stroke-width="1.6"/>'
    )
    mx = (wx1 + 8 + x1 - 34) / 2
    o.append(
        f'<circle cx="{f(mx)}" cy="34" r="6" fill="{grad("gold")}" {s(1.4)}/>'
        f'<path d="M{f(mx - 3)} 34h6M{f(mx)} 31v6" stroke="{INK}" stroke-width="1.2"/>'
    )
    o.append(
        f'<rect x="{f(x0 + 18)}" y="30" width="30" height="8" rx="3" fill="#2a1a1d" {s(1.6)}/>'
        f'<path d="M{f(x0 + 22)} 38L{f(x0 + 26)} 52H{f(x0 + 46)}" fill="none" {s(2.4)}/>'
    )
    o.append(
        f'<rect x="{f(x0 + 44)}" y="18" width="8" height="12" rx="2" fill="{grad("brass")}" {s(1.2)}/>'
        f'<rect x="{f(x0 + 46)}" y="21" width="4" height="6" fill="#fff3c8"/>'
    )
    o.append(k.wheel(x0 + 60, 70, 15, spoke="#d8b264"))
    o.append(k.wheel(x1 - 40, 64, 21, spoke="#d8b264"))
    return "".join(o)


def _carriage_front(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 8)]
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 34)}" cy="62" rx="6" ry="20" fill="none" stroke="{INK}" stroke-width="5"/>'
            f'<ellipse cx="{f(cx + side * 34)}" cy="62" rx="6" ry="20" fill="none" stroke="#d8b264" stroke-width="2.4"/>'
        )
    o.append(
        f'<path d="M{f(cx - 28)} 66V18Q{f(cx - 28)} 8 {f(cx - 18)} 8H{f(cx + 18)}Q{f(cx + 28)} 8 {f(cx + 28)} 18V66Z" '
        f'fill="{grad("lacquer")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 30)}" y="2" width="60" height="9" rx="3" fill="#2a1a1d" {s(1.8)}/>'
    )
    o.append(
        f'<rect x="{f(cx - 18)}" y="18" width="36" height="22" rx="4" fill="#cfe1ea" {s(1.6)}/>'
        f'<path d="M{f(cx)} 18v22" stroke="{INK}" stroke-width="1.6"/>'
        f'<path d="M{f(cx - 14)} 24l7 -4" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>'
    )
    o.append(f'<path d="M{f(cx - 26)} 50h52" stroke="#d8b264" stroke-width="1.8"/>')
    for side in (-1, 1):
        lx = cx + side * 30
        o.append(
            f'<rect x="{f(lx - 4)}" y="22" width="8" height="12" rx="2" fill="{grad("brass")}" {s(1.2)}/>'
            f'<rect x="{f(lx - 2)}" y="25" width="4" height="6" fill="#fff3c8"/>'
        )
    o.append(
        k.outlined(f"M{f(cx - 12)} 66L{f(cx - 16)} 88", "#a8723f", 3.6)
        + k.outlined(f"M{f(cx + 12)} 66L{f(cx + 16)} 88", "#a8723f", 3.6)
    )
    return "".join(o)


def _crown(cx, base):
    return (
        f'<path d="M{f(cx - 10)} {f(base)}L{f(cx - 11)} {f(base - 12)}L{f(cx - 5)} {f(base - 6)}L{f(cx)} {f(base - 15)}'
        f'L{f(cx + 5)} {f(base - 6)}L{f(cx + 11)} {f(base - 12)}L{f(cx + 10)} {f(base)}Z" fill="{grad("gold")}" {s(1.4)}/>'
        f'<circle cx="{f(cx)}" cy="{f(base - 4)}" r="2.2" fill="#c43c3c"/>'
        f'<circle cx="{f(cx - 6)}" cy="{f(base - 4)}" r="1.5" fill="#2f5aa8"/><circle cx="{f(cx + 6)}" cy="{f(base - 4)}" r="1.5" fill="#2f8f83"/>'
    )


def _egg(cx, base):
    return (
        f'<rect x="{f(cx - 5)}" y="{f(base - 4)}" width="10" height="4" rx="1" fill="{grad("gold")}" {s(1.1)}/>'
        f'<path d="M{f(cx)} {f(base - 20)}Q{f(cx + 9)} {f(base - 18)} {f(cx + 8)} {f(base - 9)}Q{f(cx + 7)} {f(base - 3)} {f(cx)} {f(base - 3)}'
        f'Q{f(cx - 7)} {f(base - 3)} {f(cx - 8)} {f(base - 9)}Q{f(cx - 9)} {f(base - 18)} {f(cx)} {f(base - 20)}Z" fill="#3f8fbf" {s(1.3)}/>'
        f'<path d="M{f(cx - 7)} {f(base - 11)}H{f(cx + 7)}" stroke="#f3d27a" stroke-width="1.8"/>'
        f'<circle cx="{f(cx)}" cy="{f(base - 15)}" r="1.4" fill="#f3d27a"/>'
    )


def _vase(cx, base):
    return (
        f'<path d="M{f(cx - 3)} {f(base - 22)}H{f(cx + 3)}L{f(cx + 2)} {f(base - 18)}Q{f(cx + 10)} {f(base - 12)} {f(cx + 6)} {f(base - 3)}'
        f'L{f(cx + 4)} {f(base)}H{f(cx - 4)}L{f(cx - 6)} {f(base - 3)}Q{f(cx - 10)} {f(base - 12)} {f(cx - 2)} {f(base - 18)}Z" '
        f'fill="#f4f1e8" {s(1.3)}/>'
        f'<path d="M{f(cx - 6)} {f(base - 10)}q3 -3 6 0t6 0" stroke="#2f5aa8" stroke-width="1.6" fill="none"/>'
    )


def display_case(w, h):
    x0, x1 = 8, w - 8
    top_y, base_top = 4, h - 36
    front_y = base_top - 24
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 9)]
    o.append(
        legs(((x0 + 8, base_top + 20), (x1 - 8, base_top + 20)), h - 8, 5, "#3b2418")
    )
    o.append(
        f'<rect x="{f(x0)}" y="{f(base_top)}" width="{f(x1 - x0)}" height="22" rx="3" fill="{grad("walnut")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 6)} {f(base_top + 11)}H{f(x1 - 6)}" stroke="#b07a52" stroke-width="1.4"/>'
    )
    o.append(
        f'<rect x="{f(x0 + 2)}" y="{f(top_y)}" width="{f(x1 - x0 - 4)}" height="{f(base_top - top_y)}" fill="#7a1f2e"/>'
        f'<rect x="{f(x0 + 2)}" y="{f(front_y)}" width="{f(x1 - x0 - 4)}" height="{f(base_top - front_y)}" fill="#5e1622"/>'
    )
    artifacts = (_crown, _egg, _vase)
    if h > w * 1.15:
        n = max(1, int((front_y - top_y) // 52))
        spots = [(w / 2, top_y + (front_y - top_y) * (i + 0.75) / n) for i in range(n)]
    else:
        n = max(1, int((x1 - x0) // 62))
        spots = [(x0 + (x1 - x0) * (i + 0.5) / n, front_y - 2) for i in range(n)]
    for i, (ax, ay) in enumerate(spots):
        o.append(
            f'<ellipse cx="{f(ax)}" cy="{f(ay)}" rx="17" ry="5" fill="#3d0d16" fill-opacity=".55"/>'
        )
        o.append(
            f'<g transform="translate({f(ax)} {f(ay)}) scale(1.45) translate({f(-ax)} {f(-ay)})">'
            f"{artifacts[i % 3](ax, ay)}</g>"
        )
    o.append(
        f'<rect x="{f(x0)}" y="{f(top_y)}" width="{f(x1 - x0)}" height="{f(front_y - top_y)}" fill="#d6f1f6" fill-opacity=".14" {s(1.8)}/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="{f(front_y)}" width="{f(x1 - x0)}" height="{f(base_top - front_y)}" fill="#d6f1f6" fill-opacity=".22" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 3)} {f(top_y + 3)}V{f(base_top - 3)}M{f(x0 + 3)} {f(front_y + 2)}H{f(x1 - 3)}" stroke="#ffffff" stroke-opacity=".6" stroke-width="1.6"/>'
    )
    glare = "".join(
        f"M{f(x0 + 10 + i)} {f(base_top - 3)}l12 -18"
        for i in range(0, int(x1 - x0 - 30), 46)
    )
    o.append(
        f'<path d="{glare}" stroke="#ffffff" stroke-opacity=".75" stroke-width="2.4" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(x0)} {f(top_y)}H{f(x1)}" stroke="{grad("brass")}" stroke-width="3"/>'
    )
    return "".join(o)


def gramophone(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 32, 8)]
    o.append(
        k.block(
            cx - 28,
            cx + 20,
            44,
            56,
            84,
            lid=grad("walnut-top"),
            face=grad("walnut"),
            side="#4a2c1d",
        )
    )
    o.append(
        f'<rect x="{f(cx - 20)}" y="62" width="32" height="14" rx="2" fill="none" stroke="#b07a52" stroke-width="1.4"/>'
    )
    o.append(
        f'<path d="M{f(cx + 21)} 66q5 -2 6 4" stroke="{INK}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
    )
    o.append(
        f'<ellipse cx="{f(cx - 2)}" cy="50" rx="20" ry="5" fill="#1d1a1a" {s(1.4)}/>'
        f'<ellipse cx="{f(cx - 2)}" cy="50" rx="6" ry="1.8" fill="#c43c3c"/>'
    )
    o.append(
        k.outlined(f"M{f(cx + 16)} 49Q{f(cx + 14)} 38 {f(cx + 6)} 32", "#d8b264", 4.4)
    )
    o.append(k.outlined(f"M{f(cx + 6)} 32Q{f(cx)} 22 {f(cx - 6)} 14", "#d8b264", 6))
    o.append(
        f'<g transform="rotate(-28 {f(cx - 14)} 2)">'
        f'<ellipse cx="{f(cx - 14)}" cy="2" rx="26" ry="20" fill="{grad("gold")}" {s()}/>'
        f'<ellipse cx="{f(cx - 12)}" cy="4" rx="17" ry="12" fill="#8a5a22" {s(1.4)}/>'
        f'<ellipse cx="{f(cx - 10)}" cy="6" rx="7" ry="5" fill="#3b2418"/>'
        + "".join(
            f'<path d="M{f(cx - 14 + 26 * math.cos(math.radians(a)))} {f(2 + 20 * math.sin(math.radians(a)))}'
            f'L{f(cx - 12 + 17 * math.cos(math.radians(a)))} {f(4 + 12 * math.sin(math.radians(a)))}" stroke="#9a6b1e" stroke-width="1.2"/>'
            for a in range(0, 360, 45)
        )
        + "</g>"
    )
    return "".join(o)


def specimen_cabinet(w, h):
    if h > w * 1.15:
        return "".join(
            f'<g transform="translate(0 {i * 100})">{specimen_cabinet(w, 100)}</g>'
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
    inner_top, inner_bottom = top + 8, bottom - 12
    rows = [inner_top + (inner_bottom - inner_top) * i / 3 for i in range(4)]
    # jars
    y0, y1 = rows[0], rows[1]
    o.append(
        f'<rect x="{f(x0 + 6)}" y="{f(y0)}" width="{f(x1 - x0 - 12)}" height="{f(y1 - y0 - 2)}" fill="#2b2420"/>'
    )
    colours = ("#9fd3a6", "#f2c45a", "#a8c8e8", "#e79a8c")
    jx, i = x0 + 10, 0
    while jx < x1 - 16:
        jh = (y1 - y0) * (0.62 + 0.1 * (i % 2))
        o.append(
            f'<rect x="{f(jx)}" y="{f(y1 - 3 - jh)}" width="11" height="{f(jh)}" rx="3" fill="{colours[i % 4]}" fill-opacity=".85" stroke="#1d1814" stroke-width="1"/>'
            f'<rect x="{f(jx - 0.5)}" y="{f(y1 - 5 - jh)}" width="12" height="3.4" rx="1" fill="#d8b264" stroke="#1d1814" stroke-width=".8"/>'
            f'<circle cx="{f(jx + 5.5)}" cy="{f(y1 - 3 - jh * 0.45)}" r="2.2" fill="#6b4b2a" fill-opacity=".7"/>'
        )
        jx += 15
        i += 1
    # butterfly board
    y0, y1 = rows[1], rows[2]
    o.append(
        f'<rect x="{f(x0 + 6)}" y="{f(y0)}" width="{f(x1 - x0 - 12)}" height="{f(y1 - y0 - 2)}" fill="#f3ead2" stroke="#1d1814" stroke-width="1"/>'
    )
    bx, i = x0 + 18, 0
    wing = ("#e07a3a", "#3f8fbf", "#c43c7a", "#f2c45a")
    while bx < x1 - 12:
        by = (y0 + y1) / 2 - 1
        c = wing[i % 4]
        o.append(
            f'<path d="M{f(bx)} {f(by)}l-6 -5q-3 4 0 6l6 -1l6 1q3 -2 0 -6Z" fill="{c}" stroke="#1d1814" stroke-width=".8"/>'
            f'<path d="M{f(bx)} {f(by)}l-4 4q2 2 4 -1q2 3 4 1Z" fill="{c}" stroke="#1d1814" stroke-width=".8"/>'
            f'<path d="M{f(bx)} {f(by - 4)}v8" stroke="#1d1814" stroke-width="1.2"/>'
        )
        bx += 20
        i += 1
    # drawers
    y0, y1 = rows[2], rows[3]
    cols = max(2, int((x1 - x0 - 12) // 22))
    dw = (x1 - x0 - 12) / cols
    for c in range(cols):
        dx = x0 + 6 + c * dw
        o.append(
            f'<rect x="{f(dx + 1)}" y="{f(y0 + 1)}" width="{f(dw - 2)}" height="{f(y1 - y0 - 3)}" rx="1.5" fill="#6a4128" stroke="#2a1a12" stroke-width="1"/>'
            f'<rect x="{f(dx + dw / 2 - 4)}" y="{f(y0 + 4)}" width="8" height="5" fill="#f3ead2" stroke="#d8b264" stroke-width="1"/>'
        )
    o.append(
        f'<rect x="{f(x0 + 2)}" y="{f(bottom - 10)}" width="{f(x1 - x0 - 4)}" height="9" rx="2" fill="#5a3826" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 8)} {inner_top + 2}l10 18M{f(x1 - 24)} {inner_top + 2}l8 14" stroke="#ffffff" stroke-opacity=".35" stroke-width="2.2" stroke-linecap="round"/>'
    )
    return "".join(o)


def classical_statue(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 30, 8)]
    o.append(
        k.block(
            cx - 22,
            cx + 16,
            56,
            64,
            86,
            lid="#f1ede4",
            face=grad("marble"),
            side="#bdb5a5",
        )
    )
    o.append(
        f'<path d="M{f(cx - 11)} 16Q{f(cx - 20)} 40 {f(cx - 18)} 60H{f(cx + 14)}Q{f(cx + 14)} 38 {f(cx + 9)} 16Z" fill="{grad("marble")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 8)} 22Q{f(cx - 12)} 40 {f(cx - 11)} 58M{f(cx - 1)} 24Q{f(cx - 2)} 42 {f(cx - 3)} 58M{f(cx + 6)} 22Q{f(cx + 8)} 40 {f(cx + 6)} 58" '
        f'fill="none" stroke="#b5ad9c" stroke-width="1.4"/>'
    )
    o.append(
        f'<path d="M{f(cx - 10)} 18Q{f(cx - 12)} -4 {f(cx - 2)} -8H{f(cx + 4)}Q{f(cx + 12)} -4 {f(cx + 10)} 18Z" fill="{grad("marble")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 10)} -2Q{f(cx - 22)} 10 {f(cx - 14)} 24" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
        f'<path d="M{f(cx - 10)} -2Q{f(cx - 22)} 10 {f(cx - 14)} 24" fill="none" stroke="#efe9dd" stroke-width="4" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx + 9)} -2Q{f(cx + 16)} -14 {f(cx + 6)} -20" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
        f'<path d="M{f(cx + 9)} -2Q{f(cx + 16)} -14 {f(cx + 6)} -20" fill="none" stroke="#efe9dd" stroke-width="4" stroke-linecap="round"/>'
    )
    o.append(
        f'<rect x="{f(cx - 3)}" y="-14" width="6" height="7" fill="#efe9dd" {s(1.4)}/>'
        f'<circle cx="{f(cx)}" cy="-20" r="8" fill="#f4f1ea" {s()}/>'
        f'<path d="M{f(cx - 8)} -22Q{f(cx - 6)} -31 {f(cx + 1)} -29Q{f(cx + 8)} -29 {f(cx + 8)} -22" fill="#e6e0d3" {s(1.4)}/>'
    )
    o.append(k.highlight(f"M{f(cx - 6)} 2Q{f(cx - 7)} 10 {f(cx - 5)} 14", 0.7, 2))
    return "".join(o)


def dino_skull(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 30, 7)]
    o.append(
        k.block(
            cx - 24,
            cx + 18,
            70,
            75,
            86,
            lid="#3a3a3f",
            face="#26262b",
            side="#18181c",
            depth=6,
        )
    )
    o.append(
        f'<rect x="{f(cx - 8)}" y="77" width="14" height="6" rx="1" fill="{grad("brass")}" stroke="{INK}" stroke-width=".8"/>'
    )
    o.append(
        f'<path d="M{f(cx + 2)} 72V48" stroke="{INK}" stroke-width="5"/><path d="M{f(cx + 2)} 72V48" stroke="#6b6b70" stroke-width="2.4"/>'
    )
    skull = (
        f"M{f(cx - 38)} 38Q{f(cx - 32)} 28 {f(cx - 14)} 24Q{f(cx - 2)} 12 {f(cx + 16)} 12Q{f(cx + 36)} 14 {f(cx + 36)} 28"
        f"L{f(cx + 30)} 42Q{f(cx + 12)} 50 {f(cx - 30)} 48Q{f(cx - 40)} 46 {f(cx - 38)} 38Z"
    )
    o.append(f'<path d="{skull}" fill="#efe4c8" {s()}/>')
    o.append(
        f'<path d="M{f(cx - 36)} 41L{f(cx + 28)} 38" stroke="{INK}" stroke-width="1.8"/>'
    )
    teeth = "".join(
        f"M{f(x)} 40l2.4 5 2.4 -5.4" for x in range(int(cx - 33), int(cx + 8), 6)
    )
    o.append(
        f'<path d="{teeth}" fill="#fffaf0" stroke="{INK}" stroke-width="1.1" stroke-linejoin="round"/>'
    )
    o.append(
        f'<ellipse cx="{f(cx + 6)}" cy="25" rx="5.4" ry="4.4" fill="#3b2a1e" {s(1.2)}/>'
        f'<ellipse cx="{f(cx + 22)}" cy="29" rx="7" ry="6" fill="#3b2a1e" {s(1.2)}/>'
        f'<ellipse cx="{f(cx - 27)}" cy="32" rx="3.6" ry="2.4" fill="#3b2a1e"/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} 26Q{f(cx - 10)} 18 {f(cx)} 17" fill="none" stroke="#ffffff" stroke-opacity=".7" stroke-width="2" stroke-linecap="round"/>'
    )
    return "".join(o)


def amphora(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 26, 7)]
    o.append(f'<ellipse cx="{f(cx)}" cy="82" rx="14" ry="5" fill="#3b2418" {s(1.6)}/>')
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx + side * 7)} 13Q{f(cx + side * 26)} 6 {f(cx + side * 24)} 28",
                "#c97b4a",
                4.4,
            )
        )
    body = (
        f"M{f(cx - 8)} 5H{f(cx + 8)}L{f(cx + 7)} 14Q{f(cx + 30)} 22 {f(cx + 28)} 44"
        f"Q{f(cx + 25)} 68 {f(cx + 7)} 80H{f(cx - 7)}Q{f(cx - 25)} 68 {f(cx - 28)} 44"
        f"Q{f(cx - 30)} 22 {f(cx - 7)} 14Z"
    )
    o.append(f'<path d="{body}" fill="{grad("terra")}" {s()}/>')
    o.append(
        f'<path d="M{f(cx - 28.6)} 34Q{f(cx)} 38 {f(cx + 28.6)} 34L{f(cx + 27.4)} 52Q{f(cx)} 56 {f(cx - 27.4)} 52Z" fill="#2b1b14"/>'
    )
    meander = "".join(
        f"M{f(x)} 46v-6h5v4h-3" for x in range(int(cx - 22), int(cx + 18), 8)
    )
    o.append(f'<path d="{meander}" fill="none" stroke="#e9b58a" stroke-width="1.3"/>')
    o.append(f'<path d="{body}" fill="none" {s()}/>')
    o.append(f'<ellipse cx="{f(cx)}" cy="5" rx="11" ry="3.6" fill="#a8582f" {s(1.6)}/>')
    o.append(
        k.highlight(f"M{f(cx - 18)} 26Q{f(cx - 23)} 40 {f(cx - 20)} 60", 0.45, 2.6)
    )
    return "".join(o)


def meteorite(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 34, 8)]
    o.append(
        k.block(
            cx - 30,
            cx + 22,
            68,
            74,
            86,
            lid=grad("walnut-top"),
            face=grad("walnut"),
            side="#4a2c1d",
        )
    )
    o.append(
        f'<rect x="{f(cx - 10)}" y="77" width="18" height="6" rx="1" fill="{grad("brass")}" stroke="{INK}" stroke-width=".8"/>'
    )
    rock = (
        f"M{f(cx - 30)} 70Q{f(cx - 38)} 50 {f(cx - 20)} 38Q{f(cx - 8)} 26 {f(cx + 8)} 30"
        f"Q{f(cx + 30)} 28 {f(cx + 32)} 50Q{f(cx + 36)} 66 {f(cx + 24)} 70Z"
    )
    o.append(f'<path d="{rock}" fill="{grad("meteor")}" {s()}/>')
    for x, y, rx, ry in (
        (-14, 46, 6, 4),
        (6, 40, 5, 3.4),
        (16, 56, 6, 4),
        (-4, 60, 4.4, 3),
    ):
        o.append(
            f'<ellipse cx="{f(cx + x)}" cy="{y}" rx="{rx}" ry="{ry}" fill="#2a2930" stroke="#7a7984" stroke-width="1"/>'
        )
    for x, y in ((-20, 42), (12, 34), (24, 48)):
        o.append(
            f'<path d="M{f(cx + x)} {y - 4}l1 3 3 1 -3 1 -1 3 -1 -3 -3 -1 3 -1Z" fill="#fff6d8"/>'
        )
    o.append(
        f'<path d="M{f(cx - 22)} 42Q{f(cx - 12)} 32 {f(cx)} 32" fill="none" stroke="#ffffff" stroke-opacity=".35" stroke-width="2.4" stroke-linecap="round"/>'
    )
    return "".join(o)


def _gallery(pid, ground, frame_gold):
    body = (
        f'<rect width="100" height="26" fill="{ground}"/>'
        f'<path d="M0 8H100" stroke="{frame_gold}" stroke-width="1.2"/>'
        f'<path d="M50 8L41 10.5M50 8L59 10.5" stroke="{frame_gold}" stroke-width=".8"/>'
        f'<rect x="39" y="10.5" width="22" height="8" fill="#bcd9e8" stroke="{frame_gold}" stroke-width="1.8"/>'
        '<path d="M40 18.5Q46 13 51 16T60 15V18.5Z" fill="#6fa35d"/>'
        '<circle cx="55" cy="13" r="1.4" fill="#f6e3a1"/>'
    )
    return k.face_pattern(pid, body)


def _gallery_red(pid):
    return _gallery(pid, "#8e2c32", "#e2c27a")


def _portrait_green(pid):
    body = (
        '<rect width="100" height="26" fill="#2f5a4c"/>'
        '<path d="M0 8H100" stroke="#e2c27a" stroke-width="1.2"/>'
        '<ellipse cx="50" cy="14" rx="7" ry="4.6" fill="#8a6a4a" stroke="#e2c27a" stroke-width="1.8"/>'
        '<circle cx="50" cy="13.4" r="1.8" fill="#f0d2ae"/><path d="M47.4 17.6q2.6 -3 5.2 0" fill="#3b2418"/>'
    )
    return k.face_pattern(pid, body)


def _marble_wall(pid):
    body = (
        '<rect width="100" height="26" fill="#ece6da"/>'
        '<path d="M0 10H100" stroke="#c9bfae" stroke-width="1.4"/>'
        '<path d="M6 19Q20 12 34 15M58 18Q70 12 92 14M40 9Q46 12 52 10" stroke="#c4baa8" stroke-width=".9" fill="none"/>'
        '<path d="M0 0V19M50 10V19" stroke="#d7cfbf" stroke-width="1"/>'
    )
    return k.face_pattern(pid, body)


SKINS = {
    "four_poster": four_poster,
    "sarcophagus": sarcophagus,
    "throne": throne,
    "carriage": carriage,
    "display_case": display_case,
    "gramophone": gramophone,
    "specimen_cabinet": specimen_cabinet,
    "classical_statue": classical_statue,
    "dino_skull": dino_skull,
    "amphora": amphora,
    "meteorite": meteorite,
}
WALLPAPERS = {
    "gallery_red": _gallery_red,
    "portrait_green": _portrait_green,
    "marble_wall": _marble_wall,
}
STRETCH = {"four_poster", "sarcophagus", "carriage", "display_case", "specimen_cabinet"}
TALL = {"four_poster", "throne", "gramophone", "specimen_cabinet", "classical_statue"}
