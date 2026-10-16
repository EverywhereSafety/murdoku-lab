"""The ocean liner Aurelia: deck chairs, lifeboats, a ship's telegraph and steamer trunks."""

import math

from . import _kit as k
from ._kit import INK, f, grad, legs, s, shadow

GRADIENTS = {
    "teak": ("#d29a66", "#a86d3e"),
    "lifeboat": ("#fefdf8", "#d8d2c3"),
    "iron": ("#737c84", "#454c53"),
    "rope": ("#ecd29c", "#c49b5b"),
    "trunk": ("#5c7a54", "#3f5a3a"),
    "navy-wool": ("#3d5f86", "#26425f"),
}


def deck_chair(w, h):
    cx = w / 2
    top, seat = 4, 60
    o = [shadow(cx, h - 12, 34, 8)]
    stripes = 6
    for i in range(stripes):
        a0, a1 = i / stripes, (i + 1) / stripes
        xa0, xa1 = cx - 23 + 46 * a0, cx - 23 + 46 * a1
        xb0, xb1 = cx - 27 + 54 * a0, cx - 27 + 54 * a1
        colour = "#d9574a" if i % 2 == 0 else "#f6eedd"
        o.append(
            f'<path d="M{f(xa0)} {top}H{f(xa1)}L{f(xb1)} {seat}H{f(xb0)}Z" fill="{colour}"/>'
        )
    o.append(
        f'<path d="M{f(cx - 23)} {top}H{f(cx + 23)}L{f(cx + 27)} {seat}H{f(cx - 27)}Z" fill="none" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 25)} {seat - 16}Q{f(cx)} {seat - 5} {f(cx + 25)} {seat - 16}" fill="none" '
        f'stroke="#1b130e" stroke-opacity=".16" stroke-width="8"/>'
    )
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx + side * 27)} {top - 4}L{f(cx + side * 32)} 86", "#c98d55", 5
            )
        )
    o.append(
        k.outlined(f"M{f(cx - 27)} {top - 1}H{f(cx + 27)}", "#c98d55", 5, cap="butt")
    )
    o.append(
        f'<rect x="{f(cx - 33)}" y="{seat - 1}" width="66" height="8" rx="3" fill="{grad("teak")}" {s(1.8)}/>'
    )
    o.append(
        k.outlined(f"M{f(cx - 31)} {seat + 15}H{f(cx + 31)}", "#b07a45", 4, cap="butt")
    )
    # a folded tartan rug on the foot of the chair
    o.append(
        f'<rect x="{f(cx - 12)}" y="{seat - 12}" width="24" height="10" rx="3" fill="#3f6d5c" {s(1.4)}/>'
        f'<path d="M{f(cx - 6)} {seat - 12}v10M{f(cx + 4)} {seat - 12}v10M{f(cx - 12)} {seat - 7}h24" '
        f'stroke="#e2b44c" stroke-width="1.4"/>'
    )
    return "".join(o)


def bunk(w, h):
    out = [
        k.bed(
            w,
            h,
            frame=grad("teak"),
            frame_light="#ecbd8c",
            sheet=grad("cream"),
            blanket=grad("navy-wool"),
            band="#f6f1e4",
        )
    ]
    # the lee-board that keeps a sleeper in the berth in a swell, and a brass reading lamp
    if w > h * 1.15:
        out.append(
            f'<rect x="28" y="54" width="{f(w - 60)}" height="10" rx="3" fill="{grad("teak")}" {s(1.8)}/>'
        )
        out.append(
            f'<circle cx="20" cy="2" r="6" fill="{grad("brass")}" {s(1.4)}/><circle cx="20" cy="2" r="2.6" fill="#fff3c8"/>'
        )
    else:
        out.append(
            f'<rect x="{f(w - 22)}" y="22" width="10" height="{f(h - 50)}" rx="3" fill="{grad("teak")}" {s(1.8)}/>'
        )
        out.append(
            f'<circle cx="{f(w - 22)}" cy="-6" r="6" fill="{grad("brass")}" {s(1.4)}/><circle cx="{f(w - 22)}" cy="-6" r="2.6" fill="#fff3c8"/>'
        )
    return "".join(out)


def lifeboat(w, h):
    if h > w * 1.15:
        return _lifeboat_upright(w, h)
    x0, x1 = 6, w - 6
    span = x1 - x0
    mid = (x0 + x1) / 2
    g = 30
    half = min(18, span * 0.12)
    keel = half + 24
    o = [shadow(mid, h - 12, span / 2, 9)]
    for cxk in (x0 + span * 0.28, x0 + span * 0.72):
        o.append(
            f'<path d="M{f(cxk - 13)} {h - 14}L{f(cxk - 8)} {g + 26}H{f(cxk + 8)}L{f(cxk + 13)} {h - 14}Z" fill="{grad("teak")}" {s(1.8)}/>'
        )
    o.append(
        f'<path d="M{f(x0)} {g}Q{f(mid)} {f(g + 2 * keel)} {f(x1)} {g}Z" fill="{grad("lifeboat")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 5)} {g + 2}Q{f(mid)} {f(g + 2 * (half + 6))} {f(x1 - 5)} {g + 2}" fill="none" '
        f'stroke="#d9473a" stroke-width="3.4"/>'
    )
    lens = (
        f"M{f(x0)} {g}Q{f(mid)} {f(g - 2 * half)} {f(x1)} {g}"
        f"Q{f(mid)} {f(g + 2 * half)} {f(x0)} {g}Z"
    )
    o.append(f'<path d="{lens}" fill="{grad("teak")}" {s()}/>')
    for t in (0.3, 0.5, 0.7):
        bx = x0 + span * t
        dy = 4 * half * t * (1 - t)
        o.append(
            f'<rect x="{f(bx - 4)}" y="{f(g - dy + 2)}" width="8" height="{f(2 * dy - 4)}" rx="2" '
            f'fill="#ecc28c" stroke="#7a4d2a" stroke-width="1.2"/>'
        )
    if span > 150:
        o.append(
            k.outlined(
                f"M{f(x0 + span * 0.22)} {g - 3}L{f(x0 + span * 0.78)} {g + 2}",
                "#f1e4c4",
                3,
                ink_width=5,
            )
        )
        o.append(
            f'<text x="{f(mid)}" y="{f(g + half + 18)}" font-size="9" font-family="DM Mono" font-weight="500" '
            f'text-anchor="middle" fill="#1e3651" letter-spacing="1.6">AURELIA</text>'
        )
    o.append(f'<path d="{lens}" fill="none" stroke="#f2ede1" stroke-width="2.2"/>')
    o.append(f'<path d="{lens}" fill="none" {s(1.4)}/>')
    return "".join(o)


def _lifeboat_upright(w, h):
    cx = w / 2
    y0, y1 = 4, h - 24
    span = y1 - y0
    mid = (y0 + y1) / 2
    half = min(26, w * 0.28)
    o = [shadow(cx, h - 12, half + 8, 10)]
    o.append(
        f'<path d="M{f(cx)} {y0}Q{f(cx + 2 * half + 8)} {f(mid + 8)} {f(cx)} {f(y1 + 16)}'
        f'Q{f(cx - 2 * half - 8)} {f(mid + 8)} {f(cx)} {y0}Z" fill="{grad("lifeboat")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - half - 2)} {f(mid + 26)}Q{f(cx)} {f(y1 + 18)} {f(cx + half + 2)} {f(mid + 26)}" '
        f'fill="none" stroke="#d9473a" stroke-width="3.2"/>'
    )
    lens = (
        f"M{f(cx)} {y0}Q{f(cx + 2 * half)} {f(mid)} {f(cx)} {f(y1)}"
        f"Q{f(cx - 2 * half)} {f(mid)} {f(cx)} {y0}Z"
    )
    o.append(f'<path d="{lens}" fill="{grad("teak")}" {s()}/>')
    for t in (0.3, 0.5, 0.7):
        by = y0 + span * t
        dx = 4 * half * t * (1 - t)
        o.append(
            f'<rect x="{f(cx - dx + 2)}" y="{f(by - 4)}" width="{f(2 * dx - 4)}" height="8" rx="2" '
            f'fill="#ecc28c" stroke="#7a4d2a" stroke-width="1.2"/>'
        )
    o.append(f'<path d="{lens}" fill="none" stroke="#f2ede1" stroke-width="2.2"/>')
    o.append(f'<path d="{lens}" fill="none" {s(1.4)}/>')
    return "".join(o)


def ship_telegraph(w, h):
    cx, hy = w / 2, 10
    o = [shadow(cx, h - 12, 24, 7)]
    o.append(
        f'<ellipse cx="{f(cx)}" cy="80" rx="19" ry="7" fill="{grad("brass")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 8)} 80L{f(cx - 6)} 32H{f(cx + 6)}L{f(cx + 8)} 80Z" fill="{grad("brass")}" {s()}/>'
    )
    o.append(k.highlight(f"M{f(cx - 3)} 74V38", 0.55, 2))
    o.append(f'<circle cx="{f(cx)}" cy="{hy}" r="27" fill="{grad("brass")}" {s()}/>')
    o.append(
        f'<path d="M{f(cx)} {hy - 21}A21 21 0 0 0 {f(cx)} {hy + 21}V{hy + 12}A12 12 0 0 1 {f(cx)} {hy - 12}Z" fill="#cfe3c4"/>'
        f'<path d="M{f(cx)} {hy - 21}A21 21 0 0 1 {f(cx)} {hy + 21}V{hy + 12}A12 12 0 0 0 {f(cx)} {hy - 12}Z" fill="#f1b7a9"/>'
        f'<circle cx="{f(cx)}" cy="{hy}" r="12" fill="#fbf6e8"/>'
    )
    ticks = "".join(
        f"M{f(cx + 13 * math.cos(math.radians(a)))} {f(hy + 13 * math.sin(math.radians(a)))}"
        f"L{f(cx + 20 * math.cos(math.radians(a)))} {f(hy + 20 * math.sin(math.radians(a)))}"
        for a in range(0, 360, 30)
    )
    o.append(f'<path d="{ticks}" stroke="#5a4a2c" stroke-width="1.2"/>')
    o.append(f'<circle cx="{f(cx)}" cy="{hy}" r="21" fill="none" {s(1.6)}/>')
    o.append(
        f'<path d="M{f(cx)} {hy}L{f(cx + 9)} {hy - 15}" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
        f'<path d="M{f(cx + 6)} {hy - 10}L{f(cx + 9)} {hy - 15}" stroke="#d9473a" stroke-width="3" stroke-linecap="round"/>'
    )
    o.append(f'<circle cx="{f(cx)}" cy="{hy}" r="4" fill="{grad("brass")}" {s(1.2)}/>')
    o.append(
        k.outlined(f"M{f(cx + 25)} {hy + 6}L{f(cx + 38)} {hy - 12}", "#d8b264", 4.4)
    )
    o.append(
        f'<circle cx="{f(cx + 38)}" cy="{hy - 12}" r="5" fill="#2a221d" stroke="{INK}" stroke-width="1.4"/>'
    )
    return "".join(o)


def steamer_trunk(w, h):
    x0, x1 = 12, w - 22
    top, front, bottom = 30, 46, h - 12
    o = [shadow((x0 + x1) / 2 + 4, bottom + 2, 38, 8)]
    o.append(
        k.block(
            x0,
            x1,
            top,
            front,
            bottom,
            lid="#6f8f66",
            face=grad("trunk"),
            side="#34482f",
        )
    )
    o.append(
        f'<path d="M{f(x0 + 2)} {front + 11}H{f(x1 - 2)}M{f(x0 + 2)} {bottom - 9}H{f(x1 - 2)}" '
        f'stroke="#c9945e" stroke-width="3.4"/>'
    )
    for sx in (x0 + 15, x1 - 15):
        o.append(
            f'<path d="M{f(sx + 8)} {top}L{f(sx)} {front}V{bottom}" fill="none" stroke="#6b3f22" stroke-width="5.5"/>'
        )
        o.append(
            f'<rect x="{f(sx - 4)}" y="{front + 3}" width="8" height="7" rx="1" fill="none" stroke="#d8b264" stroke-width="2"/>'
        )
    for cx_, cy_ in ((x0, front), (x1, front), (x0, bottom), (x1, bottom)):
        o.append(
            f'<circle cx="{f(cx_)}" cy="{f(cy_)}" r="3.4" fill="{grad("brass")}" {s(1.1)}/>'
        )
    mx = (x0 + x1) / 2
    o.append(
        f'<circle cx="{f(mx - 3)}" cy="{front + 23}" r="7" fill="#e8c35a" {s(1.2)}/>'
        f'<circle cx="{f(mx - 3)}" cy="{front + 23}" r="3.4" fill="#d9473a"/>'
        f'<rect x="{f(mx + 6)}" y="{front + 16}" width="12" height="9" rx="1.5" fill="#f6efe0" {s(1.1)} '
        f'transform="rotate(-8 {f(mx + 12)} {front + 20})"/>'
        f'<path d="M{f(mx + 8)} {front + 20}h8" stroke="#3d5f86" stroke-width="1.6" transform="rotate(-8 {f(mx + 12)} {front + 20})"/>'
    )
    return "".join(o)


def life_ring(w, h):
    cx, cy, r = w / 2, 40, 22
    o = [shadow(cx, h - 12, 26, 7)]
    o.append(
        f'<rect x="{f(cx - 5)}" y="0" width="10" height="82" rx="2" fill="{grad("teak")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 13)}" y="78" width="26" height="8" rx="3" fill="#8a5a33" {s(1.6)}/>'
    )
    o.append(
        f'<circle cx="{f(cx)}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="16"/>'
        f'<circle cx="{f(cx)}" cy="{cy}" r="{r}" fill="none" stroke="#fbf7ee" stroke-width="12"/>'
    )
    seg = 2 * math.pi * r / 8
    o.append(
        f'<circle cx="{f(cx)}" cy="{cy}" r="{r}" fill="none" stroke="#d9473a" stroke-width="12" '
        f'stroke-dasharray="{f(seg)} {f(seg)}" transform="rotate(-22.5 {f(cx)} {cy})"/>'
    )
    d = []
    for i in range(4):
        a0, a1 = math.radians(45 + 90 * i), math.radians(135 + 90 * i)
        am = (a0 + a1) / 2
        p0 = (cx + (r + 7) * math.cos(a0), cy + (r + 7) * math.sin(a0))
        p1 = (cx + (r + 7) * math.cos(a1), cy + (r + 7) * math.sin(a1))
        c = (cx + (r + 14) * math.cos(am), cy + (r + 14) * math.sin(am))
        d.append(f"M{f(p0[0])} {f(p0[1])}Q{f(c[0])} {f(c[1])} {f(p1[0])} {f(p1[1])}")
    o.append(k.outlined("".join(d), "#ead19a", 2.4, ink_width=4.4))
    o.append(
        k.highlight(
            f"M{f(cx - 17)} {cy - 9}Q{f(cx - 10)} {cy - 19} {f(cx + 1)} {cy - 21}",
            0.75,
            2.4,
        )
    )
    return "".join(o)


def figurehead(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 30, 8)]
    o.append(
        k.block(
            cx - 24,
            cx + 18,
            60,
            68,
            86,
            lid="#e0aa74",
            face=grad("teak"),
            side="#8a5a33",
        )
    )
    o.append(
        f'<path d="M{f(cx - 4)} -16Q{f(cx + 22)} -18 {f(cx + 28)} 4Q{f(cx + 34)} 26 {f(cx + 22)} 50'
        f'Q{f(cx + 12)} 38 {f(cx + 12)} 22Z" fill="#e2b44c" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} 64Q{f(cx - 24)} 30 {f(cx - 8)} 18H{f(cx + 8)}Q{f(cx + 22)} 30 {f(cx + 20)} 64Z" '
        f'fill="#3f7f9a" {s()}/>'
    )
    o.append(k.highlight(f"M{f(cx - 16)} 54Q{f(cx - 17)} 34 {f(cx - 8)} 24", 0.35, 2.4))
    o.append(k.outlined(f"M{f(cx - 18)} 40Q{f(cx)} 50 {f(cx + 18)} 38", "#e2b44c", 5))
    o.append(
        f'<rect x="{f(cx - 5)}" y="8" width="10" height="12" fill="#f0d2ae" {s(1.6)}/>'
    )
    o.append(f'<circle cx="{f(cx)}" cy="0" r="12" fill="#f0d2ae" {s()}/>')
    o.append(
        f'<path d="M{f(cx - 12)} -1Q{f(cx - 11)} -16 {f(cx + 2)} -14Q{f(cx + 13)} -12 {f(cx + 12)} -1'
        f'Q{f(cx + 3)} -9 {f(cx - 12)} -1Z" fill="#e2b44c" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 7)} 1q2.5 2 5 0M{f(cx + 2)} 1q2.5 2 5 0" stroke="{INK}" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
        f'<path d="M{f(cx - 2)} 6.5q2 1.4 4 0" stroke="#b5624f" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M{f(cx - 1)} 52l2.4 5 5.4 .6-4 3.6 1.2 5.3-5 -2.8-5 2.8 1.2 -5.3-4 -3.6 5.4 -.6Z" '
        f'fill="#f3d68c" stroke="{INK}" stroke-width="1"/>'
    )
    return "".join(o)


def anchor(w, h):
    cx = w / 2
    iron = "#5f676e"
    o = [shadow(cx, h - 12, 34, 8)]
    o.append(
        f'<rect x="{f(cx - 30)}" y="76" width="60" height="10" rx="3" fill="{grad("teak")}" {s(1.8)}/>'
    )
    o.append(
        f'<circle cx="{f(cx)}" cy="6" r="7" fill="none" stroke="{INK}" stroke-width="6.4"/>'
        f'<circle cx="{f(cx)}" cy="6" r="7" fill="none" stroke="{iron}" stroke-width="3.2"/>'
    )
    o.append(
        f'<rect x="{f(cx - 5)}" y="12" width="10" height="62" rx="3" fill="{grad("iron")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 26)}" y="16" width="52" height="8" rx="4" fill="{grad("iron")}" {s()}/>'
    )
    arm = f"M{f(cx - 32)} 50Q{f(cx - 28)} 78 {f(cx)} 78Q{f(cx + 28)} 78 {f(cx + 32)} 50"
    o.append(k.outlined(arm, iron, 7.5, ink_width=12))
    for side in (-1, 1):
        tx = cx + side * 32
        o.append(
            f'<path d="M{f(tx)} 36L{f(tx + side * 9)} 54L{f(tx - side * 8)} 51Z" fill="{iron}" {s(1.8)}/>'
        )
    o.append(
        f'<path d="M{f(cx - 7)} 30q7 5 14 0M{f(cx - 7)} 37q7 5 14 0M{f(cx - 7)} 44q7 5 14 0" '
        f'fill="none" stroke="#e2c48e" stroke-width="3"/>'
    )
    o.append(k.highlight(f"M{f(cx - 2)} 28V68", 0.3, 2))
    return "".join(o)


def rope_coil(w, h):
    cx = w / 2
    top, bottom, rx, ry = 44, 70, 34, 14
    o = [shadow(cx, h - 12, 38, 9)]
    o.append(
        f'<path d="M{f(cx - rx)} {top}V{bottom}A{rx} {ry} 0 0 0 {f(cx + rx)} {bottom}V{top}Z" '
        f'fill="{grad("rope")}" {s()}/>'
    )
    for yy in (top + 7, top + 14, top + 21):
        o.append(
            f'<path d="M{f(cx - rx)} {yy}A{rx} {ry} 0 0 0 {f(cx + rx)} {yy}" fill="none" stroke="#a9813f" stroke-width="1.6"/>'
        )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{top}" rx="{rx}" ry="{ry}" fill="#efd8a6" {s()}/>'
    )
    for rr in (27, 20, 13):
        o.append(
            f'<ellipse cx="{f(cx)}" cy="{top}" rx="{rr}" ry="{f(rr * ry / rx)}" fill="none" stroke="#b58c4a" stroke-width="2"/>'
        )
    o.append(f'<ellipse cx="{f(cx)}" cy="{top}" rx="6" ry="2.6" fill="#6b4b2a"/>')
    end = f"M{f(cx + 10)} {top + 1}Q{f(cx + 42)} {top + 2} {f(cx + 40)} {bottom + 6}Q{f(cx + 38)} {bottom + 13} {f(cx + 30)} {bottom + 13}"
    o.append(k.outlined(end, "#e3c38a", 4.6))
    o.append(
        f'<path d="{end}" fill="none" stroke="#a9813f" stroke-width="1.4" stroke-dasharray="2 3"/>'
    )
    return "".join(o)


def wireless_set(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 8)]
    o.append(legs(((cx - 32, 70), (cx + 32, 70)), 86, 5, "#5a3826"))
    o.append(
        f'<rect x="{f(cx - 38)}" y="54" width="76" height="12" rx="3" fill="{grad("teak")}" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 36)}" y="64" width="72" height="8" rx="2" fill="#8a5a33" {s(1.6)}/>'
    )
    for vx in (cx - 20, cx - 8, cx + 4):
        o.append(
            f'<rect x="{f(vx)}" y="0" width="7" height="12" rx="3.5" fill="#ffd27a" {s(1.2)}/>'
            f'<circle cx="{f(vx + 3.5)}" cy="4.5" r="2" fill="#ff9a3c"/>'
        )
    o.append(
        k.block(
            cx - 32, cx + 14, 6, 16, 58, lid="#c98d55", face="#2b3035", side="#6e4527"
        )
    )
    o.append(
        f'<rect x="{f(cx - 28)}" y="20" width="20" height="13" rx="2" fill="#f3ead2" {s(1.2)}/>'
        f'<path d="M{f(cx - 25)} 31a8 8 0 0 1 14 0" fill="none" stroke="#9a8f7c" stroke-width="1"/>'
        f'<path d="M{f(cx - 18)} 31l5 -7" stroke="#d9473a" stroke-width="1.4"/>'
    )
    for dx, dy in ((cx + 3, 26), (cx - 18, 45), (cx + 3, 45)):
        o.append(
            f'<circle cx="{f(dx)}" cy="{dy}" r="6.5" fill="{grad("brass")}" {s(1.2)}/>'
            f'<circle cx="{f(dx)}" cy="{dy}" r="3.6" fill="#1f2326"/>'
            f'<path d="M{f(dx)} {dy}l2.5 -2.5" stroke="#f3ead2" stroke-width="1.2"/>'
        )
    o.append(
        f'<path d="M{f(cx + 20)} 58Q{f(cx + 29)} 40 {f(cx + 38)} 58" fill="none" stroke="{INK}" stroke-width="3"/>'
    )
    for hx in (cx + 20, cx + 38):
        o.append(
            f'<ellipse cx="{f(hx)}" cy="59" rx="4.5" ry="3.5" fill="#3b2418" {s(1.2)}/>'
        )
    o.append(
        f'<rect x="{f(cx - 35)}" y="57" width="12" height="5" rx="1" fill="#1f2326"/>'
        f'<path d="M{f(cx - 34)} 57l10 -3" stroke="#d8b264" stroke-width="2.2" stroke-linecap="round"/>'
    )
    return "".join(o)


def _portholes(pid):
    holes = "".join(
        f'<circle cx="{x}" cy="13" r="5.4" fill="#e2c27a" stroke="#6b5426" stroke-width="1.1"/>'
        f'<circle cx="{x}" cy="13" r="3.4" fill="#5f97b3" stroke="#3f5f72" stroke-width=".9"/>'
        f'<path d="M{x - 2} 12q1.5 -1.5 3.4 -1" stroke="#ffffff" stroke-width="1" fill="none" stroke-linecap="round"/>'
        for x in (27, 73)
    )
    body = (
        '<rect width="100" height="26" fill="#efe9dc"/>'
        '<path d="M1 0V19M50 0V19" stroke="#d3cab7" stroke-width="1.6"/>'
        f"{holes}"
        '<g fill="#b9ae96"><circle cx="8" cy="10" r="1"/><circle cx="92" cy="10" r="1"/>'
        '<circle cx="8" cy="16" r="1"/><circle cx="92" cy="16" r="1"/></g>'
    )
    return k.face_pattern(pid, body)


def _sea_rail(pid):
    body = (
        '<rect width="100" height="26" fill="#a9d6ea"/>'
        '<rect y="12" width="100" height="7" fill="#3f86a8"/>'
        '<path d="M10 15.5q3 -1.6 6 0M46 17q3 -1.6 6 0M76 15q3 -1.6 6 0" stroke="#d8f0f6" stroke-width="1.1" fill="none"/>'
        '<path d="M0 8.5H100M0 13.5H100" stroke="#ffffff" stroke-width="2"/>'
        '<path d="M0 8V19M25 8V19M50 8V19M75 8V19" stroke="#ffffff" stroke-width="1.8"/>'
    )
    return k.face_pattern(pid, body)


def _deco_gold(pid):
    fans = []
    for x in (25, 75):
        rays = "".join(
            f"M{x} 18L{x + 7.5 * math.cos(math.radians(a)):.1f} {18 - 7.5 * math.sin(math.radians(a)):.1f}"
            for a in range(20, 180, 32)
        )
        fans.append(
            f'<path d="M{x - 8.5} 18A8.5 8.5 0 0 1 {x + 8.5} 18Z" fill="#28585d" stroke="#d9b866" stroke-width="1.1"/>'
            f'<path d="{rays}" stroke="#d9b866" stroke-width=".9"/>'
        )
    body = (
        '<rect width="100" height="26" fill="#1f4a4f"/>'
        '<path d="M0 8H100" stroke="#d9b866" stroke-width="1.2"/>'
        '<path d="M50 9V19" stroke="#d9b866" stroke-width=".9" stroke-opacity=".7"/>'
        + "".join(fans)
    )
    return k.face_pattern(pid, body)


def _bulkhead(pid):
    body = (
        '<rect width="100" height="26" fill="#8e9ba3"/>'
        '<rect y="6" width="100" height="6.5" fill="#9fabb2"/>'
        '<path d="M0 12.5H100M33 6V19M66 6V19" stroke="#6f7c84" stroke-width="1.3"/>'
        '<g fill="#5f6b72">'
        + "".join(
            f'<circle cx="{x}" cy="{y}" r="1.05"/>'
            for x in (5, 28, 38, 61, 71, 95)
            for y in (9.5, 16)
        )
        + "</g>"
    )
    return k.face_pattern(pid, body)


SKINS = {
    "deck_chair": deck_chair,
    "bunk": bunk,
    "lifeboat": lifeboat,
    "ship_telegraph": ship_telegraph,
    "steamer_trunk": steamer_trunk,
    "life_ring": life_ring,
    "figurehead": figurehead,
    "anchor": anchor,
    "rope_coil": rope_coil,
    "wireless_set": wireless_set,
}
WALLPAPERS = {
    "portholes": _portholes,
    "sea_rail": _sea_rail,
    "deco_gold": _deco_gold,
    "bulkhead": _bulkhead,
}
STRETCH = {"bunk", "lifeboat"}
TALL = {"bunk", "ship_telegraph", "figurehead", "life_ring", "wireless_set"}
