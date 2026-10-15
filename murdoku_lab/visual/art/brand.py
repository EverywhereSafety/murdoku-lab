"""Brand art: the snail detective and the casebook icons.

The Inspector is a snail in a deerstalker, after the Everywhere Safety snail mark: slow down,
look closely. It is original vector art built here (we do not redraw the ES mark itself), on a
128-unit grid with shared anchor points so every pose fits the same slot. `resources/brand.json`
switches between this draft and a neutral placeholder of identical size.
"""

import json
from pathlib import Path

INK = "#102725"
SHELL = "#1d5a4e"
SHELL_LIGHT = "#2f7a6a"
SPIRAL = "#f3e9d0"
BODY = "#a9c79f"
BODY_LIGHT = "#cfe2c4"
BODY_SHADE = "#86a97e"
HAT = "#c99a55"
HAT_DARK = "#8f6630"
HAT_CHECK = "#7b5526"
BRASS = "#c9a052"
BRASS_DARK = "#8a6427"
GLASS = "#dff1f1"

POSES = ("idle", "thinking", "pointing", "celebrating")
BRAND_PATH = Path(__file__).resolve().parents[2] / "resources" / "brand.json"


def mascot_mode():
    try:
        return json.loads(BRAND_PATH.read_text()).get("mascot", "draft-snail")
    except FileNotFoundError:
        return "draft-snail"


def _s(width=2.6):
    return f'stroke="{INK}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"'


def _shell(cx=78, cy=62, r=30):
    spiral = (
        f"M{cx + 2} {cy + 2}"
        f"m-3 0a4 4 0 1 1 6 3"
        f"a9 9 0 1 1-13-10"
        f"a15 15 0 1 1 20 21"
        f"a22 22 0 1 1-30-30"
    )
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SHELL}" {_s()}/>'
        f'<path d="M{cx - r + 7} {cy - 8}a{r - 6} {r - 6} 0 0 1 {r - 2} -{r - 12}" fill="none" stroke="{SHELL_LIGHT}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="{spiral}" fill="none" stroke="{SPIRAL}" stroke-width="3.4" stroke-linecap="round"/>'
    )


def _body(lift=0):
    return (
        f'<path d="M12 104Q8 94 18 90L30 {86 - lift}Q34 {70 - lift} 40 {58 - lift}Q46 {46 - lift} 56 {50 - lift}Q60 {62 - lift} 58 {80 - lift}L100 86Q116 90 112 100Q110 106 98 106H22Q12 106 12 104Z" fill="{BODY}" {_s()}/>'
        f'<path d="M20 100H96" stroke="{BODY_SHADE}" stroke-width="3" stroke-linecap="round"/>'
        f'<path d="M38 {82 - lift}Q42 {66 - lift} 50 {58 - lift}" fill="none" stroke="{BODY_LIGHT}" stroke-width="4" stroke-linecap="round"/>'
    )


def _eyes(base_x=44, base_y=50, mood="open", tilt=0, length=36):
    """Two eye stalks poking up through the hat; `mood` is open, happy or squint."""
    out = []
    for dx, lean in ((-8, -10 + tilt), (8, 6 + tilt)):
        x0, y0 = base_x + dx * 0.5, base_y
        x1, y1 = base_x + dx + lean * 0.6, base_y - length
        out.append(
            f'<path d="M{x0} {y0}Q{x0 + lean * 0.2} {y0 - 14} {x1} {y1}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M{x0} {y0}Q{x0 + lean * 0.2} {y0 - 14} {x1} {y1}" fill="none" stroke="{BODY}" stroke-width="3.6" stroke-linecap="round"/>'
        )
        if mood == "happy":
            out.append(
                f'<circle cx="{x1}" cy="{y1}" r="7.2" fill="#ffffff" {_s(2.2)}/>'
                f'<circle cx="{x1 + 1}" cy="{y1 + 0.5}" r="3.6" fill="{INK}"/>'
                f'<path d="M{x1 + 2.4} {y1 - 2.2}l.9 1.8 1.8.9-1.8.9-.9 1.8-.9-1.8-1.8-.9 1.8-.9Z" fill="#ffffff"/>'
            )
        elif mood == "squint":
            out.append(
                f'<circle cx="{x1}" cy="{y1}" r="7.2" fill="#ffffff" {_s(2.2)}/>'
                f'<path d="M{x1 - 4} {y1}h8" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
            )
        else:
            out.append(
                f'<circle cx="{x1}" cy="{y1}" r="7.2" fill="#ffffff" {_s(2.2)}/>'
                f'<circle cx="{x1 + 1.5}" cy="{y1 + 1}" r="3.4" fill="{INK}"/>'
                f'<circle cx="{x1 + 2.6}" cy="{y1 - 0.4}" r="1.1" fill="#ffffff"/>'
            )
    return "".join(out)


def _smile(x=48, y=64, open_mouth=False):
    if open_mouth:
        return f'<path d="M{x - 6} {y}q6 7 12 0Z" fill="#7a3b48" {_s(2)}/>'
    return f'<path d="M{x - 5} {y}q5 4 10 0" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>'


def _hat(x=45, y=40, tilt=0, lift=0):
    """A deerstalker: crown, front and back peaks, a bow on top, and a check pattern."""
    t = f'transform="rotate({tilt} {x} {y}) translate(0 {-lift})"'
    return (
        f"<g {t}>"
        f'<path d="M{x - 26} {y + 2}Q{x - 30} {y + 8} {x - 22} {y + 9}L{x + 22} {y + 9}Q{x + 32} {y + 8} {x + 26} {y + 2}Z" fill="{HAT_DARK}" {_s(2.2)}/>'
        f'<path d="M{x - 18} {y + 4}Q{x - 20} {y - 16} {x} {y - 18}Q{x + 20} {y - 16} {x + 18} {y + 4}Z" fill="{HAT}" {_s(2.4)}/>'
        f'<path d="M{x - 16} {y - 6}H{x + 16}M{x - 12} {y - 13}H{x + 12}M{x - 8} {y - 17}V{y + 3}M{x + 2} {y - 18}V{y + 4}M{x + 11} {y - 15}V{y + 4}" stroke="{HAT_CHECK}" stroke-width="1.6" stroke-opacity=".75"/>'
        f'<path d="M{x - 6} {y - 18}q-8 -8 -2 -10 4 2 6 8M{x + 6} {y - 18}q8 -8 2 -10 -4 2 -6 8" fill="{HAT}" {_s(1.8)}/>'
        f'<circle cx="{x}" cy="{y - 18}" r="2.6" fill="{HAT_DARK}" {_s(1.6)}/>'
        f"</g>"
    )


def _magnifier(x, y, r=11, angle=35, handle=18):
    import math

    a = math.radians(angle)
    hx, hy = x + (r + 1) * math.cos(a), y + (r + 1) * math.sin(a)
    ex, ey = x + (r + handle) * math.cos(a), y + (r + handle) * math.sin(a)
    return (
        f'<path d="M{hx:.1f} {hy:.1f}L{ex:.1f} {ey:.1f}" stroke="{INK}" stroke-width="7.5" stroke-linecap="round"/>'
        f'<path d="M{hx:.1f} {hy:.1f}L{ex:.1f} {ey:.1f}" stroke="{BRASS_DARK}" stroke-width="4" stroke-linecap="round"/>'
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GLASS}" fill-opacity=".85" stroke="{INK}" stroke-width="2.4"/>'
        f'<circle cx="{x}" cy="{y}" r="{r - 2.2}" fill="none" stroke="{BRASS}" stroke-width="3"/>'
        f'<path d="M{x - r * 0.5:.1f} {y - r * 0.2:.1f}q{r * 0.2:.1f} -{r * 0.45:.1f} {r * 0.6:.1f} -{r * 0.4:.1f}" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round"/>'
    )


def _shadow():
    return (
        '<ellipse cx="62" cy="108" rx="52" ry="7" fill="#102725" fill-opacity=".14"/>'
    )


def snail(pose="idle"):
    """The Inspector, drawn inside a 128×128 box."""
    if pose not in POSES:
        raise ValueError(f"pose must be one of {POSES}")
    parts = [_shadow()]
    if pose == "idle":
        parts += [
            _shell(),
            _body(),
            _magnifier(102, 84, r=9, angle=110, handle=12),
            _hat(45, 40, tilt=-6),
            _eyes(),
            _smile(),
        ]
    elif pose == "thinking":
        parts += [
            _shell(),
            _body(),
            _hat(43, 40, tilt=-14),
            _eyes(mood="squint", tilt=-4),
            _magnifier(70, 62, r=9, angle=60, handle=14),
            _smile(46, 65),
            '<g fill="#102725" fill-opacity=".55"><circle cx="20" cy="30" r="2.6"/><circle cx="13" cy="21" r="3.6"/><circle cx="10" cy="9" r="4.8"/></g>',
        ]
    elif pose == "pointing":
        parts += [
            _shell(),
            _body(lift=4),
            _hat(45, 36, tilt=-4),
            _eyes(base_y=46, tilt=2),
            # The magnifier held up to the right eye: a big magnified pupil behind the glass.
            f'<circle cx="57" cy="22" r="15" fill="{GLASS}" fill-opacity=".55" stroke="{INK}" stroke-width="2.6"/>'
            f'<circle cx="57" cy="22" r="12.5" fill="none" stroke="{BRASS}" stroke-width="3.2"/>'
            f'<circle cx="59" cy="23" r="6" fill="{INK}"/><circle cx="61" cy="20.5" r="2" fill="#ffffff"/>'
            f'<path d="M67 33L80 50" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
            f'<path d="M67 33L80 50" stroke="{BRASS_DARK}" stroke-width="4.4" stroke-linecap="round"/>',
            _smile(44, 61, open_mouth=True),
        ]
    else:  # celebrating
        parts += [
            _shell(),
            _body(lift=6),
            _hat(52, 6, tilt=18, lift=2),
            _eyes(base_y=44, mood="happy", length=30),
            _smile(44, 59, open_mouth=True),
            _magnifier(102, 82, r=9, angle=110, handle=12),
            f'<g fill="{BRASS}" {_s(1.4)}>'
            '<path d="M14 40l3 7 7 3-7 3-3 7-3-7-7-3 7-3Z"/>'
            '<path d="M104 18l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z"/>'
            '<path d="M86 6l1.6 3.6 3.6 1.6-3.6 1.6L86 16.4l-1.6-3.6-3.6-1.6 3.6-1.6Z"/>'
            "</g>",
        ]
    return "".join(parts)


def placeholder(pose="idle"):
    """Neutral stand-in with the same footprint: a magnifier over a case folder."""
    return (
        _shadow()
        + f'<rect x="18" y="40" width="80" height="62" rx="6" fill="#e6c88d" {_s()}/>'
        + f'<path d="M18 48H54L60 40H98" fill="none" {_s()}/>'
        + _magnifier(70, 56, r=20, angle=40, handle=26)
    )


def mascot_svg(pose="idle", *, size=128, mode=None):
    mode = mode or mascot_mode()
    body = snail(pose) if mode == "draft-snail" else placeholder(pose)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 128 128" role="img" aria-label="The Inspector">{body}</svg>'
    )
