"""The Midnight Meridian sleeper: berths, a dining car, a samovar, luggage and a coal heap."""

from . import _kit as k
from ._kit import INK, f, grad, legs, s, shadow

GRADIENTS = {
    "mahogany": ("#8a4a32", "#5e2f1f"),
    "green-velvet": ("#4f8a6a", "#2f5f48"),
    "green-velvet-front": ("#2f5f48", "#244a38"),
    "churn": ("#e3e7e6", "#a9b1b0"),
    "wicker": ("#dcb57a", "#b88d52"),
    "tartan": ("#3f6d5c", "#2c4f42"),
}


def berth(w, h):
    out = [
        k.bed(
            w,
            h,
            frame=grad("mahogany"),
            frame_light="#c07a56",
            sheet="#fbf8f1",
            blanket=grad("tartan"),
            band="#d9473a",
            leg="#3b1f14",
        )
    ]
    if w > h * 1.15:
        out.append(
            f'<path d="M10 -14H30V60Q26 66 22 60Q18 66 14 60Q10 66 10 60Z" fill="{grad("green-velvet")}" {s(1.8)}/>'
            f'<path d="M15 -10V56M21 -10V58M26 -10V56" stroke="#244a38" stroke-width="1.2"/>'
            f'<rect x="8" y="-18" width="24" height="5" rx="2" fill="{grad("brass")}" {s(1.2)}/>'
        )
    else:
        x1 = w - 10
        out.append(
            f'<path d="M{f(x1 - 20)} -14H{f(x1 + 2)}V{f(h - 34)}Q{f(x1 - 2)} {f(h - 28)} {f(x1 - 6)} {f(h - 34)}'
            f'Q{f(x1 - 10)} {f(h - 28)} {f(x1 - 14)} {f(h - 34)}Q{f(x1 - 18)} {f(h - 28)} {f(x1 - 20)} {f(h - 34)}Z" fill="{grad("green-velvet")}" {s(1.8)}/>'
            f'<path d="M{f(x1 - 14)} -10V{f(h - 38)}M{f(x1 - 7)} -10V{f(h - 38)}" stroke="#244a38" stroke-width="1.2"/>'
            f'<rect x="{f(x1 - 24)}" y="-18" width="30" height="5" rx="2" fill="{grad("brass")}" {s(1.2)}/>'
        )
        out.append(
            f'<path d="M22 -6v-8q0 -4 6 -4" fill="none" stroke="#d8b264" stroke-width="2"/>'
            f'<path d="M24 -18h12l-3 -8h-6Z" fill="#f3b8a6" {s(1.2)}/>'
        )
    return "".join(out)


def compartment_seat(w, h):
    cx = w / 2
    o = [
        k.armchair(
            w,
            h,
            back=grad("green-velvet"),
            seat="#5c9a78",
            front=grad("green-velvet-front"),
            arm=grad("green-velvet"),
            back_top=-14,
            leg="#3b1f14",
        )
    ]
    o.append(
        f'<path d="M{f(cx - 16)} -6H{f(cx + 16)}V8Q{f(cx + 12)} 12 {f(cx + 8)} 8Q{f(cx + 4)} 12 {f(cx)} 8'
        f'Q{f(cx - 4)} 12 {f(cx - 8)} 8Q{f(cx - 12)} 12 {f(cx - 16)} 8Z" fill="#fbf8f1" {s(1.2)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 12)} 0h24" stroke="#d8cdbb" stroke-width="1" stroke-dasharray="1.6 1.6"/>'
    )
    return "".join(o)


def _lamp(x, y):
    return (
        f'<ellipse cx="{f(x)}" cy="{f(y + 2)}" rx="6" ry="2.4" fill="{grad("brass")}" {s(1.1)}/>'
        f'<path d="M{f(x)} {f(y)}V{f(y - 14)}" stroke="#b58a3c" stroke-width="2"/>'
        f'<ellipse cx="{f(x)}" cy="{f(y - 18)}" rx="11" ry="9" fill="#ffd9a0" fill-opacity=".35"/>'
        f'<path d="M{f(x - 8)} {f(y - 12)}L{f(x - 5)} {f(y - 24)}H{f(x + 5)}L{f(x + 8)} {f(y - 12)}Z" fill="#f3a6b6" {s(1.3)}/>'
        f'<path d="M{f(x - 4)} {f(y - 23)}l-1.6 10M{f(x)} {f(y - 23)}v10M{f(x + 4)} {f(y - 23)}l1.6 10" stroke="#d97f94" stroke-width=".9"/>'
    )


def _place(x, y):
    return (
        f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="10" ry="6.4" fill="#ffffff" {s(1.3)}/>'
        f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="6" ry="3.6" fill="none" stroke="#2f5f48" stroke-width="1.2"/>'
        f'<path d="M{f(x - 14)} {f(y - 4)}v8M{f(x + 14)} {f(y - 4)}v8" stroke="#9aa1a8" stroke-width="1.8" stroke-linecap="round"/>'
    )


def dining_car_table(w, h):
    x0, x1 = 8, w - 8
    tall = h > w * 1.15
    top_y, top_h = 18, (h - 70 if tall else 40)
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2, 10)]
    for lx in (x0 + 10, x1 - 10):
        o.append(
            f'<rect x="{f(lx - 4)}" y="{f(top_y + top_h)}" width="8" height="{f(h - 8 - top_y - top_h)}" fill="#5e2f1f" {s(1.6)}/>'
        )
    o.append(
        f'<rect x="{f(x0)}" y="{top_y}" width="{f(x1 - x0)}" height="{f(top_h)}" rx="4" fill="#fbf8f1" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0)} {f(top_y + top_h)}V{f(top_y + top_h + 12)}Q{f((x0 + x1) / 2)} {f(top_y + top_h + 16)} {f(x1)} {f(top_y + top_h + 12)}V{f(top_y + top_h)}Z" fill="#efe9dc" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 4)} {f(top_y + top_h + 10)}H{f(x1 - 4)}" stroke="#2f5f48" stroke-width="1.4"/>'
    )
    if tall:
        n = max(1, int(top_h // 55))
        spots = [(w / 2, top_y + top_h * (i + 0.5) / n) for i in range(n)]
    else:
        spots = [
            (
                x0 + (x1 - x0) * (i + 0.5) / max(1, int((x1 - x0) // 80)),
                top_y + top_h * 0.55,
            )
            for i in range(max(1, int((x1 - x0) // 80)))
        ]
    for x, y in spots:
        o.append(_place(x - 18, y + 4))
        o.append(_place(x + 18, y + 4))
        o.append(_lamp(x, y + 2))
        o.append(
            f'<path d="M{f(x + 30)} {f(y - 8)}l-3 8h6Z" fill="#ffffff" {s(1)}/>'
            f'<path d="M{f(x - 30)} {f(y - 10)}v8M{f(x - 33)} {f(y - 14)}h6l-1 4h-4Z" stroke="#c9d9de" fill="#e8f2f4" stroke-width="1"/>'
        )
    return "".join(o)


def samovar(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 28, 7)]
    o.append(
        f'<ellipse cx="{f(cx)}" cy="80" rx="28" ry="7" fill="{grad("brass")}" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 10)} 78L{f(cx - 14)} 66H{f(cx + 14)}L{f(cx + 10)} 78Z" fill="{grad("brass")}" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 14)} 66Q{f(cx - 27)} 48 {f(cx - 20)} 26Q{f(cx - 15)} 14 {f(cx)} 12Q{f(cx + 15)} 14 {f(cx + 20)} 26Q{f(cx + 27)} 48 {f(cx + 14)} 66Z" '
        f'fill="{grad("gold")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 22)} 36Q{f(cx)} 42 {f(cx + 22)} 36" fill="none" stroke="#9a6b1e" stroke-width="1.6"/>'
        f'<path d="M{f(cx - 21)} 52Q{f(cx)} 58 {f(cx + 21)} 52" fill="none" stroke="#9a6b1e" stroke-width="1.6"/>'
    )
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx + side * 20)} 24q{f(side * 9)} 2 {f(side * 8)} 12",
                "#2a221d",
                3.4,
            )
        )
    o.append(
        f'<rect x="{f(cx - 16)}" y="50" width="8" height="5" rx="1.5" fill="{grad("brass")}" {s(1.1)}/>'
        f'<path d="M{f(cx - 16)} 55v5" stroke="#d8b264" stroke-width="2.4"/>'
        f'<rect x="{f(cx - 14)}" y="45" width="4" height="6" rx="1" fill="#2a221d"/>'
    )
    o.append(
        f'<rect x="{f(cx - 5)}" y="4" width="10" height="9" fill="{grad("brass")}" {s(1.2)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 10)} 4Q{f(cx - 12)} -8 {f(cx)} -10Q{f(cx + 12)} -8 {f(cx + 10)} 4Z" fill="#fbf8f1" {s(1.4)}/>'
        f'<path d="M{f(cx + 10)} -2l7 -4" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
        f'<path d="M{f(cx - 8)} -3q4 3 8 0t8 0" fill="none" stroke="#3f6fb0" stroke-width="1.4"/>'
        f'<circle cx="{f(cx)}" cy="-12" r="2" fill="#3f6fb0" {s(.8)}/>'
    )
    o.append(k.highlight(f"M{f(cx - 14)} 30Q{f(cx - 18)} 44 {f(cx - 12)} 58", 0.5, 2.6))
    return "".join(o)


def _suitcase(x, y, w, h, colour):
    return (
        f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="3" fill="{colour}" {s(1.6)}/>'
        f'<path d="M{f(x + w * 0.3)} {f(y)}V{f(y + h)}M{f(x + w * 0.7)} {f(y)}V{f(y + h)}" stroke="#5a3826" stroke-width="2"/>'
        f'<path d="M{f(x + w / 2 - 5)} {f(y)}q5 -5 10 0" fill="none" stroke="{INK}" stroke-width="1.8"/>'
    )


def luggage_rack(w, h):
    if h > w * 1.15:
        return "".join(
            f'<g transform="translate(0 {i * 100})">{luggage_rack(w, 100)}</g>'
            for i in range(int(round(h / 100)))
        )
    x0, x1 = 10, w - 10
    o = [shadow(w / 2, h - 10, (x1 - x0) / 2 + 2, 8)]
    span = x1 - x0
    o.append(_suitcase(x0 + 6, -8, min(40, span * 0.5), 26, "#b5703f"))
    o.append(
        f'<ellipse cx="{f(x1 - 18)}" cy="6" rx="13" ry="5" fill="#c7718a" {s(1.4)}/>'
        f'<path d="M{f(x1 - 31)} 6V16Q{f(x1 - 18)} 24 {f(x1 - 5)} 16V6" fill="#c7718a" {s(1.4)}/>'
    )
    o.append(_suitcase(x0 + 8, 38, min(46, span * 0.55), 32, "#7a2f3f"))
    if span > 70:
        o.append(
            _suitcase(
                x0 + 8 + min(46, span * 0.55) + 4,
                46,
                span - min(46, span * 0.55) - 16,
                24,
                "#3f6d8a",
            )
        )
    for px in (x0 + 2, x1 - 2):
        o.append(k.outlined(f"M{f(px)} -10V84", "#d8b264", 3.2, cap="butt"))
    for y in (18, 70):
        o.append(k.outlined(f"M{f(x0)} {y}H{f(x1)}", "#d8b264", 3.2, cap="butt"))
        o.append(k.outlined(f"M{f(x0)} {y + 6}H{f(x1)}", "#c09848", 2.4, cap="butt"))
    return "".join(o)


def luggage_trolley(w, h):
    if h > w * 1.15 or w < 150:
        if h > 100:
            return (
                f'<g transform="translate(0 {f(h - 100)})">{_trolley_front(w, 100)}</g>'
            )
        return _trolley_front(w, h)
    x0, x1 = 8, w - 8
    mid = (x0 + x1) / 2
    o = [shadow(mid, h - 12, (x1 - x0) / 2, 9)]
    o.append(
        k.outlined(
            f"M{f(x1 - 20)} 60L{f(x1 - 6)} 14M{f(x1 - 12)} 16H{f(x1 + 2)}", "#6e4527", 4
        )
    )
    o.append(
        f'<rect x="{f(x0 + 6)}" y="56" width="{f(x1 - x0 - 30)}" height="9" rx="2" fill="{grad("wood")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(x0 + 10)} 74L{f(x0 + 14)} 65M{f(x1 - 30)} 74L{f(x1 - 34)} 65" stroke="{INK}" stroke-width="3"/>'
    )
    o.append(k.wheel(mid - 10, 72, 13, spoke="#5a6066", hub="#9aa1a8"))
    o.append(
        k.block(
            x0 + 10, x0 + 70, 24, 32, 56, lid="#6f8f66", face="#4f6b4a", side="#34482f"
        )
    )
    o.append(
        f'<path d="M{f(x0 + 24)} 32V56M{f(x0 + 56)} 32V56" stroke="#6b3f22" stroke-width="4"/>'
    )
    o.append(_suitcase(x0 + 84, 28, 46, 28, "#b5703f"))
    o.append(_suitcase(x0 + 90, 8, 34, 20, "#7a2f3f"))
    o.append(
        f'<ellipse cx="{f(x0 + 40)}" cy="20" rx="14" ry="5" fill="#c7718a" {s(1.4)}/>'
        f'<path d="M{f(x0 + 26)} 20V14Q{f(x0 + 40)} 6 {f(x0 + 54)} 14V20" fill="#e9a6b7" {s(1.4)}/>'
    )
    return "".join(o)


def _trolley_front(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 32, 8)]
    o.append(
        k.outlined(f"M{f(cx - 22)} 60V8H{f(cx + 22)}V60", "#6e4527", 3.4, cap="butt")
    )
    o.append(_suitcase(cx - 24, 34, 48, 28, "#b5703f"))
    o.append(_suitcase(cx - 18, 14, 36, 20, "#7a2f3f"))
    o.append(
        f'<rect x="{f(cx - 30)}" y="62" width="60" height="9" rx="2" fill="{grad("wood")}" {s()}/>'
    )
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 22)}" cy="78" rx="5" ry="10" fill="#3a3f44" {s(1.6)}/>'
        )
    return "".join(o)


def _sack(x, base, height, colour, stripe):
    top = base - height
    return (
        f'<path d="M{f(x - 14)} {f(base)}Q{f(x - 18)} {f(top + 16)} {f(x - 7)} {f(top + 8)}L{f(x - 4)} {f(top)}H{f(x + 4)}'
        f'L{f(x + 7)} {f(top + 8)}Q{f(x + 18)} {f(top + 16)} {f(x + 14)} {f(base)}Q{f(x)} {f(base + 4)} {f(x - 14)} {f(base)}Z" fill="{colour}" {s()}/>'
        f'<path d="M{f(x - 7)} {f(top + 8)}H{f(x + 7)}" stroke="#8a6a3c" stroke-width="2.6"/>'
        f'<path d="M{f(x - 12)} {f(base - height * 0.38)}Q{f(x)} {f(base - height * 0.32)} {f(x + 12)} {f(base - height * 0.38)}" fill="none" stroke="{stripe}" stroke-width="3"/>'
    )


def mail_sacks(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 36, 8)]
    o.append(_sack(cx - 16, 70, 42, "#d9d2bd", "#3f6fb0"))
    o.append(_sack(cx + 16, 72, 46, "#e3dcc8", "#c43c3c"))
    o.append(_sack(cx, 84, 40, "#efe9d8", "#c43c3c"))
    o.append(
        f'<text x="{f(cx)}" y="79" font-size="8.5" font-family="DM Mono" font-weight="500" text-anchor="middle" fill="#5a3826">MAIL</text>'
    )
    return "".join(o)


def hamper(w, h):
    x0, x1 = 14, w - 22
    top, front, bottom = 38, 50, h - 12
    o = [shadow((x0 + x1) / 2 + 4, bottom + 2, 34, 8)]
    o.append(
        k.block(
            x0,
            x1,
            top,
            front,
            bottom,
            lid="#e6c48d",
            face=grad("wicker"),
            side="#a87a40",
        )
    )
    weave = "".join(
        f"M{f(x)} {front + 2}V{bottom - 2}" for x in range(int(x0 + 6), int(x1 - 2), 6)
    ) + "".join(
        f"M{f(x0 + 2)} {y}H{f(x1 - 2)}" for y in range(front + 6, bottom - 2, 6)
    )
    o.append(f'<path d="{weave}" stroke="#a87a40" stroke-width="1"/>')
    o.append(
        f'<path d="M{f(x0 + 16)} {front + 10}L{f(x0 + 6)} {front - 2}H{f(x0 + 26)}Z" fill="#d9473a"/>'
        f'<path d="M{f(x0 + 8)} {front}l4 4M{f(x0 + 14)} {front}l4 4M{f(x0 + 20)} {front}l4 4" stroke="#fbf8f1" stroke-width="1.6"/>'
    )
    for sx in (x0 + 14, x1 - 14):
        o.append(
            f'<path d="M{f(sx + 6)} {top}L{f(sx)} {front}V{front + 14}" fill="none" stroke="#6b3f22" stroke-width="4"/>'
            f'<rect x="{f(sx - 3.4)}" y="{front + 8}" width="7" height="6" rx="1" fill="none" stroke="#d8b264" stroke-width="1.6"/>'
        )
    o.append(
        f'<path d="M{f((x0 + x1) / 2 - 8)} {top + 4}q8 -10 16 0" fill="none" stroke="{INK}" stroke-width="3"/>'
    )
    return "".join(o)


def railway_lantern(w, h):
    cx = w / 2
    o = [
        f'<ellipse cx="{f(cx)}" cy="{h - 8}" rx="30" ry="7" fill="#e2523f" fill-opacity=".18"/>',
        shadow(cx, h - 12, 22, 6),
    ]
    o.append(
        k.outlined(
            f"M{f(cx - 14)} 22Q{f(cx - 14)} -4 {f(cx)} -4Q{f(cx + 14)} -4 {f(cx + 14)} 22",
            "#5a6066",
            2.4,
        )
    )
    o.append(
        f'<rect x="{f(cx - 17)}" y="74" width="34" height="8" rx="2" fill="#26292c" {s()}/>'
    )
    o.append(
        f'<rect x="{f(cx - 14)}" y="28" width="28" height="48" rx="4" fill="#2b2f33" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 16)} 28L{f(cx - 10)} 16H{f(cx + 10)}L{f(cx + 16)} 28Z" fill="#3a3f44" {s()}/>'
        f'<rect x="{f(cx - 4)}" y="8" width="8" height="9" fill="#3a3f44" {s(1.4)}/>'
        f'<rect x="{f(cx - 6)}" y="5" width="12" height="4" rx="1.5" fill="#2b2f33" {s(1.2)}/>'
    )
    o.append(
        f'<circle cx="{f(cx)}" cy="51" r="15" fill="#ff8a6a" fill-opacity=".3"/>'
        f'<circle cx="{f(cx)}" cy="51" r="11" fill="#e2523f" stroke="{INK}" stroke-width="1.8"/>'
        f'<circle cx="{f(cx)}" cy="51" r="11" fill="none" stroke="#9aa1a8" stroke-width="2.6" stroke-opacity=".9"/>'
        f'<circle cx="{f(cx - 4)}" cy="47" r="3" fill="#ffd2c4"/>'
    )
    o.append(
        f'<ellipse cx="{f(cx + 14)}" cy="51" rx="2.6" ry="7" fill="#4fae6a" {s(1.2)}/>'
    )
    return "".join(o)


def coal_heap(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 38, 8)]
    o.append(k.outlined(f"M{f(cx + 6)} 46L{f(cx + 26)} -4", "#a8723f", 3.6))
    o.append(
        f'<path d="M{f(cx + 20)} -10h12l-2 8h-8Z" fill="none" stroke="{INK}" stroke-width="2.6"/>'
    )
    o.append(
        f'<path d="M{f(cx - 38)} 84Q{f(cx - 30)} 52 {f(cx - 8)} 42Q{f(cx + 10)} 34 {f(cx + 24)} 46Q{f(cx + 40)} 60 {f(cx + 38)} 84Z" fill="#26262b" {s()}/>'
    )
    o.append(f'<path d="M{f(cx + 2)} 42l8 -2 4 10 -10 4Z" fill="#9aa1a8" {s(1.2)}/>')
    lumps = (
        (-24, 70),
        (-12, 62),
        (2, 66),
        (16, 60),
        (26, 72),
        (-30, 80),
        (-6, 76),
        (10, 78),
        (-18, 52),
        (6, 50),
    )
    for i, (x, y) in enumerate(lumps):
        r = 5 + (i % 3)
        o.append(
            f'<path d="M{f(cx + x - r)} {y}L{f(cx + x - r * 0.3)} {y - r}L{f(cx + x + r)} {f(y - r * 0.4)}L{f(cx + x + r * 0.6)} {y + r * 0.6}Z" '
            f'fill="#3a3a42" stroke="#121214" stroke-width="1"/>'
            f'<path d="M{f(cx + x - r * 0.3)} {y - r}L{f(cx + x + r)} {f(y - r * 0.4)}" stroke="#8a8a96" stroke-width="1.2"/>'
        )
    return "".join(o)


def milk_churn(w, h):
    cx = w / 2
    o = [shadow(cx, h - 12, 26, 7)]
    body = (
        f"M{f(cx - 20)} 82V38Q{f(cx - 20)} 26 {f(cx - 9)} 20V12H{f(cx + 9)}V20Q{f(cx + 20)} 26 {f(cx + 20)} 38V82"
        f"Q{f(cx)} 88 {f(cx - 20)} 82Z"
    )
    o.append(f'<path d="{body}" fill="{grad("churn")}" {s()}/>')
    for y in (44, 74):
        o.append(
            f'<path d="M{f(cx - 20)} {y}Q{f(cx)} {y + 5} {f(cx + 20)} {y}" fill="none" stroke="#7f8988" stroke-width="2.6"/>'
        )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="12" rx="13" ry="4" fill="#d6dcdb" {s(1.6)}/>'
        f'<path d="M{f(cx - 13)} 12V8Q{f(cx)} 2 {f(cx + 13)} 8V12" fill="#c3cac9" {s(1.6)}/>'
        f'<rect x="{f(cx - 3)}" y="1" width="6" height="4" rx="1.5" fill="#9aa1a8" {s(1)}/>'
    )
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx + side * 12)} 24q{f(side * 10)} -2 {f(side * 10)} 8",
                "#9aa1a8",
                2.6,
            )
        )
    o.append(k.highlight(f"M{f(cx - 12)} 34V76", 0.7, 3))
    o.append(
        f'<rect x="{f(cx - 7)}" y="52" width="14" height="9" rx="1.5" fill="{grad("brass")}" {s(1)}/>'
    )
    return "".join(o)


def _walnut_panels(pid):
    body = (
        '<rect width="100" height="26" fill="#6e4527"/>'
        '<rect x="6" y="7" width="38" height="11" rx="1.5" fill="#8a5a37" stroke="#4a2c1d" stroke-width="1"/>'
        '<rect x="56" y="7" width="38" height="11" rx="1.5" fill="#8a5a37" stroke="#4a2c1d" stroke-width="1"/>'
        '<path d="M25 9l4 3.5-4 3.5-4 -3.5ZM75 9l4 3.5-4 3.5-4 -3.5Z" fill="#d9b866"/>'
    )
    return k.face_pattern(pid, body)


def _night_window(pid):
    def window(x, moon):
        extra = (
            f'<circle cx="{x + 34}" cy="11" r="3" fill="#f6e7c1"/><circle cx="{x + 35.4}" cy="10" r="2.6" fill="#1d2b4f"/>'
            if moon
            else ""
        )
        return (
            f'<rect x="{x + 18}" y="7" width="64" height="12" rx="2" fill="#1d2b4f" stroke="#5a3826" stroke-width="2"/>'
            f'<g fill="#f6e7c1"><circle cx="{x + 26}" cy="10" r=".9"/><circle cx="{x + 48}" cy="13" r=".8"/>'
            f'<circle cx="{x + 60}" cy="9.5" r="1"/><circle cx="{x + 72}" cy="14" r=".8"/></g>'
            f'<path d="M{x + 19} 18q10 -5 20 -1t22 -2t20 1V19H{x + 19}Z" fill="#2f4a3f"/>'
            + extra
            + f'<path d="M{x + 18} 7q6 4 4 12H{x + 18}Z" fill="#7a2f3f"/>'
        )

    body = (
        '<rect width="200" height="26" fill="#6e4527"/>'
        + window(0, True)
        + window(100, False)
    )
    return k.face_pattern(pid, body, width=200)


def _green_velvet(pid):
    body = (
        '<rect width="100" height="26" fill="#2f5c48"/>'
        '<path d="M0 8.5H100" stroke="#d9b866" stroke-width="1.6"/>'
        + "".join(
            f'<circle cx="{x}" cy="14" r="1.2" fill="#244a38"/>'
            for x in range(10, 100, 20)
        )
        + '<path d="M0 18H100" stroke="#d9b866" stroke-width=".8" stroke-opacity=".7"/>'
    )
    return k.face_pattern(pid, body)


SKINS = {
    "berth": berth,
    "compartment_seat": compartment_seat,
    "dining_car_table": dining_car_table,
    "samovar": samovar,
    "luggage_rack": luggage_rack,
    "luggage_trolley": luggage_trolley,
    "mail_sacks": mail_sacks,
    "hamper": hamper,
    "railway_lantern": railway_lantern,
    "coal_heap": coal_heap,
    "milk_churn": milk_churn,
}
WALLPAPERS = {
    "walnut_panels": _walnut_panels,
    "night_window": _night_window,
    "green_velvet": _green_velvet,
}
STRETCH = {"berth", "dining_car_table", "luggage_rack", "luggage_trolley"}
TALL = {
    "berth",
    "compartment_seat",
    "samovar",
    "luggage_rack",
    "railway_lantern",
    "coal_heap",
}
