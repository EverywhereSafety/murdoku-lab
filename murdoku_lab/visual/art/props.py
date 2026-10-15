"""Casebook props: one original drawing per formal kind, plus themed skins.

Drawers work in the prop's true footprint (pixels), so strokes stay even and multi-cell props
are drawn once, oriented to their footprint, instead of being stretched. A theme may swap the
drawing for a kind (its "skin") so that the picture matches the noun the clues use: in the manor,
`register` is called a writing desk and is drawn as one.
"""

INK = "#102725"
SHADOW = "#102725"

# Material palette shared by every drawing.
WOOD = "#b98153"
WOOD_LIGHT = "#d8a571"
WOOD_DARK = "#8a5a37"
CREAM = "#fbf3df"
LINEN = "#efe4c8"
SAGE = "#88a98c"
SAGE_DARK = "#5f8566"
LEAF = "#7aa36a"
LEAF_DARK = "#557f4f"
LEAF_LIGHT = "#a9c98f"
STONE = "#c9cbbf"
STONE_DARK = "#9ea395"
BRASS = "#c9a052"
BRASS_DARK = "#93702d"
RED = "#c4573f"
PLUM = "#8d4f6e"
TEAL = "#4f8f88"
NAVY = "#3d5a73"
TERRA = "#c98257"
WATER = "#86bcc8"
SAND = "#e8d39f"


def _s(stroke=INK, width=2):
    return f'stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"'


def rect(x, y, w, h, r, fill, stroke=INK, width=2, extra=""):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r:.1f}" fill="{fill}" {_s(stroke, width)} {extra}/>'


def ell(cx, cy, rx, ry, fill, stroke=INK, width=2, extra=""):
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" {_s(stroke, width)} {extra}/>'


def path(d, fill="none", stroke=INK, width=2, extra=""):
    return f'<path d="{d}" fill="{fill}" {_s(stroke, width)} {extra}/>'


def shadow_rect(x, y, w, h, r, dx=5, dy=6, opacity=0.16):
    return f'<rect x="{x + dx:.1f}" y="{y + dy:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r:.1f}" fill="{SHADOW}" fill-opacity="{opacity}"/>'


def shadow_ell(cx, cy, rx, ry, opacity=0.16):
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{SHADOW}" fill-opacity="{opacity}"/>'


def fit(body, w, h, size=100):
    """Centre a drawing designed in a size×size box inside a w×h footprint, uniformly scaled."""
    s = min(w, h) / size
    dx, dy = (w - size * s) / 2, (h - size * s) / 2
    return f'<g transform="translate({dx:.2f} {dy:.2f}) scale({s:.4f})">{body}</g>'


def rotated(draw, w, h):
    """Draw a portrait-designed prop in a landscape footprint by turning it a quarter."""
    inner = draw(h, w)
    return f'<g transform="translate({w:.1f} 0) rotate(90)">{inner}</g>'


# ------------------------------------------------------------------------------ standable
def bed(w, h):
    if w > h * 1.15:
        return rotated(bed, w, h)
    x, y, bw, bh = 6, 4, w - 12, h - 8
    o = [shadow_rect(x, y, bw, bh, 9)]
    o.append(rect(x, y, bw, bh, 9, WOOD))
    o.append(rect(x + 5, y + 5, bw - 10, bh - 10, 6, CREAM))
    pillow_h = min(22, bh * 0.22)
    if bw > 70:
        pw = (bw - 26) / 2
        o.append(rect(x + 10, y + 10, pw, pillow_h, 7, "#ffffff", width=1.6))
        o.append(rect(x + 16 + pw, y + 10, pw, pillow_h, 7, "#ffffff", width=1.6))
    else:
        o.append(rect(x + 10, y + 10, bw - 20, pillow_h, 7, "#ffffff", width=1.6))
    top = y + 16 + pillow_h
    o.append(rect(x + 5, top, bw - 10, y + bh - 5 - top, 5, TEAL))
    o.append(path(f"M{x + 5} {top + 9}H{x + bw - 5}", stroke=CREAM, width=2.4))
    o.append(path(f"M{x + 14} {top + 22}H{x + bw - 14}", stroke="#6fa7a0", width=1.4))
    return "".join(o)


def chair(w, h):
    body = (
        shadow_ell(54, 84, 30, 9)
        + path("M24 52 22 84M76 52 79 84", stroke=WOOD_DARK, width=5)
        + rect(18, 40, 64, 38, 12, WOOD)
        + rect(25, 44, 50, 26, 9, "#e0bf86")
        + path("M18 48V26Q18 15 30 15H70Q82 15 82 26V48", fill=WOOD_DARK)
        + path("M28 24H72", stroke="#e9cf9f", width=1.6)
        + rect(13, 40, 11, 30, 5, WOOD_DARK)
        + rect(76, 40, 11, 30, 5, WOOD_DARK)
    )
    return fit(body, w, h)


def wingback(w, h):
    body = (
        shadow_ell(54, 85, 32, 9)
        + path("M26 70 24 86M74 70 77 86", stroke=WOOD_DARK, width=5)
        + path("M16 58Q12 22 30 14H70Q88 22 84 58Z", fill=PLUM)
        + path("M26 22Q50 12 74 22", stroke="#b47a95", width=1.8)
        + rect(20, 48, 60, 28, 11, "#a76585")
        + rect(27, 50, 46, 18, 8, "#c48aa5")
        + path("M14 40Q8 52 14 70H26V44Z", fill="#7a4260")
        + path("M86 40Q92 52 86 70H74V44Z", fill="#7a4260")
    )
    return fit(body, w, h)


def chaise(w, h):
    if h > w * 1.15:
        return f'<g transform="translate(0 {h:.1f}) rotate(-90)">{chaise(h, w)}</g>'
    x, y, cw, ch = 4, h * 0.22, w - 8, h * 0.6
    o = [shadow_rect(x, y, cw, ch, 14)]
    o.append(rect(x, y, cw, ch, 14, TEAL))
    o.append(
        path(
            f"M{x} {y + ch * 0.55}Q{x - 2} {y - 10} {x + cw * 0.28} {y + 4}V{y + ch}",
            fill="#3f7d77",
        )
    )
    o.append(rect(x + cw * 0.3, y + 8, cw * 0.66, ch - 16, 10, "#6fb0a7", width=1.6))
    o.append(
        path(f"M{x + cw * 0.52} {y + 12}V{y + ch - 12}", stroke="#4f8f88", width=1.4)
    )
    return "".join(o)


def carpet(w, h):
    x, y, cw, ch = 3, 3, w - 6, h - 6
    o = [shadow_rect(x, y, cw, ch, 3, dx=3, dy=4, opacity=0.12)]
    fringe = []
    step = 7
    if cw >= ch:
        for xx in range(int(x + 6), int(x + cw - 4), step):
            fringe.append(f"M{xx} {y - 3}v6M{xx} {y + ch - 3}v6")
    else:
        for yy in range(int(y + 6), int(y + ch - 4), step):
            fringe.append(f"M{x - 3} {yy}h6M{x + cw - 3} {yy}h6")
    o.append(path("".join(fringe), stroke="#a8784f", width=1.5))
    o.append(rect(x, y, cw, ch, 3, RED))
    o.append(
        rect(x + 7, y + 7, cw - 14, ch - 14, 2, "#e09a6e", stroke="#f2cf96", width=2)
    )
    cx, cy = x + cw / 2, y + ch / 2
    r = min(cw, ch) * 0.24
    o.append(
        path(
            f"M{cx} {cy - r}L{cx + r} {cy}L{cx} {cy + r}L{cx - r} {cy}Z",
            fill="#f4d394",
            width=1.6,
        )
    )
    o.append(
        path(
            f"M{cx} {cy - r * 0.48}L{cx + r * 0.48} {cy}L{cx} {cy + r * 0.48}L{cx - r * 0.48} {cy}Z",
            fill=TEAL,
            width=1.4,
        )
    )
    for fx, fy in (
        (x + 16, y + 16),
        (x + cw - 16, y + 16),
        (x + 16, y + ch - 16),
        (x + cw - 16, y + ch - 16),
    ):
        o.append(
            f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="3.2" fill="#f4d394" stroke="none"/>'
        )
    return "".join(o)


def car(w, h):
    if h > w * 1.15:
        return f'<g transform="translate(0 {h:.1f}) rotate(-90)">{car(h, w)}</g>'
    x, y, cw, ch = 4, h * 0.14, w - 8, h * 0.72
    o = [shadow_rect(x, y, cw, ch, ch * 0.4)]
    o.append(rect(x, y, cw, ch, ch * 0.4, NAVY))
    o.append(
        rect(x + cw * 0.28, y + ch * 0.14, cw * 0.4, ch * 0.72, ch * 0.22, "#5e7d96")
    )
    o.append(
        path(
            f"M{x + cw * 0.26} {y + ch * 0.2}Q{x + cw * 0.2} {y + ch / 2} {x + cw * 0.26} {y + ch * 0.8}",
            stroke="#cfe1ea",
            width=4,
        )
    )
    o.append(
        path(
            f"M{x + cw * 0.7} {y + ch * 0.22}Q{x + cw * 0.75} {y + ch / 2} {x + cw * 0.7} {y + ch * 0.78}",
            stroke="#cfe1ea",
            width=3,
        )
    )
    for yy in (y + ch * 0.2, y + ch * 0.8):
        o.append(
            f'<circle cx="{x + cw - 6:.1f}" cy="{yy:.1f}" r="4" fill="#f7e7a7" stroke="{INK}" stroke-width="1.5"/>'
        )
    o.append(rect(x - 2, y + ch * 0.06, 9, ch * 0.88, 4, "#2b3f50", width=1.4))
    return "".join(o)


def golf_cart(w, h):
    if h > w * 1.15:
        return f'<g transform="translate(0 {h:.1f}) rotate(-90)">{golf_cart(h, w)}</g>'
    body = (
        shadow_rect(10, 26, 80, 54, 14)
        + rect(10, 26, 80, 54, 14, "#f2f0e6")
        + rect(18, 18, 46, 70, 8, "#7fb08f", extra='fill-opacity=".95"')
        + path("M20 30H62M20 76H62", stroke="#5f8f70", width=2)
        + rect(66, 34, 18, 38, 6, "#d6d2c0")
        + rect(72, 40, 8, 26, 3, "#b3492f", width=1.5)
        + path("M75 36v-8", stroke=INK, width=2)
        + f'<circle cx="16" cy="28" r="5" fill="{INK}"/><circle cx="16" cy="78" r="5" fill="{INK}"/><circle cx="84" cy="28" r="5" fill="{INK}"/><circle cx="84" cy="78" r="5" fill="{INK}"/>'
    )
    return fit(body, w, h)


def sand_prop(w, h):
    x, y, cw, ch = 6, 6, w - 12, h - 12
    o = [
        f'<path d="M{x + cw * .12} {y + ch * .5}Q{x} {y + ch * .1} {x + cw * .42} {y + ch * .12}Q{x + cw * .7} {y - 2} {x + cw * .9} {y + ch * .3}Q{x + cw + 4} {y + ch * .62} {x + cw * .72} {y + ch * .86}Q{x + cw * .4} {y + ch + 4} {x + cw * .14} {y + ch * .8}Q{x - 2} {y + ch * .68} {x + cw * .12} {y + ch * .5}Z" fill="{SAND}" {_s(BRASS_DARK, 3)}/>'
    ]
    for i in range(3):
        yy = y + ch * (0.36 + i * 0.16)
        o.append(
            path(
                f"M{x + cw * .22} {yy}q{cw * .14} -6 {cw * .28} 0t{cw * .28} 0",
                stroke="#c2a76a",
                width=1.6,
            )
        )
    return "".join(o)


def flag(w, h):
    body = (
        ell(48, 80, 26, 9, "#6f9b6d", stroke="none")
        + ell(46, 78, 11, 4.5, "#2f4a3e", width=1.5)
        + path("M47 20V78", width=3)
        + path("M49 21 80 31 49 42Z", fill=RED)
    )
    return fit(body, w, h)


def tee(w, h):
    body = (
        rect(14, 64, 72, 22, 9, "#7aa66d", stroke="none")
        + path("M24 70h52M24 79h52", stroke="#9bc08b", width=2)
        + path("M44 46h12l-4 26h-4Z", fill=WOOD_LIGHT)
        + f'<circle cx="50" cy="34" r="15" fill="#ffffff" stroke="{INK}" stroke-width="2"/>'
        + '<g fill="#c9ccc2"><circle cx="45" cy="29" r="1.8"/><circle cx="55" cy="29" r="1.8"/><circle cx="50" cy="37" r="1.8"/><circle cx="43" cy="38" r="1.6"/><circle cx="57" cy="38" r="1.6"/></g>'
    )
    return fit(body, w, h)


# ------------------------------------------------------------------------------- blocking
def table(w, h):
    x, y, tw, th = 5, 6, w - 10, h - 12
    o = [shadow_rect(x, y, tw, th, 12)]
    o.append(rect(x, y, tw, th, 12, WOOD))
    o.append(rect(x + 6, y + 6, tw - 12, th - 12, 8, WOOD_LIGHT, width=1.6))
    if tw >= th:
        for i in range(1, 3):
            yy = y + 6 + (th - 12) * i / 3
            o.append(
                path(f"M{x + 12} {yy:.1f}H{x + tw - 12}", stroke="#c08b5c", width=1.2)
            )
    else:
        for i in range(1, 3):
            xx = x + 6 + (tw - 12) * i / 3
            o.append(
                path(f"M{xx:.1f} {y + 12}V{y + th - 12}", stroke="#c08b5c", width=1.2)
            )
    cx, cy = x + tw * 0.42, y + th * 0.46
    o.append(ell(cx, cy, 11, 9, CREAM, width=1.6))
    o.append(ell(cx, cy, 5, 4, "#c9b98f", width=1.2))
    o.append(ell(x + tw * 0.68, y + th * 0.58, 6, 6, SAGE, width=1.5))
    return "".join(o)


def writing_desk(w, h):
    body = (
        shadow_rect(12, 22, 80, 62, 6)
        + rect(10, 20, 80, 62, 6, WOOD_DARK)
        + rect(16, 26, 68, 34, 4, "#3f6b5d")
        + rect(16, 64, 30, 14, 3, WOOD)
        + rect(54, 64, 30, 14, 3, WOOD)
        + f'<circle cx="31" cy="71" r="2" fill="{BRASS}"/><circle cx="69" cy="71" r="2" fill="{BRASS}"/>'
        + rect(26, 32, 26, 20, 2, CREAM, width=1.4)
        + path("M30 38h18M30 43h14", stroke="#a8a08a", width=1.2)
        + path("M60 30 72 52", stroke=INK, width=2)
        + path("M70 26q8 4 4 10", fill="#f3f0e6", width=1.4)
    )
    return fit(body, w, h)


def tv(w, h):
    body = (
        shadow_rect(14, 26, 72, 52, 9)
        + rect(14, 26, 72, 52, 9, "#6c7b74")
        + rect(21, 33, 46, 38, 6, "#bfd4cf")
        + path("M26 40q8-4 16 0", stroke="#e9f3f0", width=2)
        + f'<circle cx="76" cy="40" r="4" fill="{BRASS}" stroke="{INK}" stroke-width="1.4"/><circle cx="76" cy="55" r="4" fill="{BRASS}" stroke="{INK}" stroke-width="1.4"/>'
        + path("M36 26 28 12M58 26 68 12", width=2)
        + path("M30 78v8M70 78v8", width=4)
    )
    return fit(body, w, h)


def cabinet_radio(w, h):
    body = (
        shadow_rect(20, 14, 62, 72, 12)
        + path("M20 86V30Q20 14 50 14Q80 14 80 30V86Z", fill=WOOD_DARK)
        + path("M27 46V32Q27 21 50 21Q73 21 73 32V46Z", fill="#d8c08f", width=1.6)
        + path(
            "M33 28v16M41 24v20M50 22v22M59 24v20M67 28v16", stroke="#9c7b4c", width=1.4
        )
        + rect(27, 52, 46, 12, 3, "#f1e2b8", width=1.4)
        + path("M33 58h34", stroke="#b38a52", width=1.2)
        + path("M46 54v8", stroke=RED, width=1.6)
        + f'<circle cx="36" cy="74" r="4.5" fill="{BRASS}" stroke="{INK}" stroke-width="1.4"/><circle cx="64" cy="74" r="4.5" fill="{BRASS}" stroke="{INK}" stroke-width="1.4"/>'
    )
    return fit(body, w, h)


def shelf(w, h):
    vertical = h > w * 1.15
    x, y, sw, sh = 5, 5, w - 10, h - 10
    o = [shadow_rect(x, y, sw, sh, 4)]
    o.append(rect(x, y, sw, sh, 4, WOOD_DARK))
    o.append(rect(x + 5, y + 5, sw - 10, sh - 10, 2, "#d8b48a", width=1.4))
    colours = (
        "#88a98c",
        "#c9715a",
        "#d4b55e",
        "#6f93a8",
        "#a6739a",
        "#d99a62",
        "#7a9b74",
        "#c88a7a",
    )
    if vertical:
        shelves = max(2, int((sh - 10) // 38))
        for s in range(shelves):
            y0 = y + 5 + s * (sh - 10) / shelves
            y1 = y + 5 + (s + 1) * (sh - 10) / shelves
            o.append(path(f"M{x + 3} {y1:.1f}H{x + sw - 3}", width=3))
            bx = x + 9
            i = s * 3
            while bx < x + sw - 14:
                bw = 7 + (i * 5) % 6
                bh = (y1 - y0) * (0.62 + ((i * 7) % 4) * 0.08)
                o.append(
                    rect(
                        bx,
                        y1 - bh - 1.5,
                        bw,
                        bh,
                        1,
                        colours[i % len(colours)],
                        width=1.2,
                    )
                )
                bx += bw + 2
                i += 1
    else:
        rows = 2
        for s in range(rows):
            y1 = y + 5 + (s + 1) * (sh - 10) / rows
            y0 = y + 5 + s * (sh - 10) / rows
            if s < rows - 1:
                o.append(path(f"M{x + 3} {y1:.1f}H{x + sw - 3}", width=3))
            bx = x + 9
            i = s * 5
            while bx < x + sw - 14:
                bw = 7 + (i * 5) % 6
                bh = (y1 - y0) * (0.6 + ((i * 7) % 4) * 0.08)
                o.append(
                    rect(
                        bx,
                        y1 - bh - 1.5,
                        bw,
                        bh,
                        1,
                        colours[i % len(colours)],
                        width=1.2,
                    )
                )
                bx += bw + 2
                i += 1
    return "".join(o)


def plant(w, h):
    body = (
        shadow_ell(52, 86, 22, 7)
        + path("M32 60 37 86H63L68 60Z", fill=TERRA)
        + rect(29, 56, 42, 9, 3, "#dd9a6c")
        + path("M50 57Q22 52 18 30Q42 26 50 57Z", fill=LEAF)
        + path("M51 56Q56 24 80 22Q84 44 51 56Z", fill=LEAF_DARK)
        + path("M48 56Q36 70 14 58Q28 42 48 56Z", fill=LEAF_DARK)
        + path("M52 56Q70 40 86 52Q74 70 52 56Z", fill=LEAF)
        + path("M50 57Q48 36 44 20", stroke=LEAF_DARK, width=2)
    )
    return fit(body, w, h)


def fern(w, h):
    fronds = ""
    for angle in (-62, -34, -8, 18, 44, 68):
        fronds += f'<g transform="rotate({angle} 50 58)"><path d="M50 58V18" fill="none" stroke="{LEAF_DARK}" stroke-width="2"/>'
        for i, yy in enumerate(range(24, 56, 6)):
            span = 4 + i * 1.3
            fronds += f'<path d="M50 {yy}l-{span:.1f} -3M50 {yy}l{span:.1f} -3" stroke="{LEAF}" stroke-width="3" stroke-linecap="round"/>'
        fronds += "</g>"
    body = (
        shadow_ell(52, 88, 22, 7)
        + fronds
        + path("M34 64 38 88H62L66 64Z", fill="#c7d0c3")
        + rect(31, 59, 38, 8, 3, "#e3e8de")
    )
    return fit(body, w, h)


def tree(w, h):
    body = (
        shadow_ell(55, 84, 34, 11)
        + path("M44 60h12l3 24H41Z", fill=WOOD_DARK)
        + path(
            "M22 52Q8 38 26 28Q22 12 42 15Q53 2 68 17Q86 12 85 34Q99 48 82 60Q74 74 58 64Q36 76 28 62Q12 62 22 52Z",
            fill=LEAF,
        )
        + path("M30 40Q40 26 54 30M60 46Q70 38 78 42", stroke=LEAF_LIGHT, width=3)
        + path("M44 52Q52 58 64 52", stroke=LEAF_DARK, width=2)
    )
    return fit(body, w, h)


def potted_bay(w, h):
    body = (
        shadow_ell(52, 88, 22, 7)
        + path("M46 66V38", stroke=WOOD_DARK, width=4)
        + f'<circle cx="50" cy="32" r="24" fill="{LEAF_DARK}" stroke="{INK}" stroke-width="2"/>'
        + '<path d="M36 26q10-8 22-2M40 40q10 6 22-2" fill="none" stroke="#8fb47c" stroke-width="2.4" stroke-linecap="round"/>'
        + path("M34 66 38 88H62L66 66Z", fill="#c4c9bd")
        + rect(31, 61, 38, 8, 3, "#e1e5da")
    )
    return fit(body, w, h)


def flowers(w, h):
    blooms = ""
    for x, y, color in (
        (32, 32, "#c9667a"),
        (52, 24, "#e5b84e"),
        (70, 36, "#d98a6f"),
        (44, 44, "#e7d0e6"),
    ):
        blooms += (
            f'<g fill="{color}" stroke="{INK}" stroke-width="1.2"><circle cx="{x - 6}" cy="{y}" r="6"/>'
            f'<circle cx="{x + 6}" cy="{y}" r="6"/><circle cx="{x}" cy="{y - 6}" r="6"/><circle cx="{x}" cy="{y + 6}" r="6"/></g>'
            f'<circle cx="{x}" cy="{y}" r="3.6" fill="#f7da8a"/>'
        )
    body = (
        shadow_ell(52, 88, 20, 6)
        + path("M40 62 34 36M50 60 52 26M60 62 70 38", stroke=LEAF_DARK, width=3)
        + blooms
        + path("M33 60 38 88H62L67 60Z", fill=TERRA)
        + rect(30, 56, 40, 8, 3, "#dd9a6c")
    )
    return fit(body, w, h)


def lilies(w, h):
    blooms = ""
    for x, y, rot in ((34, 30, -30), (54, 22, 0), (70, 34, 30)):
        blooms += (
            f'<g transform="rotate({rot} {x} {y})"><path d="M{x} {y}l-9 -12 9 4 9 -4Z" fill="#fbf8f0" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>'
            f'<path d="M{x} {y}l-12 -2 12 -4 12 4Z" fill="#fff" stroke="{INK}" stroke-width="1.2"/>'
            f'<path d="M{x} {y}v-8" stroke="#d9a441" stroke-width="1.5"/></g>'
        )
    body = (
        shadow_ell(52, 88, 16, 5)
        + path("M44 66 36 34M50 64 54 24M56 66 68 36", stroke=LEAF_DARK, width=2.6)
        + blooms
        + path("M40 62Q34 76 42 88H58Q66 76 60 62Z", fill="#b9d5d2")
        + path("M42 66H58", stroke="#e8f4f2", width=2)
    )
    return fit(body, w, h)


def shrub(w, h):
    body = (
        shadow_ell(54, 82, 36, 10)
        + path(
            "M20 74Q6 64 17 50Q12 34 30 34Q32 18 48 26Q62 12 72 30Q90 30 84 48Q96 64 80 76Z",
            fill=LEAF,
        )
        + path(
            "M30 52q10-9 16 2m10-14q9 0 9 9m-12 16q9-8 15-1",
            stroke=LEAF_LIGHT,
            width=2.4,
        )
        + '<g fill="#e08a8f" stroke="#102725" stroke-width="1.2"><circle cx="34" cy="44" r="4.5"/><circle cx="66" cy="58" r="5"/><circle cx="56" cy="36" r="3.8"/></g>'
    )
    return fit(body, w, h)


def box_hedge(w, h):
    x, y, bw, bh = 8, 10, w - 16, h - 20
    o = [shadow_rect(x, y, bw, bh, 10)]
    o.append(rect(x, y, bw, bh, 10, LEAF_DARK))
    o.append(rect(x + 5, y + 5, bw - 10, bh - 10, 7, LEAF, width=1.4))
    for i in range(int(bw // 14)):
        xx = x + 10 + i * 14
        o.append(path(f"M{xx} {y + 12}q4 6 0 12", stroke=LEAF_LIGHT, width=2))
    return "".join(o)


def palm(w, h):
    body = (
        shadow_ell(54, 86, 26, 8)
        + path("M34 64 38 88H62L66 64Z", fill=TERRA)
        + path("M48 64 46 36", stroke=WOOD_DARK, width=5)
        + path("M47 36Q22 14 10 34Q28 28 47 36Z", fill=LEAF)
        + path("M47 36Q46 8 70 10Q66 24 47 36Z", fill=LEAF_DARK)
        + path("M47 36Q76 18 90 36Q70 34 47 36Z", fill=LEAF)
        + path("M47 36Q30 44 18 62Q36 54 47 36Z", fill=LEAF_DARK)
        + path("M47 36Q66 44 80 62Q60 56 47 36Z", fill=LEAF_DARK)
        + rect(31, 60, 38, 8, 3, "#dd9a6c")
    )
    return fit(body, w, h)


def crate(w, h):
    body = (
        shadow_rect(16, 18, 68, 68, 4)
        + rect(16, 18, 68, 68, 4, WOOD)
        + rect(16, 18, 68, 68, 4, "none")
        + path("M16 34H84M16 70H84", width=2)
        + path("M22 34 78 70M78 34 22 70", stroke=WOOD_DARK, width=4)
        + path("M22 34 78 70M78 34 22 70", stroke=WOOD_LIGHT, width=1.4)
        + '<g fill="#102725"><circle cx="21" cy="24" r="1.6"/><circle cx="79" cy="24" r="1.6"/><circle cx="21" cy="80" r="1.6"/><circle cx="79" cy="80" r="1.6"/></g>'
    )
    return fit(body, w, h)


def packing_crate(w, h):
    return crate(w, h)


def box(w, h):
    body = (
        shadow_rect(18, 26, 64, 58, 5)
        + rect(18, 26, 64, 58, 5, "#d6ab78")
        + path("M18 40H82", width=2)
        + rect(44, 26, 12, 58, 1, "#efe2c0", width=1.4)
        + path("M26 54h12M26 60h8", stroke="#9b7a51", width=1.6)
        + path("M60 66l6 6m0-6-6 6", stroke="#9b7a51", width=1.6)
    )
    return fit(body, w, h)


def hatbox(w, h):
    body = (
        shadow_ell(54, 66, 34, 24)
        + ell(50, 62, 34, 24, "#c7718a")
        + ell(50, 52, 34, 24, "#e9a6b7")
        + path("M18 52Q50 64 82 52", stroke="#ffffff", width=3)
        + path("M44 30 50 52 58 30", stroke="#7f2f4a", width=2.4)
        + path(
            "M44 30q-10-8-4-14 6 2 10 10M58 30q10-8 4-14-6 2-10 10",
            fill="#9d3b5c",
            width=1.6,
        )
    )
    return fit(body, w, h)


def register(w, h):
    body = (
        shadow_rect(16, 34, 68, 50, 6)
        + rect(16, 46, 68, 38, 6, "#7d8c86")
        + path("M24 46 30 22H70L76 46Z", fill="#9aaba4")
        + rect(36, 26, 28, 12, 2, "#cfe6b3", width=1.4)
        + path("M41 32h6M51 32h8", stroke="#4e6a3a", width=1.6)
        + '<g fill="#efe9d6" stroke="#102725" stroke-width="1.1">'
        + "".join(
            f'<rect x="{24 + c * 10}" y="{52 + r * 9}" width="7" height="6" rx="1.5"/>'
            for r in range(3)
            for c in range(4)
        )
        + "</g>"
        + rect(66, 52, 10, 24, 2, RED, width=1.4)
    )
    return fit(body, w, h)


def bear(w, h):
    body = (
        shadow_ell(52, 86, 24, 7)
        + f'<circle cx="32" cy="22" r="8" fill="#b17b4f" stroke="{INK}" stroke-width="2"/>'
        + f'<circle cx="68" cy="22" r="8" fill="#b17b4f" stroke="{INK}" stroke-width="2"/>'
        + ell(50, 66, 24, 20, "#b98256")
        + ell(50, 68, 13, 11, "#e2bf93", width=1.4)
        + f'<circle cx="50" cy="34" r="20" fill="#c68d5e" stroke="{INK}" stroke-width="2"/>'
        + ell(50, 40, 9, 7, "#e7c7a0", width=1.4)
        + f'<circle cx="43" cy="30" r="2.2" fill="{INK}"/><circle cx="57" cy="30" r="2.2" fill="{INK}"/>'
        + ell(50, 37, 3.4, 2.4, INK, width=0)
        + ell(26, 80, 9, 7, "#b98256")
        + ell(74, 80, 9, 7, "#b98256")
        + path("M40 52q10 6 20 0", stroke="#c64b4b", width=3)
    )
    return fit(body, w, h)


def bearskin(w, h):
    body = (
        shadow_ell(52, 56, 42, 30, opacity=0.1)
        + path(
            "M50 22Q60 14 68 20Q80 18 84 30Q96 30 92 42Q98 54 88 60Q92 74 78 76Q72 88 58 82Q50 90 42 82Q28 88 22 76Q8 74 12 60Q2 54 8 42Q4 30 16 30Q20 18 32 20Q40 14 50 22Z",
            fill="#e8dcc4",
        )
        + f'<circle cx="50" cy="30" r="12" fill="#f2e8d4" stroke="{INK}" stroke-width="2"/>'
        + f'<circle cx="45" cy="28" r="1.8" fill="{INK}"/><circle cx="55" cy="28" r="1.8" fill="{INK}"/>'
        + ell(50, 35, 3, 2, INK, width=0)
        + path("M34 52q16 10 32 0", stroke="#cdbf9f", width=2)
    )
    return fit(body, w, h)


def statue(w, h):
    body = (
        shadow_rect(26, 70, 52, 16, 3)
        + rect(24, 68, 52, 16, 3, STONE_DARK)
        + path("M34 68 40 46H60L66 68Z", fill=STONE)
        + f'<circle cx="50" cy="32" r="15" fill="{STONE}" stroke="{INK}" stroke-width="2"/>'
        + path("M44 29q3-3 6 0M52 29q3-3 6 0", stroke="#7f8579", width=1.4)
        + path("M47 40q3 2 6 0", stroke="#7f8579", width=1.4)
        + path("M36 26Q38 14 50 16Q62 14 64 26", stroke="#a9ae9f", width=3)
    )
    return fit(body, w, h)


def piano(w, h):
    body = (
        shadow_rect(14, 14, 74, 74, 18)
        + path(
            "M16 84V30Q16 12 40 12Q58 12 62 24Q66 40 80 46Q90 52 86 68L84 84Z",
            fill="#2f3b37",
        )
        + path(
            "M24 74V34Q24 22 40 22Q52 22 55 32Q58 46 74 54Q80 58 78 66L77 74Z",
            fill="#4b5a54",
            width=1.6,
        )
        + rect(16, 74, 68, 13, 2, "#fbf5e6", width=1.6)
        + path(
            "M23 74v8M30 74v8M37 74v8M44 74v8M51 74v8M58 74v8M65 74v8M72 74v8",
            stroke=INK,
            width=2.2,
        )
        + path("M40 22V60", stroke="#7d8b84", width=1.2)
    )
    return fit(body, w, h)


def boulder(w, h):
    body = (
        shadow_ell(54, 80, 36, 10)
        + path("M14 72 22 40 44 22 70 26 86 52 80 76 58 84H28Z", fill=STONE)
        + path("M44 22 40 54 58 84M40 54 86 52", stroke=STONE_DARK, width=1.6)
        + path("M26 46 34 36", stroke="#e6e8de", width=3)
    )
    return fit(body, w, h)


def millstone(w, h):
    body = (
        shadow_ell(54, 60, 38, 30)
        + ell(50, 54, 38, 30, STONE)
        + ell(50, 50, 38, 30, "#d8d9cd")
        + ell(50, 50, 9, 7, "#8d927f")
        + path(
            "M50 20V40M50 60V80M14 50H40M60 50H86M24 30 42 44M76 30 58 44M24 70 42 56M76 70 58 56",
            stroke="#a6aa9b",
            width=1.6,
        )
    )
    return fit(body, w, h)


def barrel(w, h):
    body = (
        shadow_ell(54, 84, 28, 8)
        + path("M26 20Q20 50 26 82H74Q80 50 74 20Z", fill=WOOD)
        + ell(50, 20, 24, 7, WOOD_LIGHT)
        + path("M24 34H76M23 68H77", stroke="#4f5b57", width=4)
        + path("M38 26Q35 50 38 80M62 26Q65 50 62 80", stroke=WOOD_DARK, width=1.4)
    )
    return fit(body, w, h)


def wine_cask(w, h):
    body = (
        shadow_ell(54, 84, 36, 8)
        + rect(16, 74, 68, 8, 2, WOOD_DARK)
        + ell(50, 50, 34, 30, WOOD)
        + ell(50, 50, 26, 23, WOOD_LIGHT, width=1.6)
        + ell(50, 50, 6, 5, "#7a2f3f", width=1.4)
        + path("M24 50h52M50 27v46", stroke="#c28d5d", width=1.2)
        + ell(50, 50, 34, 30, "none", stroke="#4f5b57", width=3)
    )
    return fit(body, w, h)


def water_prop(w, h):
    x, y, cw, ch = 4, 4, w - 8, h - 8
    o = [
        f'<path d="M{x + cw * .1} {y + ch * .55}Q{x} {y + ch * .12} {x + cw * .4} {y + ch * .1}Q{x + cw * .78} {y} {x + cw * .92} {y + ch * .34}Q{x + cw + 3} {y + ch * .7} {x + cw * .7} {y + ch * .9}Q{x + cw * .36} {y + ch + 3} {x + cw * .12} {y + ch * .8}Q{x - 3} {y + ch * .7} {x + cw * .1} {y + ch * .55}Z" fill="{WATER}" {_s("#3e6f7c", 3)}/>'
    ]
    o.append(
        path(
            f"M{x + cw * .25} {y + ch * .4}q{cw * .1} -6 {cw * .2} 0M{x + cw * .5} {y + ch * .65}q{cw * .1} -6 {cw * .2} 0",
            stroke="#e8f6f6",
            width=2.4,
        )
    )
    lx, ly = x + cw * 0.68, y + ch * 0.36
    o.append(
        f'<path d="M{lx:.1f} {ly:.1f}m-9 0a9 9 0 1 0 18 0l-9 0Z" fill="#7aa36a" stroke="{INK}" stroke-width="1.4"/>'
    )
    return "".join(o)


def void(w, h):
    x, y, cw, ch = 6, 6, w - 12, h - 12
    return rect(x, y, cw, ch, 8, "#2b3b37", stroke="#102725", width=2) + path(
        f"M{x + 10} {y + 10}L{x + cw - 10} {y + ch - 10}M{x + cw - 10} {y + 10}L{x + 10} {y + ch - 10}",
        stroke="#5d6f69",
        width=3,
    )


def generic(w, h):
    x, y, cw, ch = 10, 14, w - 20, h - 28
    return (
        shadow_rect(x, y, cw, ch, 10)
        + rect(x, y, cw, ch, 10, "#ddd0b6")
        + path(
            f"M{x + cw / 2 - 12} {y + ch / 2 - 7}l12 -7 12 7v14l-12 7-12-7Z",
            fill="#f3ead2",
            width=1.6,
        )
    )


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
    "writing_desk": writing_desk,
    "cabinet_radio": cabinet_radio,
    "fern": fern,
    "potted_bay": potted_bay,
    "lilies": lilies,
    "box_hedge": box_hedge,
    "hatbox": hatbox,
    "bearskin": bearskin,
    "millstone": millstone,
    "wine_cask": wine_cask,
    "packing_crate": packing_crate,
}

# Footprints drawn as one oriented piece when they are a filled rectangle; every other kind
# repeats per cell, which keeps a non-rectangular footprint honest about its exact cells.
STRETCH = {
    "table",
    "carpet",
    "bed",
    "car",
    "golf_cart",
    "water",
    "sand",
    "shelf",
    "generic",
    "void",
    "chaise",
    "box_hedge",
    "writing_desk",
}


def drawer(kind, skin=None):
    if skin and skin in SKINS:
        return SKINS[skin], skin
    return BASE.get(kind, generic), kind


def draw(kind, w, h, skin=None):
    fn, _ = drawer(kind, skin)
    return fn(w, h)


def stretches(kind, skin=None):
    return (skin or kind) in STRETCH or kind in STRETCH and not skin
