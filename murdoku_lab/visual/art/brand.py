"""Brand art: the Everywhere Safety donut-and-friend mark, with the donut in a deerstalker.

The mark is kept as it is — a sprinkled donut and a soft white dome with two big round eyes on a
ground line — and the only addition is a deerstalker on the donut. Poses change nothing but the
friend's gaze (and the hat's tilt), so the mark stays recognisable everywhere it appears.
`resources/brand.json` switches between this and a neutral placeholder of identical size.
"""

import json
import math
from pathlib import Path

INK = "#102725"
PAPER = "#fbf7ee"
HAT = "#c99a55"
HAT_DARK = "#8f6630"
CHECK = "#7b5526"

POSES = ("idle", "thinking", "pointing", "celebrating")
BRAND_PATH = Path(__file__).resolve().parents[2] / "resources" / "brand.json"


def mascot_mode():
    try:
        return json.loads(BRAND_PATH.read_text()).get("mascot", "donut")
    except FileNotFoundError:
        return "donut"


def _s(width, colour):
    return f'stroke="{colour}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"'


def _donut(cx, cy, r, hole, line, fill):
    o = [
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" {_s(3.4, line)}/>',
        f'<circle cx="{cx}" cy="{cy}" r="{hole}" fill="{fill}" {_s(3.4, line)}/>',
    ]
    for i in range(10):
        t = math.radians(i * 36 + 18)
        rr = (r + hole) / 2 + (3 if i % 2 else -2.5)
        x, y = cx + rr * math.cos(t), cy + rr * math.sin(t)
        rot = math.degrees(t) + 90 + (28 if i % 3 else -24)
        o.append(
            f'<path d="M{x - 4:.1f} {y:.1f}h8" {_s(3.2, line)} '
            f'transform="rotate({rot:.0f} {x:.1f} {y:.1f})"/>'
        )
    return "".join(o)


def _friend(line, fill, eye_ink, gaze, mood):
    """The soft dome with two big round eyes; it has no mouth, like the mark."""
    o = [
        '<path d="M50 104Q44 104 47 94Q53 70 68 57Q83 45 99 50Q115 56 121 78Q126 96 '
        f'124 102Q122 106 112 106Z" fill="{fill}" {_s(3.2, line)}/>'
    ]
    gx, gy = gaze
    for ex in (84, 105):
        ey = 78
        if mood == "celebrating":
            o.append(
                f'<path d="M{ex - 7} {ey + 2}q7 -9 14 0" fill="none" {_s(3.2, eye_ink)}/>'
            )
            continue
        o.append(
            f'<circle cx="{ex}" cy="{ey}" r="9" fill="#ffffff" {_s(2.8, eye_ink)}/>'
        )
        o.append(
            f'<circle cx="{ex + gx * 3.4:.1f}" cy="{ey + gy * 3.4:.1f}" r="4.6" fill="{eye_ink}"/>'
        )
    return "".join(o)


def _deerstalker(cx, cy, w, tilt, line, mono):
    crown = INK if mono else HAT
    peak = INK if mono else HAT_DARK
    h = w * 0.55
    o = [f'<g transform="rotate({tilt} {cx} {cy})">']
    o.append(
        f'<path d="M{cx - w * 0.62} {cy - 2}Q{cx - w * 0.66} {cy + 6} {cx - w * 0.48} {cy + 6}'
        f"H{cx + w * 0.48}Q{cx + w * 0.66} {cy + 6} {cx + w * 0.62} {cy - 2}"
        f'Q{cx} {cy - 6} {cx - w * 0.62} {cy - 2}Z" fill="{peak}" {_s(2.6, line)}/>'
    )
    o.append(
        f'<path d="M{cx - w * 0.42} {cy + 1}Q{cx - w * 0.46} {cy - h} {cx} {cy - h}'
        f'Q{cx + w * 0.46} {cy - h} {cx + w * 0.42} {cy + 1}Z" fill="{crown}" {_s(2.8, line)}/>'
    )
    check = line if mono else CHECK
    for i in range(1, 4):
        yy = cy - h * i / 4
        half = w * 0.42 * (1 - (i / 4) ** 2 * 0.55)
        o.append(
            f'<path d="M{cx - half:.1f} {yy:.1f}H{cx + half:.1f}" stroke="{check}" '
            f'stroke-width="1.6" stroke-opacity=".75"/>'
        )
    for dx in (-0.22, 0, 0.22):
        o.append(
            f'<path d="M{cx + w * dx:.1f} {cy - h + 3:.1f}V{cy:.1f}" stroke="{check}" '
            f'stroke-width="1.6" stroke-opacity=".75"/>'
        )
    o.append(
        f'<path d="M{cx - 2} {cy - h + 1}q-9 -8 -12 -2q2 7 12 2M{cx + 2} {cy - h + 1}'
        f'q9 -8 12 -2q-2 7 -12 2" fill="{crown}" {_s(2.2, line)}/>'
    )
    o.append(
        f'<circle cx="{cx}" cy="{cy - h + 1}" r="2.6" fill="{peak}" {_s(1.8, line)}/>'
    )
    o.append("</g>")
    return "".join(o)


def donut_detective(pose="idle", *, mono=False):
    """Drawn in a 128×128 box. `mono` is the white-on-ink mark used for icons."""
    if pose not in POSES:
        raise ValueError(f"pose must be one of {POSES}")
    line = PAPER if mono else INK
    fill = INK if mono else PAPER
    friend_fill = PAPER if mono else "#ffffff"
    gaze, tilt, lift = {
        "idle": ((-1, 0.2), -14, 0),
        "thinking": ((0.2, -1), -8, 0),
        "pointing": ((1, 0.3), -18, 0),
        "celebrating": ((0, 0), 10, 8),
    }[pose]
    o = [f'<path d="M10 107Q66 109 124 107" fill="none" {_s(3.2, line)}/>']
    o.append(_donut(44, 66, 30, 10, line, fill))
    o.append(_deerstalker(44, 38 - lift, 50, tilt, line, mono))
    o.append(_friend(line, friend_fill, INK, gaze, pose))
    if pose == "celebrating":
        o.append(
            f'<g fill="{HAT}" {_s(1.4, line)}>'
            '<path d="M118 16l2.6 6 6 2.6-6 2.6-2.6 6-2.6-6-6-2.6 6-2.6Z"/>'
            '<path d="M100 6l1.8 4 4 1.8-4 1.8-1.8 4-1.8-4-4-1.8 4-1.8Z"/></g>'
        )
    return "".join(o)


def placeholder(pose="idle"):
    """Neutral stand-in with the same footprint: a magnifier over a case folder."""
    return (
        f'<rect x="18" y="40" width="80" height="62" rx="6" fill="#e6c88d" {_s(2.6, INK)}/>'
        f'<path d="M18 48H54L60 40H98" fill="none" {_s(2.6, INK)}/>'
        f'<circle cx="72" cy="58" r="18" fill="#dff1f1" {_s(2.6, INK)}/>'
        f'<path d="M85 71 100 86" {_s(7, INK)}/>'
    )


def mascot_svg(pose="idle", *, size=128, mode=None, mono=False):
    mode = mode or mascot_mode()
    body = (
        placeholder(pose) if mode == "placeholder" else donut_detective(pose, mono=mono)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 128 128" role="img" aria-label="Detective Donut">{body}</svg>'
    )
