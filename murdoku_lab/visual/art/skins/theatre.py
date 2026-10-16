"""Backstage at the Rosalind Theatre: costume rails, spotlights, scenery flats and a prop coffin."""

from . import _kit as k
from ._kit import INK, f, grad, legs, s, shadow

GRADIENTS = {
    "pumpkin": ("#f7a650", "#d9701f"),
    "burlap": ("#d6b37a", "#b48e55"),
    "stage-black": ("#3a3a42", "#202026"),
}


def directors_chair(w, h):
    cx = w / 2
    wood = "#c98d55"
    o = [shadow(cx, h - 12, 32, 8)]
    o.append(k.outlined(f"M{f(cx - 28)} 58L{f(cx + 26)} 86", wood, 4.4))
    o.append(k.outlined(f"M{f(cx + 28)} 58L{f(cx - 26)} 86", wood, 4.4))
    for side in (-1, 1):
        o.append(k.outlined(f"M{f(cx + side * 28)} 0V60", wood, 5, cap="butt"))
    o.append(
        f'<rect x="{f(cx - 31)}" y="4" width="62" height="22" rx="2" fill="#1f1f24" {s()}/>'
    )
    o.append(k.star(cx, 15, 7.5, "#f6e7c1", line=0.8))
    for side in (-1, 1):
        o.append(
            f'<rect x="{f(cx + side * 32 - 4)}" y="30" width="8" height="20" rx="3" fill="{wood}" {s(1.6)}/>'
        )
    o.append(
        f'<path d="M{f(cx - 28)} 46H{f(cx + 28)}V58Q{f(cx)} 64 {f(cx - 28)} 58Z" fill="#2b2b31" {s()}/>'
    )
    o.append(k.highlight(f"M{f(cx - 20)} 50H{f(cx + 20)}", 0.25, 2))
    return "".join(o)


def vanity(w, h):
    x0, x1 = 8, w - 8
    mx0, mx1 = x0 + 8, x1 - 8
    top_y, front = 18, h - 34
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 9)]
    o.append(
        f'<rect x="{f(mx0)}" y="-28" width="{f(mx1 - mx0)}" height="50" rx="4" fill="#2a2228" {s()}/>'
    )
    o.append(
        f'<rect x="{f(mx0 + 7)}" y="-21" width="{f(mx1 - mx0 - 14)}" height="36" rx="2" fill="#cfe3ea" {s(1.4)}/>'
    )
    o.append(
        f'<path d="M{f(mx0 + 12)} 10l14 -26M{f(mx0 + 22)} 12l12 -22" stroke="#ffffff" stroke-opacity=".7" stroke-width="2.4" stroke-linecap="round"/>'
    )
    n = max(3, int((mx1 - mx0) // 13))
    for i in range(n):
        o.append(k.bulb(mx0 + 4 + i * (mx1 - mx0 - 8) / (n - 1), -24.5, 2.8))
    for yy in (-12, 0, 12):
        o.append(k.bulb(mx0 + 3.5, yy, 2.8))
        o.append(k.bulb(mx1 - 3.5, yy, 2.8))
    o.append(legs(((x0 + 6, front + 10), (x1 - 6, front + 10)), h - 8, 5, "#5a3826"))
    o.append(
        f'<rect x="{f(x0)}" y="{top_y}" width="{f(x1 - x0)}" height="{f(front - top_y)}" rx="4" fill="#f1e2c8" {s()}/>'
    )
    o.append(
        f'<rect x="{f(x0)}" y="{f(front)}" width="{f(x1 - x0)}" height="12" rx="3" fill="#d6bc94" {s()}/>'
    )
    for i in range(max(1, int((x1 - x0) // 40))):
        px = x0 + (x1 - x0) * (i + 0.5) / max(1, int((x1 - x0) // 40))
        o.append(
            f'<circle cx="{f(px)}" cy="{f(front + 6)}" r="2" fill="{grad("brass")}" {s(.8)}/>'
        )
    span = x1 - x0
    cols = max(1, int(span // 60))
    rows = max(1, int((front - top_y) // 52))
    spots = [
        (x0 + i * 60, top_y + (front - top_y) * (j + 0.5) / rows)
        for i in range(cols)
        for j in range(rows)
    ]
    for bx, by in spots:
        o.append(
            f'<circle cx="{f(bx + 16)}" cy="{f(by)}" r="7" fill="#f3b8c6" {s(1.4)}/>'
            f'<circle cx="{f(bx + 14)}" cy="{f(by - 2)}" r="2.4" fill="#ffffff" fill-opacity=".8"/>'
        )
        o.append(
            f'<rect x="{f(bx + 28)}" y="{f(by - 4)}" width="5" height="11" rx="1.5" fill="#d9473a" {s(1.1)} '
            f'transform="rotate(30 {f(bx + 30)} {f(by)})"/>'
        )
        o.append(
            f'<rect x="{f(bx + 40)}" y="{f(by - 6)}" width="9" height="11" rx="2" fill="#7fa7c9" {s(1.2)}/>'
            f'<path d="M{f(bx + 42)} {f(by - 6)}l-2 -9M{f(bx + 45)} {f(by - 6)}v-11M{f(bx + 48)} {f(by - 6)}l2 -8" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
        )
    return "".join(o)


def spotlight(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 30, 7)]
    for fx, fy in ((cx - 26, 86), (cx + 26, 86), (cx + 4, 80)):
        o.append(k.outlined(f"M{f(cx)} 54L{f(fx)} {fy}", "#4a5056", 3.4))
    o.append(k.outlined(f"M{f(cx)} 56V26", "#5a6066", 4.4))
    o.append(
        k.outlined(f"M{f(cx - 21)} 6V26H{f(cx + 21)}V6", "#5a6066", 3.4, cap="butt")
    )
    o.append(
        f'<ellipse cx="{f(cx - 34)}" cy="-2" rx="12" ry="16" fill="#ffe9a8" fill-opacity=".35"/>'
    )
    o.append(f'<g transform="rotate(-18 {f(cx)} 8)">')
    o.append(
        f'<rect x="{f(cx - 22)}" y="-6" width="40" height="26" rx="5" fill="{grad("stage-black")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 12)} -6v-5M{f(cx - 4)} -6v-5M{f(cx + 4)} -6v-5M{f(cx + 12)} -6v-5" stroke="{INK}" stroke-width="2.4"/>'
    )
    o.append(
        f'<rect x="{f(cx - 30)}" y="-10" width="10" height="34" rx="3" fill="#2b2f33" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 30)} -10L{f(cx - 42)} -17V-12L{f(cx - 30)} -5ZM{f(cx - 30)} 24L{f(cx - 42)} 31V26L{f(cx - 30)} 19Z" fill="#3a3f44" {s(1.4)}/>'
    )
    o.append(
        f'<ellipse cx="{f(cx - 27)}" cy="7" rx="4.5" ry="12" fill="#fff3c8" stroke="#7a5a1c" stroke-width="1.2"/>'
    )
    o.append(k.highlight(f"M{f(cx - 16)} -1H{f(cx + 12)}", 0.3, 2))
    o.append("</g>")
    return "".join(o)


def _garment(gx, rail, shape, colour):
    hook = (
        f'<path d="M{f(gx)} {f(rail)}q3 1 2 3.5q-1 2 -2 1.5" fill="none" stroke="{INK}" stroke-width="1.4"/>'
        f'<path d="M{f(gx - 9)} {f(rail + 11)}L{f(gx)} {f(rail + 5)}L{f(gx + 9)} {f(rail + 11)}" fill="none" stroke="{INK}" stroke-width="1.6"/>'
    )
    if shape == "dress":
        body = (
            f'<path d="M{f(gx - 8)} {f(rail + 10)}H{f(gx + 8)}L{f(gx + 6)} {f(rail + 26)}L{f(gx + 16)} {f(rail + 70)}'
            f'Q{f(gx)} {f(rail + 75)} {f(gx - 16)} {f(rail + 70)}L{f(gx - 6)} {f(rail + 26)}Z" fill="{colour}" {s(1.8)}/>'
            f'<path d="M{f(gx - 6)} {f(rail + 26)}H{f(gx + 6)}" stroke="#f6e7c1" stroke-width="2.4"/>'
            f'<path d="M{f(gx - 10)} {f(rail + 50)}q4 6 0 16M{f(gx + 6)} {f(rail + 48)}q3 8 1 18" fill="none" stroke="#1b130e" stroke-opacity=".25" stroke-width="1.6"/>'
        )
    elif shape == "coat":
        body = (
            f'<rect x="{f(gx - 11)}" y="{f(rail + 10)}" width="22" height="52" rx="4" fill="{colour}" {s(1.8)}/>'
            f'<path d="M{f(gx - 6)} {f(rail + 10)}L{f(gx)} {f(rail + 24)}L{f(gx + 6)} {f(rail + 10)}" fill="#f6e7c1" {s(1.2)}/>'
            f'<path d="M{f(gx)} {f(rail + 24)}V{f(rail + 60)}" stroke="#1b130e" stroke-opacity=".35" stroke-width="1.2"/>'
            + "".join(
                f'<circle cx="{f(gx + 3)}" cy="{f(rail + yy)}" r="1.6" fill="#e2c27a"/>'
                for yy in (30, 38, 46)
            )
        )
    else:
        body = (
            f'<path d="M{f(gx - 7)} {f(rail + 9)}H{f(gx + 7)}L{f(gx + 18)} {f(rail + 60)}H{f(gx - 18)}Z" fill="{colour}" {s(1.8)}/>'
            f'<path d="M{f(gx - 9)} {f(rail + 9)}Q{f(gx)} {f(rail + 18)} {f(gx + 9)} {f(rail + 9)}" fill="#e2c27a" {s(1.4)}/>'
            f'<path d="M{f(gx - 18)} {f(rail + 58)}H{f(gx + 18)}" stroke="#e2c27a" stroke-width="2.4"/>'
        )
    return body + hook


def costume_rack(w, h):
    if h > w * 1.15:
        return "".join(
            f'<g transform="translate(0 {i * 100})">{costume_rack(w, 100)}</g>'
            for i in range(int(round(h / 100)))
        )
    x0, x1 = 10, w - 10
    rail = -8
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 8)]
    for px in (x0 + 2, x1 - 2):
        o.append(k.outlined(f"M{f(px)} {rail}V82", "#5a6066", 3.4, cap="butt"))
        o.append(k.outlined(f"M{f(px - 9)} 82H{f(px + 9)}", "#5a6066", 3.4))
        o.append(
            f'<circle cx="{f(px - 8)}" cy="86" r="3" fill="#222222"/><circle cx="{f(px + 8)}" cy="86" r="3" fill="#222222"/>'
        )
    colours = ("#c43c4c", "#e2b44c", "#6b4c9a", "#2f8f83", "#3f6fb0", "#e07a5f")
    shapes = ("dress", "coat", "cape")
    n = max(2, int((x1 - x0 - 10) // 20))
    spacing = (x1 - x0 - 16) / n
    for i in range(n):
        gx = x0 + 8 + spacing * (i + 0.5)
        o.append(_garment(gx, rail, shapes[i % 3], colours[(i * 2 + 1) % len(colours)]))
    o.append(k.outlined(f"M{f(x0 - 2)} {rail}H{f(x1 + 2)}", "#9aa1a8", 3.2))
    return "".join(o)


def flat_tree(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 32, 7)]
    o.append(k.outlined(f"M{f(cx + 6)} 4L{f(cx + 34)} 82", "#c9a46a", 4))
    o.append(
        f'<rect x="{f(cx + 26)}" y="76" width="18" height="11" rx="5" fill="{grad("burlap")}" {s(1.6)}/>'
    )
    canopy = (
        f"M{f(cx - 30)} 40Q{f(cx - 44)} 28 {f(cx - 32)} 14Q{f(cx - 36)} -6 {f(cx - 16)} -10Q{f(cx - 6)} -26 {f(cx + 10)} -18"
        f"Q{f(cx + 30)} -22 {f(cx + 32)} -2Q{f(cx + 44)} 10 {f(cx + 34)} 26Q{f(cx + 40)} 44 {f(cx + 20)} 46"
        f"Q{f(cx + 4)} 54 {f(cx - 12)} 48Q{f(cx - 26)} 52 {f(cx - 30)} 40Z"
    )
    trunk = f"M{f(cx - 7)} 44L{f(cx - 9)} 82H{f(cx + 9)}L{f(cx + 7)} 44Z"
    o.append(
        f'<g transform="translate(3 2)"><path d="{trunk}" fill="#e3c79a" {s(1.6)}/><path d="{canopy}" fill="#e3c79a" {s(1.6)}/></g>'
    )
    o.append(f'<path d="{trunk}" fill="#9a6a3f" {s()}/>')
    o.append(
        f'<path d="M{f(cx - 3)} 52v12M{f(cx + 3)} 60v14" stroke="#6b4527" stroke-width="1.6" stroke-linecap="round"/>'
    )
    o.append(f'<path d="{canopy}" fill="#6fae5a" {s()}/>')
    o.append(
        f'<path d="M{f(cx - 22)} 32Q{f(cx - 8)} 40 {f(cx + 8)} 34M{f(cx + 4)} 10Q{f(cx + 16)} 16 {f(cx + 24)} 8M{f(cx - 24)} 6Q{f(cx - 14)} 12 {f(cx - 6)} 4" '
        f'fill="none" stroke="#4f8a45" stroke-width="3" stroke-linecap="round"/>'
    )
    for x, y in ((-14, -6), (10, -12), (-24, 20), (18, 24), (0, 18)):
        o.append(
            f'<ellipse cx="{f(cx + x)}" cy="{y}" rx="5" ry="3" fill="#a6d38c" transform="rotate(-20 {f(cx + x)} {y})"/>'
        )
    o.append(
        f'<rect x="{f(cx - 14)}" y="80" width="28" height="7" rx="2" fill="#26262b" {s(1.4)}/>'
    )
    return "".join(o)


def _mask(cx, cy, colour, smile):
    mouth = (
        f"M{f(cx - 4)} {f(cy + 3)}q4 4 8 0"
        if smile
        else f"M{f(cx - 4)} {f(cy + 5)}q4 -4 8 0"
    )
    brows = (
        f"M{f(cx - 6)} {f(cy - 5)}q2 -2 4 0M{f(cx + 2)} {f(cy - 5)}q2 -2 4 0"
        if smile
        else f"M{f(cx - 6)} {f(cy - 6)}q2 2 4 0M{f(cx + 2)} {f(cy - 6)}q2 2 4 0"
    )
    return (
        f'<path d="M{f(cx - 9)} {f(cy - 7)}Q{f(cx)} {f(cy - 11)} {f(cx + 9)} {f(cy - 7)}Q{f(cx + 10)} {f(cy + 6)} {f(cx)} {f(cy + 10)}'
        f'Q{f(cx - 10)} {f(cy + 6)} {f(cx - 9)} {f(cy - 7)}Z" fill="{colour}" {s(1.4)}/>'
        f'<ellipse cx="{f(cx - 4)}" cy="{f(cy - 2)}" rx="2.2" ry="1.6" fill="{INK}"/>'
        f'<ellipse cx="{f(cx + 4)}" cy="{f(cy - 2)}" rx="2.2" ry="1.6" fill="{INK}"/>'
        f'<path d="{mouth}{brows}" fill="none" stroke="{INK}" stroke-width="1.3" stroke-linecap="round"/>'
    )


def prop_trunk(w, h):
    x0, x1 = 12, w - 22
    top, front, bottom = 32, 46, h - 12
    o = [shadow((x0 + x1) / 2 + 4, bottom + 2, 38, 8)]
    o.append(
        k.block(
            x0,
            x1,
            top,
            front,
            bottom,
            lid="#4a4a53",
            face=grad("stage-black"),
            side="#1c1c21",
        )
    )
    o.append(
        f'<path d="M{f(x0 + 1)} {front + 5}H{f(x1 - 1)}M{f(x0 + 1)} {bottom - 5}H{f(x1 - 1)}" stroke="#d8b264" stroke-width="2.4"/>'
    )
    for cx_, cy_ in (
        (x0 + 3, front + 3),
        (x1 - 3, front + 3),
        (x0 + 3, bottom - 3),
        (x1 - 3, bottom - 3),
    ):
        o.append(
            f'<rect x="{f(cx_ - 3)}" y="{f(cy_ - 3)}" width="6" height="6" rx="1" fill="{grad("brass")}" {s(.9)}/>'
        )
    o.append(
        f'<text x="{f((x0 + x1) / 2)}" y="{front + 22}" font-size="10" font-family="DM Mono" font-weight="500" '
        f'text-anchor="middle" fill="#f6efe0" fill-opacity=".85" letter-spacing="1.5">PROPS</text>'
    )
    o.append(_mask(x0 + 22, top + 4, "#f3d27a", True))
    o.append(_mask(x0 + 42, top + 7, "#d5dbe0", False))
    return "".join(o)


def wig_stand(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 22, 6)]
    o.append(
        f'<ellipse cx="{f(cx)}" cy="82" rx="18" ry="5.5" fill="{grad("walnut")}" {s(1.8)}/>'
    )
    o.append(k.outlined(f"M{f(cx)} 81V52", "#7a4d33", 4, cap="butt"))
    o.append(
        f'<path d="M{f(cx - 7)} 46Q{f(cx)} 52 {f(cx + 7)} 46V56H{f(cx - 7)}Z" fill="#e6d6c6" {s(1.4)}/>'
    )
    back = [
        (cx - 15, 14, 8.5),
        (cx + 15, 14, 8.5),
        (cx - 20, 27, 7.5),
        (cx + 20, 27, 7.5),
        (cx - 19, 40, 7),
        (cx + 19, 40, 7),
        (cx - 15, 52, 6.4),
        (cx + 15, 52, 6.4),
    ]
    front_curls = [(cx - 6, 6, 8.5), (cx + 6, 6, 8.5), (cx, 0, 7.5)]

    def curl(x, y, r):
        return (
            f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="#f8f4ec" {s(1.5)}/>'
            f'<path d="M{f(x - r * 0.4)} {f(y)}a{f(r * 0.4)} {f(r * 0.4)} 0 1 1 {f(r * 0.4)} {f(r * 0.4)}" fill="none" stroke="#cfc4b2" stroke-width="1.3"/>'
        )

    o.append("".join(curl(*c) for c in back))
    o.append(
        f'<ellipse cx="{f(cx)}" cy="34" rx="11" ry="14" fill="#f1e4d8" {s()}/>'
        f'<path d="M{f(cx - 6)} 32q2 1.4 4 0M{f(cx + 2)} 32q2 1.4 4 0M{f(cx - 2)} 41q2 1 4 0" fill="none" stroke="#b8a898" stroke-width="1.2" stroke-linecap="round"/>'
    )
    o.append("".join(curl(*c) for c in front_curls))
    o.append(
        f'<path d="M{f(cx + 12)} 58l-7 -5v10ZM{f(cx + 12)} 58l7 -5v10Z" fill="#1f1f24" {s(1)}/>'
    )
    return "".join(o)


def _sack(x, y, rot=0):
    return (
        f'<g transform="rotate({rot} {f(x)} {f(y)})">'
        f'<path d="M{f(x - 19)} {f(y - 8)}Q{f(x)} {f(y - 14)} {f(x + 17)} {f(y - 8)}Q{f(x + 23)} {f(y)} {f(x + 17)} {f(y + 8)}'
        f'Q{f(x)} {f(y + 14)} {f(x - 19)} {f(y + 8)}Q{f(x - 24)} {f(y)} {f(x - 19)} {f(y - 8)}Z" fill="{grad("burlap")}" {s()}/>'
        f'<path d="M{f(x - 15)} {f(y - 5)}Q{f(x)} {f(y - 9)} {f(x + 13)} {f(y - 5)}" fill="none" stroke="#8a6a3c" stroke-width="1.2" stroke-dasharray="2 2"/>'
        f'<path d="M{f(x + 17)} {f(y - 5)}l7 -3v16l-7 -3Z" fill="#c9a46a" {s(1.4)}/>'
        f'<path d="M{f(x - 6)} {f(y - 1)}h10" stroke="#b5432f" stroke-width="2.6"/></g>'
    )


def sandbag(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 34, 8)]
    o.append(
        k.outlined(f"M{f(cx + 2)} 38Q{f(cx + 6)} 0 {f(cx + 8)} -34", "#d9c08a", 2.6)
    )
    o.append(_sack(cx - 15, 70, -3))
    o.append(_sack(cx + 15, 72, 4))
    o.append(_sack(cx, 52, -2))
    o.append(
        f'<circle cx="{f(cx + 2)}" cy="42" r="3.4" fill="none" stroke="{INK}" stroke-width="2.6"/>'
        f'<circle cx="{f(cx + 2)}" cy="42" r="3.4" fill="none" stroke="#9aa1a8" stroke-width="1.2"/>'
    )
    return "".join(o)


def pumpkin_coach(w, h):
    if h > w * 1.15 or w < 150:
        if h > 100:
            return (
                f'<g transform="translate(0 {f(h - 100)})">{_pumpkin_front(w, 100)}</g>'
            )
        return _pumpkin_front(w, h)
    x0, x1 = 8, w - 8
    mid = (x0 + x1) / 2
    rx, ry = min(66, (x1 - x0) / 2 - 18), 32
    o = [shadow(mid, h - 12, (x1 - x0) / 2, 9)]
    o.append(
        k.outlined(f"M{f(x0 + 30)} 70Q{f(mid)} 86 {f(x1 - 34)} 64", "#e2b44c", 3.4)
    )
    o.append(
        k.outlined(f"M{f(x0 + 18)} 52Q{f(x0 + 8)} 40 {f(x0 + 18)} 34", "#e2b44c", 3)
    )
    o.append(
        f'<ellipse cx="{f(mid)}" cy="38" rx="{f(rx)}" ry="{ry}" fill="{grad("pumpkin")}" {s()}/>'
    )
    for t in (-0.62, -0.3, 0.3, 0.62):
        o.append(
            f'<path d="M{f(mid + t * rx * 0.55)} {f(38 - ry + 3)}Q{f(mid + t * rx * 1.18)} 38 {f(mid + t * rx * 0.55)} {f(38 + ry - 3)}" '
            f'fill="none" stroke="#c4581c" stroke-width="1.8"/>'
        )
    o.append(
        f'<ellipse cx="{f(mid)}" cy="36" rx="16" ry="14" fill="#fbe7a8" stroke="{INK}" stroke-width="6.4"/>'
        f'<ellipse cx="{f(mid)}" cy="36" rx="16" ry="14" fill="#fbe7a8" stroke="#e2b44c" stroke-width="3.4"/>'
        f'<path d="M{f(mid)} 22v28M{f(mid - 16)} 36h32" stroke="#e2b44c" stroke-width="2"/>'
    )
    o.append(
        k.highlight(
            f"M{f(mid - rx * 0.7)} 22Q{f(mid - rx * 0.4)} 10 {f(mid - rx * 0.1)} 8",
            0.45,
            3,
        )
    )
    o.append(k.outlined(f"M{f(mid)} {f(38 - ry + 2)}q3 -10 -6 -14", "#5d9154", 4))
    o.append(
        f'<path d="M{f(mid - 4)} {f(38 - ry - 6)}q8 -6 12 2q-6 -2 -6 4" fill="none" stroke="#5d9154" stroke-width="2"/>'
    )
    o.append(k.wheel(x0 + 34, 70, 16, tyre="#e2b44c", spoke="#e2b44c", hub="#fff3c8"))
    o.append(k.wheel(x1 - 36, 66, 20, tyre="#e2b44c", spoke="#e2b44c", hub="#fff3c8"))
    return "".join(o)


def _pumpkin_front(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 8)]
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 34)}" cy="64" rx="6" ry="18" fill="none" stroke="{INK}" stroke-width="5"/>'
            f'<ellipse cx="{f(cx + side * 34)}" cy="64" rx="6" ry="18" fill="none" stroke="#e2b44c" stroke-width="2.6"/>'
        )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="44" rx="32" ry="30" fill="{grad("pumpkin")}" {s()}/>'
    )
    for t in (-0.6, -0.25, 0.25, 0.6):
        o.append(
            f'<path d="M{f(cx + t * 18)} 16Q{f(cx + t * 40)} 44 {f(cx + t * 18)} 72" fill="none" stroke="#c4581c" stroke-width="1.8"/>'
        )
    o.append(
        f'<circle cx="{f(cx)}" cy="42" r="11" fill="#fbe7a8" stroke="{INK}" stroke-width="6"/>'
        f'<circle cx="{f(cx)}" cy="42" r="11" fill="#fbe7a8" stroke="#e2b44c" stroke-width="3"/>'
    )
    o.append(k.outlined(f"M{f(cx)} 15q3 -10 -6 -14", "#5d9154", 4))
    return "".join(o)


def stage_coffin(w, h):
    def draw(length, width):
        half = min(26, width / 2)
        sh = length * 0.28
        outline = (
            f"M{f(-half * 0.55)} 0H{f(half * 0.55)}L{f(half)} {f(sh)}L{f(half * 0.62)} {f(length)}"
            f"H{f(-half * 0.62)}L{f(-half)} {f(sh)}Z"
        )
        inset = (
            f"M{f(-half * 0.42)} 6H{f(half * 0.42)}L{f(half * 0.8)} {f(sh)}L{f(half * 0.5)} {f(length - 6)}"
            f"H{f(-half * 0.5)}L{f(-half * 0.8)} {f(sh)}Z"
        )
        bx, by = 0, sh * 0.55
        bat = (
            f"M{f(bx - 8)} {f(by)}Q{f(bx - 6)} {f(by - 4)} {f(bx - 4)} {f(by - 2)}Q{f(bx - 2)} {f(by - 5)} {f(bx)} {f(by - 2)}"
            f"Q{f(bx + 2)} {f(by - 5)} {f(bx + 4)} {f(by - 2)}Q{f(bx + 6)} {f(by - 4)} {f(bx + 8)} {f(by)}"
            f"Q{f(bx + 4)} {f(by + 1)} {f(bx + 2)} {f(by + 3)}Q{f(bx)} {f(by + 1)} {f(bx - 2)} {f(by + 3)}"
            f"Q{f(bx - 4)} {f(by + 1)} {f(bx - 8)} {f(by)}Z"
        )
        details = (
            f'<path d="{inset}" fill="none" stroke="#2a1a12" stroke-opacity=".55" stroke-width="1.6"/>'
            f'<path d="{bat}" fill="#1b130e"/>'
            f'<rect x="-7" y="{f(sh + 10)}" width="14" height="9" rx="1.5" fill="{grad("brass")}" {s(1)}/>'
            + "".join(
                f'<path d="M{f(side * half * 0.86)} {f(sh + dy)}v10" stroke="#d8b264" stroke-width="3" stroke-linecap="round"/>'
                for side in (-1, 1)
                for dy in (8, (length - sh) * 0.6)
            )
            + k.highlight(f"M{f(-half * 0.45)} 4L{f(-half * 0.85)} {f(sh)}", 0.3, 2)
        )
        return outline, details

    return k.lying(w, h, draw, fill=grad("walnut"), band="#2a1a12")


def _curtain(pid):
    folds = "".join(
        f'<rect x="{x + 2}" y="0" width="4" height="19" fill="#c0394d"/>'
        f'<rect x="{x + 9}" y="0" width="2.4" height="19" fill="#6c1424"/>'
        for x in range(0, 100, 12)
    )
    body = (
        '<rect width="100" height="26" fill="#9b2335"/>'
        + folds
        + '<rect y="15.5" width="100" height="3.5" fill="#e2c27a"/>'
        + "".join(
            f'<path d="M{x} 19q2 2.4 4 0" fill="#e2c27a"/>' for x in range(0, 100, 4)
        )
    )
    return k.face_pattern(pid, body)


def _blackbox(pid):
    body = (
        '<rect width="100" height="26" fill="#2b2b31"/>'
        '<path d="M14 11h8M18 7v8M62 15h9v-5" stroke="#e9e4d8" stroke-width="1.6" stroke-opacity=".8"/>'
        '<path d="M80 9q4 3 8 0t8 0" stroke="#f1d98a" stroke-width="1" fill="none" stroke-opacity=".6"/>'
        '<rect x="36" y="9" width="12" height="6" rx="1" fill="#2f7d4f"/>'
        '<path d="M39 12h6" stroke="#e9f4ec" stroke-width="1.2"/>'
    )
    return k.face_pattern(pid, body)


def _posters(pid):
    body = (
        '<rect width="100" height="26" fill="#b5654a"/>'
        '<path d="M0 8.5H100M0 14H100M10 8.5V14M40 8.5V14M70 8.5V14M25 14V19M55 14V19M85 14V19" stroke="#e3c3ad" stroke-width="1"/>'
        '<rect x="33" y="8" width="24" height="11" fill="#f6efe0" stroke="#2a221d" stroke-width=".8" transform="rotate(-3 45 13)"/>'
        '<rect x="33" y="8" width="24" height="3.4" fill="#c43c4c" transform="rotate(-3 45 13)"/>'
        '<path d="M36 14.5h17M37 17h12" stroke="#2a221d" stroke-width="1" transform="rotate(-3 45 13)"/>'
    )
    return k.face_pattern(pid, body)


SKINS = {
    "directors_chair": directors_chair,
    "vanity": vanity,
    "spotlight": spotlight,
    "costume_rack": costume_rack,
    "flat_tree": flat_tree,
    "prop_trunk": prop_trunk,
    "wig_stand": wig_stand,
    "sandbag": sandbag,
    "pumpkin_coach": pumpkin_coach,
    "stage_coffin": stage_coffin,
}
WALLPAPERS = {"curtain_red": _curtain, "blackbox": _blackbox, "poster_brick": _posters}
STRETCH = {"vanity", "costume_rack", "pumpkin_coach", "stage_coffin"}
TALL = {"vanity", "spotlight", "costume_rack", "flat_tree", "sandbag"}
