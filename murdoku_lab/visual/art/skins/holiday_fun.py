"""Holiday props: the Ides of March, Easter, April Fools' Day and Mother's Day.

Julius Caesar on stage, painted eggs in the garden, practical jokes backstage and breakfast in bed
at the country house. Each one is a single-cell landmark a holiday's season file can swap in.
"""

import math

from . import _kit as k
from ._kit import INK, f, grad, s, shadow

GRADIENTS = {
    "fun-marble": ("#fdfaf3", "#d9d2c3"),
    "fun-oxblood": ("#a2404c", "#6d2230"),
    "fun-rabbit": ("#e9e7dc", "#bcbaab"),
    "fun-wicker": ("#e3b878", "#b07f46"),
    "fun-toy-blue": ("#4fa9e6", "#2c74b6"),
    "fun-cushion": ("#ffb0c8", "#ec6f9a"),
    "fun-porcelain": ("#ffffff", "#dfe4e8"),
    "fun-mint": ("#c9eee1", "#94d3c0"),
}


def _leaf(x, y, angle, length, width, fill, line=1.1):
    """A pointed leaf growing from (x, y) in the direction `angle`."""
    return (
        f'<path d="M0 0Q{f(length / 2)} {f(-width)} {f(length)} 0Q{f(length / 2)} {f(width)} 0 0Z" '
        f'transform="translate({f(x)} {f(y)}) rotate({f(angle)})" fill="{fill}" '
        f'stroke="{INK}" stroke-width="{line}" stroke-linejoin="round"/>'
    )


def _ruff(cx, cy, rx, ry, points, fill, inner=0.8):
    """A zigzag ruff collar; whoever wears it draws their head over the top half."""
    corners = []
    for i in range(points * 2):
        a = math.pi * i / points
        r = 1 if i % 2 == 0 else inner
        corners.append(f"{f(cx + rx * r * math.cos(a))} {f(cy + ry * r * math.sin(a))}")
    return f'<path d="M{"L".join(corners)}Z" fill="{fill}" {s(1.4)}/>'


# An egg is two half ellipses, so a stripe can follow its outline without a clip path.
def _egg_path(cx, egg):
    top, widest, bottom, half = egg
    return (
        f"M{f(cx - half)} {f(widest)}A{f(half)} {f(widest - top)} 0 0 1 {f(cx + half)} {f(widest)}"
        f"A{f(half)} {f(bottom - widest)} 0 0 1 {f(cx - half)} {f(widest)}Z"
    )


def _egg_half(y, egg):
    top, widest, bottom, half = egg
    span = widest - top if y < widest else bottom - widest
    return half * math.sqrt(max(0.0, 1 - ((y - widest) / span) ** 2))


def _egg_band(cx, y0, y1, egg, fill, droop=2.0):
    """A painted stripe from y0 to y1, sagging as it wraps around the egg."""
    ys = [y0 + (y1 - y0) * i / 6 for i in range(7)]
    d = [
        f"M{f(cx - _egg_half(y0, egg))} {f(y0)}"
        f"Q{f(cx)} {f(y0 + 2 * droop)} {f(cx + _egg_half(y0, egg))} {f(y0)}"
    ]
    d += [f"L{f(cx + _egg_half(y, egg))} {f(y)}" for y in ys[1:]]
    d.append(f"Q{f(cx)} {f(y1 + 2 * droop)} {f(cx - _egg_half(y1, egg))} {f(y1)}")
    d += [f"L{f(cx - _egg_half(y, egg))} {f(y)}" for y in reversed(ys[:-1])]
    return f'<path d="{"".join(d)}Z" fill="{fill}"/>'


def _egg_dots(cx, y, egg, count, r, fill, droop=2.0, reach=0.74):
    """A row of dots around the egg, narrowing towards its edges."""
    half = _egg_half(y, egg)
    out = []
    for i in range(count):
        t = -reach + 2 * reach * i / (count - 1) if count > 1 else 0
        out.append(
            f'<ellipse cx="{f(cx + half * t)}" cy="{f(y + droop * (1 - t * t))}" '
            f'rx="{f(r * math.sqrt(1 - t * t * 0.7))}" ry="{f(r)}" fill="{fill}"/>'
        )
    return "".join(out)


def _egg_zigzag(cx, y, egg, teeth, rise, colour, width, droop=2.0):
    """A zigzag painted around the egg."""
    half = _egg_half(y, egg) - 0.5
    corners = []
    for i in range(teeth * 2 + 1):
        t = -1 + i / teeth
        lift = rise if i % 2 else -rise
        corners.append(f"{f(cx + half * t)} {f(y + droop * (1 - t * t) + lift)}")
    return (
        f'<path d="M{"L".join(corners)}" fill="none" stroke="{colour}" stroke-width="{width}" '
        f'stroke-linejoin="round"/>'
    )


def _ruffle(x, y, r, lobes, fill, line=0.0):
    """A ring of rounded, slightly uneven lobes: the frilled edge of a carnation's petals."""

    def rim(radius, a):
        return f"{f(x + radius * math.cos(a))} {f(y + 0.94 * radius * math.sin(a))}"

    radii = [r * (0.84 + 0.05 * ((i * 7) % 3)) for i in range(lobes)]
    d = [f"M{rim(radii[0], 0)}"]
    for i in range(lobes):
        bulge = max(radii[i], radii[(i + 1) % lobes]) * 1.24
        d.append(
            f"Q{rim(bulge, 2 * math.pi * (i + 0.5) / lobes)} "
            f"{rim(radii[(i + 1) % lobes], 2 * math.pi * (i + 1) / lobes)}"
        )
    stroke = s(line) if line else ""
    return f'<path d="{"".join(d)}Z" fill="{fill}" {stroke}/>'


def _spring(x, bottom, turns, pitch, rx, ry):
    """A coil spring rising from (x, bottom): far half-turns behind, near half-turns in front."""
    far, near = [], []
    for half in range(turns * 2):
        corners = []
        for j in range(9):
            t = math.pi * (half + j / 8)
            corners.append(
                f"{f(x + rx * math.cos(t))} {f(bottom - pitch * t / (2 * math.pi) + ry * math.sin(t))}"
            )
        (near if half % 2 == 0 else far).append(f'M{"L".join(corners)}')
    return k.outlined("".join(far), "#8d979d", 2.4, ink_width=4.8) + k.outlined(
        "".join(near), "#e3e8eb", 2.8, ink_width=5.4
    )


def caesar_bust(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx, base, 30, 8)]
    # Plinth: a dark foot and shaft that make the white marble stand out.
    o.append(
        f'<rect x="{f(cx - 26)}" y="{base - 9}" width="52" height="10" rx="2" fill="{grad("fun-oxblood")}" {s()}/>'
        f'<rect x="{f(cx - 20)}" y="{base - 25}" width="40" height="17" fill="{grad("fun-oxblood")}" {s()}/>'
        f'<rect x="{f(cx - 25)}" y="{base - 31}" width="50" height="7" rx="2" fill="{grad("fun-oxblood")}" {s()}/>'
        f'<rect x="{f(cx - 14)}" y="{base - 21}" width="28" height="9" fill="none" stroke="#e2c27a" stroke-width="1.8"/>'
    )
    # Socle, then a chest cut away in the classical sweep.
    o.append(
        f'<path d="M{f(cx - 6)} {base - 37}L{f(cx - 11)} {base - 30}H{f(cx + 11)}L{f(cx + 6)} {base - 37}Z" fill="{grad("fun-marble")}" {s(1.8)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 8)} {base - 61}Q{f(cx - 25)} {base - 60} {f(cx - 30)} {base - 50}Q{f(cx - 32)} {base - 43} {f(cx - 25)} {base - 41}'
        f"Q{f(cx - 13)} {base - 39} {f(cx - 8)} {base - 34}H{f(cx + 8)}Q{f(cx + 13)} {base - 39} {f(cx + 25)} {base - 41}"
        f'Q{f(cx + 32)} {base - 43} {f(cx + 30)} {base - 50}Q{f(cx + 25)} {base - 60} {f(cx + 8)} {base - 61}Z" fill="{grad("fun-marble")}" {s()}/>'
    )
    # The toga, gathered at one shoulder.
    o.append(
        f'<path d="M{f(cx - 28)} {base - 48}Q{f(cx - 8)} {base - 42} {f(cx + 17)} {base - 57}M{f(cx - 17)} {base - 41}Q{f(cx + 4)} {base - 38} {f(cx + 25)} {base - 51}" '
        f'fill="none" stroke="#a9a292" stroke-width="1.8" stroke-linecap="round"/>'
    )
    o.append(
        f'<circle cx="{f(cx + 19)}" cy="{base - 55}" r="3" fill="{grad("brass")}" {s(1.2)}/>'
    )
    # Neck, ears and head.
    o.append(
        f'<path d="M{f(cx - 8)} {base - 68}V{base - 58}Q{f(cx)} {base - 53} {f(cx + 8)} {base - 58}V{base - 68}Z" fill="{grad("fun-marble")}" {s()}/>'
    )
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 16.5)}" cy="{base - 77}" rx="3.2" ry="5.5" fill="#efeadd" {s(1.6)}/>'
        )
    o.append(
        f'<path d="M{f(cx)} {base - 103}C{f(cx + 13)} {base - 103} {f(cx + 17)} {base - 93} {f(cx + 16.5)} {base - 79}C{f(cx + 16)} {base - 69} {f(cx + 8)} {base - 59} {f(cx)} {base - 59}'
        f'C{f(cx - 8)} {base - 59} {f(cx - 16)} {base - 69} {f(cx - 16.5)} {base - 79}C{f(cx - 17)} {base - 93} {f(cx - 13)} {base - 103} {f(cx)} {base - 103}Z" fill="{grad("fun-marble")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx + 8)} {base - 61}C{f(cx + 13)} {base - 67} {f(cx + 16)} {base - 73} {f(cx + 16)} {base - 81}C{f(cx + 11)} {base - 73} {f(cx + 9)} {base - 67} {f(cx + 8)} {base - 61}Z" fill="#a9a292" fill-opacity=".45"/>'
    )
    # A carved, blank-eyed face, with cropped curls above and below the crown.
    o.append(
        f'<path d="M{f(cx - 10)} {base - 80}q4 -2.6 8 -.4M{f(cx + 2)} {f(base - 80.4)}q4 -2.2 8 .4M{f(cx)} {base - 80}L{f(cx - 2.2)} {base - 70}q2.2 1.8 4.4 0" '
        f'fill="none" stroke="#7f7a6c" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M{f(cx - 5)} {base - 65}q5 1.8 10 0" fill="none" stroke="#7f7a6c" stroke-width="1.6" stroke-linecap="round"/>'
        f'<ellipse cx="{f(cx - 6)}" cy="{base - 77}" rx="2.6" ry="1.4" fill="#a39c8c"/><ellipse cx="{f(cx + 6)}" cy="{base - 77}" rx="2.6" ry="1.4" fill="#a39c8c"/>'
        f'<path d="M{f(cx - 8)} {base - 99}q3 -1.8 6 -.4M{f(cx + 1)} {f(base - 99.6)}q3 -1.6 6 .2M{f(cx - 10)} {base - 87}q2 2.4 4.4 1M{f(cx - 3)} {f(base - 87.6)}q2 2.4 4.4 1M{f(cx + 4.6)} {base - 87}q2 2.4 4.4 1" '
        f'fill="none" stroke="#a39c8c" stroke-width="1.5" stroke-linecap="round"/>'
    )
    # The laurel crown: two branches of slim leaves following the hairline to meet over the brow.
    light, dark = "#7cbb5a", "#4f9139"
    branch = ((18, 82), (15.5, 86.5), (12, 90), (8, 92.5), (4, 94), (0.5, 94.5))
    for side in (-1, 1):
        stem = "L".join(f"{f(cx + side * x)} {base - y}" for x, y in branch)
        o.append(
            f'<path d="M{stem}" fill="none" stroke="#2f5f27" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    for side in (-1, 1):
        for i, ((x0, y0), (x1, y1)) in enumerate(zip(branch, branch[1:])):
            heading = math.degrees(math.atan2(y0 - y1, x0 - x1))
            for turn, colour, length in (
                (-34, dark if i % 2 else light, 11),
                (30, light if i % 2 else dark, 10),
            ):
                angle = heading + turn
                o.append(
                    _leaf(
                        cx + side * x0,
                        base - y0,
                        angle if side < 0 else 180 - angle,
                        length,
                        5.6,
                        colour,
                        0.9,
                    )
                )
    return "".join(o)


def roman_pillar(w, h):
    cx, base = w / 2, h - 12
    front = [
        (-17.5, 86),
        (-12, 76),
        (-6, 82),
        (-1, 66),
        (4, 72),
        (9, 57),
        (13, 62),
        (18, 50),
    ]
    back = [(-17.5, 86), (-13, 97), (-6, 92), (0, 94), (6, 83), (11, 79), (18, 50)]

    def edge(x):
        for (x0, y0), (x1, y1) in zip(front, front[1:]):
            if x0 <= x <= x1:
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return front[-1][1]

    def points(pts):
        return "L".join(f"{f(cx + x)} {f(base - y)}" for x, y in pts)

    o = [shadow(cx, base, 34, 8)]
    # The shaft, with the rough inside of the break above its jagged front edge.
    o.append(
        f'<path d="M{f(cx - 20)} {base - 14}L{points(back)}L{f(cx + 20)} {base - 14}Z" fill="{grad("fun-marble")}" {s()}/>'
    )
    o.append(
        f'<path d="M{points(back)}L{points(reversed(front))}Z" fill="#b3ac9b" {s(1.6)}/>'
    )
    o.append(
        f'<path d="M{f(cx - 9)} {base - 87}l3 -2M{f(cx - 2)} {base - 80}l4 -3M{f(cx + 7)} {base - 72}l3 -3" stroke="#8c8574" stroke-width="1.6" stroke-linecap="round"/>'
    )
    # Fluting, then the shade on the side away from the light.
    for x in (-13.5, -7, 0, 7, 13.5):
        o.append(
            f'<path d="M{f(cx + x)} {f(base - edge(x) + 4)}V{base - 18}" stroke="#b7b09f" stroke-width="3.4" stroke-linecap="round"/>'
        )
    o.append(
        f'<path d="M{f(cx + 10)} {f(base - edge(10))}L{points([(13, 62), (18, 50)])}L{f(cx + 20)} {base - 14}H{f(cx + 10)}Z" fill="#8f8877" fill-opacity=".28"/>'
    )
    o.append(
        k.highlight(f"M{f(cx - 16.5)} {base - 74}L{f(cx - 18)} {base - 22}", 0.9, 2)
    )
    o.append(
        f'<path d="M{points(front)}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>'
    )
    # Attic base.
    o.append(
        f'<rect x="{f(cx - 24)}" y="{base - 20}" width="48" height="10" rx="5" fill="{grad("fun-marble")}" {s()}/>'
        f'<rect x="{f(cx - 30)}" y="{base - 11}" width="60" height="12" rx="2" fill="{grad("stone")}" {s()}/>'
    )
    # What fell off.
    o.append(
        f'<path d="M{f(cx + 17)} {base + 3}L{f(cx + 20)} {base - 7}L{f(cx + 31)} {base - 11}L{f(cx + 41)} {base - 4}L{f(cx + 38)} {base + 4}Z" fill="{grad("fun-marble")}" {s()}/>'
        f'<path d="M{f(cx + 25)} {base - 6}l-1 8M{f(cx + 32)} {base - 7}l-1 9" stroke="#b7b09f" stroke-width="2.2" stroke-linecap="round"/>'
        f'<path d="M{f(cx - 41)} {base + 3}l2 -7 7 -3 5 6 -3 4Z" fill="#e7e1d3" {s(1.8)}/>'
    )
    return "".join(o)


def laurel_wreath(w, h):
    cx, base = w / 2, h - 12
    ring_y, ring_r = base - 60, 27
    golds = ("#e4c04a", "#8bb04a", "#d1b845", "#a4ba4c")
    wood = "#8a5a33"
    o = [shadow(cx, base, 24, 7)]
    # A small turned stand.
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{base - 3}" rx="21" ry="5.5" fill="{grad("walnut")}" {s()}/>'
        f'<path d="M{f(cx - 5)} {base - 22}Q{f(cx - 3)} {base - 12} {f(cx - 9)} {base - 5}H{f(cx + 9)}Q{f(cx + 3)} {base - 12} {f(cx + 5)} {base - 22}Z" fill="{grad("walnut-top")}" {s(1.8)}/>'
    )
    # Each branch: a stem with two rows of slim leaves, open at the top as a victor's wreath is.
    for side in (-1, 1):
        stem = "".join(
            ("M" if i == 0 else "L")
            + f"{f(cx + side * ring_r * math.sin(math.radians(a)))} {f(ring_y + ring_r * math.cos(math.radians(a)))}"
            for i, a in enumerate(range(0, 162, 10))
        )
        o.append(
            f'<path d="{stem}" fill="none" stroke="#6b6f2c" stroke-width="3" stroke-linecap="round"/>'
        )
        for i, a in enumerate(range(10, 150, 14)):
            rad = math.radians(a)
            x = cx + side * ring_r * math.sin(rad)
            y = ring_y + ring_r * math.cos(rad)
            heading = math.degrees(math.atan2(-math.sin(rad), side * math.cos(rad)))
            o.append(
                _leaf(x, y, heading - side * 32, 16, 7, golds[(i + 1) % len(golds)])
            )
            o.append(_leaf(x, y, heading + side * 36, 18, 8, golds[i % len(golds)]))
        rad = math.radians(150)
        o.append(
            _leaf(
                cx + side * ring_r * math.sin(rad),
                ring_y + ring_r * math.cos(rad),
                math.degrees(math.atan2(-math.sin(rad), side * math.cos(rad))),
                17,
                7,
                golds[0],
            )
        )
    # The wooden cradle it rests in, and an imperial purple tie where the branches cross.
    o.append(
        k.outlined(
            f"M{f(cx - 21)} {base - 32}Q{f(cx)} {base - 11} {f(cx + 21)} {base - 32}",
            wood,
            4,
            ink_width=7.4,
        )
    )
    y = ring_y + ring_r
    o.append(
        f'<path d="M{f(cx - 2)} {f(y)}L{f(cx - 15)} {f(y + 9)}L{f(cx - 8)} {f(y + 10)}L{f(cx + 1)} {f(y + 3)}Z" fill="#7a4196" {s(1.4)}/>'
        f'<path d="M{f(cx + 2)} {f(y)}L{f(cx + 15)} {f(y + 9)}L{f(cx + 8)} {f(y + 10)}L{f(cx - 1)} {f(y + 3)}Z" fill="#65347f" {s(1.4)}/>'
        f'<rect x="{f(cx - 5)}" y="{f(y - 4)}" width="10" height="8" rx="2.5" fill="#8d50aa" {s(1.4)}/>'
    )
    return "".join(o)


def stone_rabbit(w, h):
    cx, base = w / 2, h - 12
    stone = grad("fun-rabbit")
    o = [shadow(cx, base, 34, 8)]
    # A low garden slab with moss on it.
    o.append(
        f'<path d="M{f(cx - 34)} {base - 6}V{base - 1}Q{f(cx)} {base + 8} {f(cx + 34)} {base - 1}V{base - 6}Z" fill="#94927f" {s()}/>'
        f'<ellipse cx="{f(cx)}" cy="{base - 6}" rx="34" ry="7.5" fill="#c6c4b3" {s()}/>'
    )
    # Ears, the first thing anyone reads.
    for side, tilt in ((-1, -7), (1, 9)):
        ex = cx + side * 8.5
        o.append(
            f'<g transform="rotate({tilt} {f(ex)} {base - 60})">'
            f'<path d="M{f(ex - 5.5)} {base - 58}C{f(ex - 10.5)} {base - 80} {f(ex - 7)} {base - 106} {f(ex)} {base - 108}C{f(ex + 7)} {base - 106} {f(ex + 10.5)} {base - 80} {f(ex + 5.5)} {base - 58}Z" fill="{stone}" {s()}/>'
            f'<path d="M{f(ex - 2.4)} {base - 63}C{f(ex - 5.5)} {base - 80} {f(ex - 3.4)} {base - 97} {f(ex)} {base - 100}C{f(ex + 3.4)} {base - 97} {f(ex + 5.5)} {base - 80} {f(ex + 2.4)} {base - 63}Z" fill="#a09e8e"/>'
            f"</g>"
        )
    # Haunches, body and hind feet.
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 19)}" cy="{base - 22}" rx="13" ry="15" fill="{stone}" {s()}/>'
        )
    o.append(
        f'<path d="M{f(cx - 12)} {base - 50}C{f(cx - 19)} {base - 40} {f(cx - 21)} {base - 20} {f(cx - 13)} {base - 9}H{f(cx + 13)}C{f(cx + 21)} {base - 20} {f(cx + 19)} {base - 40} {f(cx + 12)} {base - 50}Z" fill="{stone}" {s()}/>'
    )
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 20)}" cy="{base - 9}" rx="11.5" ry="5" fill="#d9d7ca" {s()}/>'
        )
    # Forepaws carved out of the chest, with a nick for the toes.
    for side in (-1, 1):
        px = cx + side * 5.8
        o.append(
            f'<path d="M{f(px - 4.4)} {base - 31}Q{f(px - 5)} {base - 20} {f(px - 4.4)} {base - 12}Q{f(px)} {base - 7} {f(px + 4.4)} {base - 12}Q{f(px + 5)} {base - 20} {f(px + 4.4)} {base - 31}" fill="#dcdacd" {s(1.8)}/>'
            f'<path d="M{f(px)} {base - 13}v-3" stroke="#8f8d7e" stroke-width="1.3" stroke-linecap="round"/>'
        )
    # Head and carved face.
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{base - 54}" rx="17" ry="14" fill="{stone}" {s()}/>'
    )
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(cx + side * 7.5)}" cy="{f(base - 56.5)}" rx="2.4" ry="2.9" fill="#4f4d43"/>'
        )
    o.append(
        f'<path d="M{f(cx - 3)} {base - 50}h6l-3 3.4Z" fill="#6f6d60" {s(1)}/>'
        f'<path d="M{f(cx)} {f(base - 46.6)}q-1 3.4 -5 2.4M{f(cx)} {f(base - 46.6)}q1 3.4 5 2.4" fill="none" stroke="#6f6d60" stroke-width="1.4" stroke-linecap="round"/>'
    )
    # Weathering: a crack, lichen flecks and a bloom of moss.
    o.append(
        f'<path d="M{f(cx + 25)} {base - 33}l-3 4 2 3 -3 5" fill="none" stroke="#8f8d7e" stroke-width="1.2" stroke-linecap="round"/>'
    )
    for x, height in ((-22, 26), (-13, 62), (13, 43), (-7, 96), (-27, 18)):
        o.append(
            f'<circle cx="{f(cx + x)}" cy="{base - height}" r="1" fill="#96947f"/>'
        )
    o.append(
        f'<path d="M{f(cx - 34)} {base - 5}q4 -6 11 -3q5 -3 8 3q-2 7 -19 4Z" fill="#7f9e4f" {s(1)}/>'
        f'<path d="M{f(cx + 17)} {base - 3}q5 -5 10 -2q5 -1 6 3q-6 5 -16 -1Z" fill="#8caa58" {s(1)}/>'
    )
    o.append(
        k.highlight(
            f"M{f(cx - 12)} {base - 61}Q{f(cx - 7)} {base - 65} {f(cx - 2)} {base - 66}",
            0.7,
            2.2,
        )
    )
    return "".join(o)


def _easter_egg(x, y, half, rot, colour, pattern, accent):
    """A small painted egg standing at (x, y), turned a little."""
    top, widest = y - half * 1.62, y - half * 0.2
    egg = (top, widest, y + half * 0.98, half)
    o = [f'<g transform="rotate({rot} {f(x)} {f(y)})">']
    o.append(f'<path d="{_egg_path(x, egg)}" fill="{colour}"/>')
    if pattern == "band":
        o.append(_egg_band(x, y - half * 0.42, y + half * 0.08, egg, accent, droop=1.4))
    elif pattern == "zigzag":
        o.append(_egg_zigzag(x, y - half * 0.14, egg, 3, half * 0.26, accent, 2.8, 1.2))
    elif pattern == "dots":
        o.append(_egg_dots(x, y - half * 0.62, egg, 2, half * 0.19, accent, 1, 0.42))
        o.append(_egg_dots(x, y - half * 0.04, egg, 3, half * 0.19, accent, 1, 0.56))
    elif pattern == "stripes":
        for y0 in (top + half * 0.56, y - half * 0.3, y + half * 0.28):
            o.append(_egg_band(x, y0, y0 + half * 0.24, egg, accent, droop=1.2))
    o.append(f'<path d="{_egg_path(x, egg)}" fill="none" {s(1.8)}/>')
    o.append(
        k.highlight(
            f"M{f(x - half * 0.56)} {f(widest - half * 0.34)}Q{f(x - half * 0.4)} {f(widest - half * 0.82)} {f(x - half * 0.08)} {f(widest - half * 1.08)}",
            0.65,
            2,
        )
    )
    o.append("</g>")
    return "".join(o)


def egg_basket(w, h):
    cx, base = w / 2, h - 12
    o = [shadow(cx, base, 34, 8)]
    # Handle, behind the eggs.
    handle = f"M{f(cx - 34)} {base - 34}C{f(cx - 38)} {base - 98} {f(cx + 38)} {base - 98} {f(cx + 34)} {base - 34}"
    o.append(k.outlined(handle, "#c9975a", 5.4, ink_width=8.6))
    o.append(
        f'<path d="{handle}" fill="none" stroke="#8f6433" stroke-width="1.6" stroke-dasharray="3.5 5"/>'
    )
    # Eggs, back row first.
    for args in (
        (cx - 13, base - 45, 11.5, -10, "#55b8e0", "stripes", "#fdfaf0"),
        (cx + 14, base - 46, 11.5, 12, "#f6cf45", "zigzag", "#e4572e"),
        (cx - 27, base - 35, 11, -18, "#ef6f9f", "dots", "#fff3c8"),
        (cx, base - 36, 12, 2, "#9a77d6", "band", "#ffd84d"),
        (cx + 27, base - 35, 11, 20, "#5cc98c", "dots", "#fdfaf0"),
    ):
        o.append(_easter_egg(*args))
    # Easter grass spilling over the rim.
    grass = "".join(
        f"M{f(cx + x)} {base - 28}l{f(x * 0.1 - 2)} -9" for x in range(-30, 34, 6)
    )
    o.append(
        f'<path d="{grass}" fill="none" stroke="#6faf52" stroke-width="2.4" stroke-linecap="round"/>'
    )
    # Woven body: the rows of the weave first, its outline over them.
    body = f"M{f(cx - 36)} {base - 34}Q{f(cx - 34)} {base - 6} {f(cx - 22)} {base}H{f(cx + 22)}Q{f(cx + 34)} {base - 6} {f(cx + 36)} {base - 34}Q{f(cx)} {base - 22} {f(cx - 36)} {base - 34}Z"
    o.append(f'<path d="{body}" fill="{grad("fun-wicker")}"/>')
    for i, height in enumerate((6, 12, 18, 24)):
        half = 24 + 11 * height / 26
        o.append(
            f'<path d="M{f(cx - half)} {base - height - 2}Q{f(cx)} {base - height + 8} {f(cx + half)} {base - height - 2}" fill="none" stroke="#8f6433" '
            f'stroke-width="2.2" stroke-dasharray="7 4" stroke-dashoffset="{5 * (i % 2)}"/>'
        )
    o.append(f'<path d="{body}" fill="none" {s()}/>')
    # Braided rim.
    rim = f"M{f(cx - 37)} {base - 33}Q{f(cx)} {base - 19} {f(cx + 37)} {base - 33}"
    o.append(k.outlined(rim, "#dcae6e", 5.6, ink_width=8.8))
    o.append(
        f'<path d="{rim}" fill="none" stroke="#8f6433" stroke-width="1.6" stroke-dasharray="3 4.5"/>'
    )
    return "".join(o)


def painted_egg(w, h):
    cx, base = w / 2, h - 12
    top = base - 94
    egg = (top, base - 46, base - 18, 30)
    magenta, turquoise, violet, gold = "#d9468a", "#3fb9b1", "#5f3fa0", "#ffd84d"
    o = [shadow(cx, base, 26, 8)]
    # Foot and stem of the stand, then the egg, then the cup that holds it.
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{base - 3}" rx="21" ry="5.5" fill="{grad("brass")}" {s()}/>'
        f'<path d="M{f(cx - 5)} {base - 14}Q{f(cx - 3)} {base - 8} {f(cx - 8)} {base - 4}H{f(cx + 8)}Q{f(cx + 3)} {base - 8} {f(cx + 5)} {base - 14}Z" fill="{grad("brass")}" {s(1.8)}/>'
    )
    o.append(f'<path d="{_egg_path(cx, egg)}" fill="{turquoise}"/>')
    o.append(_egg_band(cx, top, base - 80, egg, magenta))
    o.append(_egg_band(cx, base - 80, base - 75, egg, gold))
    o.append(_egg_band(cx, base - 58, base - 39, egg, violet))
    o.append(_egg_band(cx, base - 58, base - 54, egg, gold))
    o.append(_egg_band(cx, base - 39, base - 35, egg, gold))
    o.append(_egg_dots(cx, base - 69, egg, 5, 3.4, "#fffdf4", reach=0.72))
    o.append(_egg_zigzag(cx, base - 49, egg, 5, 4.6, "#ff9ccb", 3.4))
    o.append(_egg_dots(cx, base - 30, egg, 5, 2.8, magenta, reach=0.7))
    o.append(f'<path d="{_egg_path(cx, egg)}" fill="none" {s()}/>')
    o.append(
        k.highlight(
            f"M{f(cx - 21)} {base - 62}Q{f(cx - 20)} {base - 78} {f(cx - 9)} {base - 88}",
            0.65,
            3,
        )
    )
    o.append(
        f'<path d="M{f(cx - 21)} {base - 28}Q{f(cx - 19)} {base - 13} {f(cx - 6)} {base - 12}H{f(cx + 6)}Q{f(cx + 19)} {base - 13} {f(cx + 21)} {base - 28}Q{f(cx)} {base - 18} {f(cx - 21)} {base - 28}Z" fill="{grad("brass")}" {s()}/>'
    )
    return "".join(o)


def jester(w, h):
    cx, base = w / 2, h - 12
    red, yellow = "#d9362f", "#f6c93f"
    o = [shadow(cx, base, 38, 8)]
    # Sat on the floor like a rag doll: legs out in front, each in the other half's colour.
    o.append(
        k.outlined(
            f"M{f(cx - 5)} {base - 12}Q{f(cx - 20)} {base - 12} {f(cx - 31)} {base - 5}",
            yellow,
            9.4,
            ink_width=13.4,
        )
    )
    o.append(
        k.outlined(
            f"M{f(cx + 5)} {base - 12}Q{f(cx + 20)} {base - 12} {f(cx + 31)} {base - 5}",
            red,
            9.4,
            ink_width=13.4,
        )
    )
    for side, colour in ((-1, red), (1, yellow)):
        o.append(
            f'<path d="M{f(cx + side * 27)} {base - 9}Q{f(cx + side * 39)} {base - 10} {f(cx + side * 42)} {base - 20}Q{f(cx + side * 47)} {base - 4} {f(cx + side * 30)} {base + 2}Q{f(cx + side * 27)} {base - 3} {f(cx + side * 27)} {base - 9}Z" fill="{colour}" {s()}/>'
            f'<circle cx="{f(cx + side * 42)}" cy="{base - 21}" r="3.2" fill="{grad("brass")}" {s(1.2)}/>'
        )
    # A motley tunic, split down the middle, its zigzag hem falling over the thighs.
    o.append(
        f'<path d="M{f(cx)} {base - 50}H{f(cx - 12)}Q{f(cx - 20)} {base - 35} {f(cx - 22)} {base - 18}l5.5 7 5.5 -6 5.5 7 5.5 -6Z" fill="{red}" {s()}/>'
        f'<path d="M{f(cx)} {base - 50}H{f(cx + 12)}Q{f(cx + 20)} {base - 35} {f(cx + 22)} {base - 18}l-5.5 7 -5.5 -6 -5.5 7 -5.5 -6Z" fill="{yellow}" {s()}/>'
    )
    for height in (39, 28):
        o.append(
            f'<circle cx="{f(cx)}" cy="{base - height}" r="2.8" fill="#fbf6e8" {s(1.2)}/>'
        )
    # Limp arms and white gloves.
    o.append(
        k.outlined(
            f"M{f(cx - 12)} {base - 45}Q{f(cx - 28)} {base - 42} {f(cx - 29)} {base - 27}",
            yellow,
            6,
            ink_width=9.6,
        )
    )
    o.append(
        k.outlined(
            f"M{f(cx + 12)} {base - 45}Q{f(cx + 28)} {base - 42} {f(cx + 29)} {base - 27}",
            red,
            6,
            ink_width=9.6,
        )
    )
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(cx + side * 29)}" cy="{base - 23}" r="5" fill="#fbf6e8" {s(1.6)}/>'
        )
    o.append(_ruff(cx, base - 50, 20, 7.5, 9, "#fbf6e8"))
    # The head flops to one side: a painted wooden face under a three-horned cap.
    o.append(f'<g transform="rotate(-7 {f(cx)} {base - 50})">')
    o.append(f'<circle cx="{f(cx)}" cy="{base - 65}" r="14.5" fill="#f7e6d2" {s()}/>')
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(cx + side * 5.8)}" cy="{base - 67}" r="3.2" fill="#ffffff" {s(1.2)}/>'
            f'<circle cx="{f(cx + side * 5.8)}" cy="{f(base - 66.6)}" r="1.6" fill="{INK}"/>'
            f'<circle cx="{f(cx + side * 9)}" cy="{base - 60}" r="2.8" fill="#ee8a8a" fill-opacity=".8"/>'
        )
    # The hinged jaw of a ventriloquist's dummy, two cuts from the corners of its grin.
    o.append(
        f'<circle cx="{f(cx)}" cy="{f(base - 62.5)}" r="2.2" fill="{red}" {s(1)}/>'
        f'<path d="M{f(cx - 7)} {f(base - 58.5)}Q{f(cx)} {base - 54} {f(cx + 7)} {f(base - 58.5)}" fill="none" stroke="#a82626" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M{f(cx - 7)} {base - 58}L{f(cx - 6.4)} {f(base - 52.6)}M{f(cx + 7)} {base - 58}L{f(cx + 6.4)} {f(base - 52.6)}" stroke="{INK}" stroke-width="1.1" stroke-linecap="round"/>'
    )
    for side in (-1, 1):
        o.append(
            f'<path d="M{f(cx + side * 4)} {base - 83}C{f(cx + side * 12)} {base - 102} {f(cx + side * 31)} {base - 107} {f(cx + side * 39)} {base - 85}'
            f'C{f(cx + side * 30)} {base - 94} {f(cx + side * 22)} {base - 87} {f(cx + side * 15.5)} {base - 72}Z" fill="{red}" {s()}/>'
        )
    o.append(
        f'<path d="M{f(cx - 9)} {base - 80}C{f(cx - 9)} {base - 94} {f(cx - 6)} {base - 106} {f(cx + 3)} {base - 114}C{f(cx + 7)} {base - 104} {f(cx + 9)} {base - 93} {f(cx + 9)} {base - 80}Z" fill="{yellow}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 15.5)} {base - 70}Q{f(cx)} {base - 79} {f(cx + 15.5)} {base - 70}L{f(cx + 15)} {base - 76}Q{f(cx)} {base - 86} {f(cx - 15)} {base - 76}Z" fill="{yellow}" {s()}/>'
    )
    for x, height in ((-39, 83), (39, 83), (3, 116)):
        o.append(
            f'<circle cx="{f(cx + x)}" cy="{base - height}" r="4.8" fill="{grad("brass")}" {s(1.5)}/>'
            f'<path d="M{f(cx + x - 2.6)} {base - height + 1}H{f(cx + x + 2.6)}" stroke="{INK}" stroke-width="1.2" stroke-linecap="round"/>'
        )
    o.append("</g>")
    return "".join(o)


def jack_in_box(w, h):
    cx, base = w / 2, h - 12
    x0, x1 = cx - 30, cx + 20
    top, front = base - 45, base - 36
    o = [shadow(cx + 3, base, 36, 8)]
    # The lid thrown back on its hinge, behind everything.
    o.append(
        f'<path d="M{f(x0 + 8)} {top}L{f(x0 + 13)} {top - 22}H{f(x1 + 13)}L{f(x1 + 8)} {top}Z" fill="#ffd84d" {s()}/>'
        f'<path d="M{f(x0 + 13)} {top - 16}H{f(x1 + 12)}" stroke="#d9362f" stroke-width="3"/>'
    )
    o.append(
        k.block(
            x0,
            x1,
            top,
            front,
            base,
            lid="#2a1c26",
            face=grad("fun-toy-blue"),
            side="#22598c",
            depth=9,
        )
    )
    # Face of the box: a big star and bright edging.
    o.append(
        f'<path d="M{f(x0 + 1)} {front + 4}H{f(x1 - 1)}M{f(x0 + 1)} {base - 4}H{f(x1 - 1)}" stroke="#ffd84d" stroke-width="3"/>'
    )
    o.append(k.star((x0 + x1) / 2, base - 18, 11, "#ffd84d", line=1.4))
    # The crank on the side.
    o.append(
        k.outlined(f"M{f(x1 + 4)} {base - 20}H{f(x1 + 15)}V{base - 30}", "#c4ccd2", 2.6)
    )
    o.append(
        f'<circle cx="{f(x1 + 15)}" cy="{base - 33}" r="4" fill="#d9362f" {s(1.5)}/>'
    )
    # The spring.
    sx = (x0 + x1) / 2 + 4
    o.append(_spring(sx, base - 40, 5, 6, 12, 3.6))
    # The clown: a ruff, a white face, orange tufts, a red nose and a small pointed hat.
    hx = sx + 3
    o.append(f'<g transform="rotate(8 {f(hx)} {base - 70})">')
    for side in (-1, 1):
        o.append(
            f'<circle cx="{f(hx + side * 15)}" cy="{base - 84}" r="7" fill="#f08a2c" {s(1.8)}/>'
        )
    o.append(_ruff(hx, base - 69, 19, 7.5, 9, "#d9362f", inner=0.74))
    o.append(f'<circle cx="{f(hx)}" cy="{base - 84}" r="14" fill="#fff8ee" {s()}/>')
    for side in (-1, 1):
        o.append(
            f'<ellipse cx="{f(hx + side * 5.6)}" cy="{base - 87}" rx="1.9" ry="2.5" fill="{INK}"/>'
        )
    o.append(
        f'<path d="M{f(hx - 9)} {base - 79}Q{f(hx)} {base - 69} {f(hx + 9)} {base - 79}Q{f(hx)} {base - 75} {f(hx - 9)} {base - 79}Z" fill="#d9362f" {s(1.4)}/>'
        f'<circle cx="{f(hx)}" cy="{f(base - 82.5)}" r="3.6" fill="#d9362f" {s(1.3)}/>'
    )
    o.append(
        f'<path d="M{f(hx - 10)} {base - 95}L{f(hx)} {base - 116}L{f(hx + 10)} {base - 95}Q{f(hx)} {base - 91} {f(hx - 10)} {base - 95}Z" fill="#2f8f83" {s()}/>'
        f'<circle cx="{f(hx)}" cy="{base - 117}" r="4" fill="#ffd84d" {s(1.4)}/>'
    )
    o.append("</g>")
    return "".join(o)


def whoopee_cushion(w, h):
    cx, base = w / 2, h - 12
    x, cy = cx - 6, base - 38
    bladder = (
        f"M{f(x - 36)} {f(cy + 1)}C{f(x - 36)} {f(cy - 14)} {f(x - 21)} {f(cy - 24)} {f(x)} {f(cy - 24)}"
        f"C{f(x + 22)} {f(cy - 24)} {f(x + 37)} {f(cy - 14)} {f(x + 36)} {f(cy + 2)}"
        f"C{f(x + 35)} {f(cy + 13)} {f(x + 19)} {f(cy + 20)} {f(x + 1)} {f(cy + 20)}"
        f"C{f(x - 21)} {f(cy + 20)} {f(x - 36)} {f(cy + 13)} {f(x - 36)} {f(cy + 1)}Z"
    )
    o = [shadow(x + 2, base - 8, 38, 9)]
    # A soft, flat bladder: its underside first, then the stubby neck with its open mouth.
    o.append(f'<path d="{bladder}" transform="translate(0 6)" fill="#c9477a" {s()}/>')
    o.append(
        f'<g transform="translate({f(x + 16)} {f(cy + 13)}) rotate(-36)">'
        f'<path d="M-12 -6Q-8 8 -8.5 13L-13 21Q0 26 13 21L8.5 13Q8 8 12 -6Z" fill="#df5688" {s()}/>'
        f'<ellipse cx="0" cy="21.5" rx="13" ry="4.8" fill="#ff9dbb" {s()}/>'
        f'<ellipse cx="0" cy="21.8" rx="8" ry="2.5" fill="#6d1f40"/>'
        f"</g>"
    )
    o.append(f'<path d="{bladder}" fill="{grad("fun-cushion")}" {s()}/>')
    # The crimped seam round the edge, creases running to the neck, and a shine.
    o.append(
        f'<ellipse cx="{f(x)}" cy="{f(cy - 2)}" rx="31.5" ry="18.2" fill="none" stroke="#c9477a" stroke-width="1.8" stroke-dasharray="2.6 3.2"/>'
    )
    o.append(
        f'<path d="M{f(x + 8)} {f(cy + 12)}Q{f(x + 10)} {f(cy + 7)} {f(x + 7)} {f(cy + 2)}M{f(x + 17)} {f(cy + 9)}Q{f(x + 18)} {f(cy + 4)} {f(x + 15)} {f(cy)}" fill="none" stroke="#c9477a" stroke-width="1.8" stroke-linecap="round"/>'
    )
    o.append(
        k.highlight(
            f"M{f(x - 22)} {f(cy - 4)}Q{f(x - 17)} {f(cy - 13)} {f(x - 5)} {f(cy - 15)}",
            0.85,
            4,
        )
    )
    o.append(
        f'<circle cx="{f(x - 24)}" cy="{f(cy + 2)}" r="2" fill="#ffffff" fill-opacity=".85"/>'
    )
    # A little puff of air out of the mouth.
    px, py = cx + 38, base - 7
    puff = ((1, -6, 4.2), (4.6, -0.5, 3.4), (-2, 0, 4.2))
    o.append(
        "".join(
            f'<circle cx="{f(px + dx)}" cy="{f(py + dy)}" r="{r}" fill="#fbf6ea" {s(1.5)}/>'
            for dx, dy, r in puff
        )
        + "".join(
            f'<circle cx="{f(px + dx)}" cy="{f(py + dy)}" r="{f(r - 0.75)}" fill="#fbf6ea"/>'
            for dx, dy, r in puff
        )
    )
    return "".join(o)


def _carnation(x, y, r, petal, deep):
    """A ruffled carnation head: frilled rings getting deeper towards the middle."""
    ticks = "".join(
        f"M{f(x + r * 0.62 * math.cos(math.radians(a)))} {f(y + r * 0.58 * math.sin(math.radians(a)))}"
        f"L{f(x + r * 0.86 * math.cos(math.radians(a)))} {f(y + r * 0.8 * math.sin(math.radians(a)))}"
        for a in range(10, 370, 36)
    )
    return (
        _ruffle(x, y, r, 13, petal, 1.5)
        + f'<path d="{ticks}" stroke="{deep}" stroke-width="1.2" stroke-linecap="round"/>'
        + _ruffle(x, y, r * 0.66, 10, deep)
        + _ruffle(x - 0.4, y - 0.4, r * 0.5, 9, petal)
        + _ruffle(x, y, r * 0.26, 6, deep)
    )


def carnations(w, h):
    cx, base = w / 2, h - 12
    green, dark = "#6d9c6d", "#4d7c55"
    o = [shadow(cx, base, 24, 7)]
    heads = (
        (-25, 76, 13, "#f39ab9", "#dd5f90"),
        (25, 79, 13, "#f39ab9", "#dd5f90"),
        (0, 97, 14.5, "#f7b4cb", "#e56e98"),
        (-11, 59, 12, "#f7b4cb", "#e56e98"),
        (13, 60, 12, "#ee85aa", "#cf4f82"),
    )
    mouth = base - 40
    # Stems, narrow blue-green leaves and the long calyx below every head.
    for x, height, *_ in heads:
        o.append(
            f'<path d="M{f(cx + x * 0.14)} {mouth}Q{f(cx + x * 0.5)} {mouth - 12} {f(cx + x)} {base - height}" fill="none" stroke="{green}" stroke-width="2.6" stroke-linecap="round"/>'
        )
    for x, height, angle in (
        (-10, 47, -165),
        (10, 47, -15),
        (-14, 58, -125),
        (15, 62, -50),
    ):
        o.append(_leaf(cx + x, base - height, angle, 18, 4.6, green, 0.9))
    for x, height, r, *_ in heads:
        length = math.hypot(x * 0.5, base - height - mouth + 12) or 1
        dx, dy = -x * 0.5 / length, (mouth - 12 - (base - height)) / length
        bx, by = cx + x + dx * (r - 1), base - height + dy * (r - 1)
        ex, ey = bx + dx * 9, by + dy * 9
        o.append(
            f'<path d="M{f(bx + dy * 4.6)} {f(by - dx * 4.6)}L{f(ex + dy * 2.2)} {f(ey - dx * 2.2)}L{f(ex - dy * 2.2)} {f(ey + dx * 2.2)}L{f(bx - dy * 4.6)} {f(by + dx * 4.6)}Z" fill="{dark}" {s(1.1)}/>'
        )
    for x, height, r, petal, deep in heads:
        o.append(_carnation(cx + x, base - height, r, petal, deep))
    # A slim white vase with a flared lip and a pink band.
    o.append(
        f'<path d="M{f(cx - 11)} {base - 42}Q{f(cx - 8)} {base - 30} {f(cx - 14)} {base - 18}Q{f(cx - 18)} {base - 6} {f(cx - 10)} {base}H{f(cx + 10)}Q{f(cx + 18)} {base - 6} {f(cx + 14)} {base - 18}Q{f(cx + 8)} {base - 30} {f(cx + 11)} {base - 42}Z" fill="{grad("fun-porcelain")}" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 14.6)} {base - 15}Q{f(cx)} {base - 10} {f(cx + 14.6)} {base - 15}" fill="none" stroke="#e77aa2" stroke-width="3.4"/>'
    )
    o.append(
        f'<ellipse cx="{f(cx)}" cy="{base - 42}" rx="13" ry="4" fill="#f4f6f8" {s(1.8)}/>'
        f'<ellipse cx="{f(cx)}" cy="{f(base - 41.6)}" rx="8" ry="2" fill="#7a8a84"/>'
    )
    o.append(
        k.highlight(
            f"M{f(cx - 7)} {base - 34}Q{f(cx - 7)} {base - 26} {f(cx - 10)} {base - 20}",
            0.9,
            2.2,
        )
    )
    return "".join(o)


def gift_hatbox(w, h):
    cx, base = w / 2, h - 12
    ribbon, ribbon_dark = "#e8506f", "#b8324f"
    top = base - 48
    drum = f"M{f(cx - 32)} {top + 6}V{base - 10}Q{f(cx)} {base + 7} {f(cx + 32)} {base - 10}V{top + 6}Z"
    o = [shadow(cx, base, 34, 8)]
    # The drum, with pale stripes that close up towards its sides.
    o.append(f'<path d="{drum}" fill="{grad("fun-mint")}"/>')
    for a in (-68, -44, -22, 22, 44, 68):
        sin_a, cos_a = math.sin(math.radians(a)), math.cos(math.radians(a))
        t = (sin_a + 1) / 2
        o.append(
            f'<path d="M{f(cx + 32 * sin_a)} {top + 10}V{f(base - 10 + 34 * t * (1 - t))}" stroke="#f3fbf7" stroke-width="{f(5 * cos_a + 1)}"/>'
        )
    o.append(f'<path d="{drum}" fill="none" {s()}/>')
    # The ribbon down its front.
    o.append(
        f'<path d="M{f(cx - 5.5)} {top + 18}V{f(base - 1.7)}Q{f(cx)} {f(base - 1.3)} {f(cx + 5.5)} {f(base - 1.7)}V{top + 18}Z" fill="{ribbon}" {s(1.6)}/>'
    )
    # The lid: a skirt, its top and the ribbon crossing it.
    o.append(
        f'<path d="M{f(cx - 35)} {top + 2}V{top + 10}Q{f(cx)} {top + 27} {f(cx + 35)} {top + 10}V{top + 2}Z" fill="#a6dcca" {s()}/>'
        f'<rect x="{f(cx - 5.5)}" y="{top + 14}" width="11" height="10" fill="{ribbon}"/>'
        f'<path d="M{f(cx - 5.5)} {top + 15}V{top + 25}M{f(cx + 5.5)} {top + 15}V{top + 25}" stroke="{INK}" stroke-width="1.6"/>'
        f'<ellipse cx="{f(cx)}" cy="{top + 2}" rx="35" ry="13.5" fill="#dcf5ec" {s()}/>'
    )
    o.append(
        f'<path d="M{f(cx - 5)} {top - 11}L{f(cx - 5.5)} {f(top + 15.5)}H{f(cx + 5.5)}L{f(cx + 5)} {top - 11}Z" fill="{ribbon}" {s(1.4)}/>'
    )
    # A big bow with two long tails.
    for side in (-1, 1):
        o.append(
            f'<path d="M{f(cx + side * 2)} {top - 4}Q{f(cx + side * 12)} {top + 2} {f(cx + side * 21)} {top + 10}L{f(cx + side * 15)} {top + 11}L{f(cx + side * 14)} {top + 17}Q{f(cx + side * 6)} {top + 7} {f(cx - side * 2)} {top}Z" fill="{ribbon}" {s(1.6)}/>'
        )
    for side in (-1, 1):
        o.append(
            f'<path d="M{f(cx)} {top - 7}C{f(cx + side * 8)} {top - 30} {f(cx + side * 31)} {top - 36} {f(cx + side * 31)} {top - 18}C{f(cx + side * 31)} {top - 4} {f(cx + side * 10)} {top - 1} {f(cx)} {top - 7}Z" fill="{ribbon}" {s()}/>'
            f'<path d="M{f(cx + side * 6)} {top - 8}C{f(cx + side * 12)} {top - 21} {f(cx + side * 24)} {top - 26} {f(cx + side * 25)} {top - 17}C{f(cx + side * 25)} {top - 9} {f(cx + side * 13)} {top - 6} {f(cx + side * 6)} {top - 8}Z" fill="{ribbon_dark}"/>'
        )
    o.append(
        f'<rect x="{f(cx - 6.5)}" y="{top - 14}" width="13" height="13" rx="4" fill="{ribbon}" {s()}/>'
    )
    o.append(
        k.highlight(
            f"M{f(cx - 22)} {top - 24}Q{f(cx - 15)} {top - 28} {f(cx - 9)} {top - 20}",
            0.6,
            2.2,
        )
    )
    return "".join(o)


def breakfast_tray(w, h):
    cx, base = w / 2, h - 12
    deck = base + 3
    x0, x1 = cx - 37, cx + 37
    top, front = deck - 50, deck - 20
    wood_dark = "#8a5a33"
    o = [shadow(cx, base, 38, 7)]
    # Four stubby legs: the back pair set in, the front pair splayed.
    for x in (cx - 23, cx + 23):
        o.append(k.outlined(f"M{f(x)} {front}V{base - 4}", "#6f4a2c", 3.4))
    for x, tilt in ((x0 + 7, -3), (x1 - 7, 3)):
        o.append(
            k.outlined(f"M{f(x)} {front + 4}L{f(x + tilt)} {base}", wood_dark, 4.6)
        )
    # Carrying handles at the ends, then the tray: a rimmed top and its front edge.
    for side in (-1, 1):
        o.append(
            k.outlined(
                f"M{f(cx + side * 37)} {top + 9}Q{f(cx + side * 46)} {top + 12} {f(cx + side * 37)} {top + 22}",
                "#c9975a",
                3.2,
            )
        )
    o.append(
        f'<rect x="{f(x0)}" y="{top}" width="74" height="{front - top}" rx="5" fill="{grad("wood")}" {s()}/>'
        f'<rect x="{f(x0 + 5)}" y="{top + 5}" width="64" height="{front - top - 10}" rx="3" fill="#f8efdc" stroke="#a8723f" stroke-width="1.6"/>'
        f'<rect x="{f(x0)}" y="{front - 3}" width="74" height="11" rx="4" fill="{grad("wood-front")}" {s()}/>'
    )
    # A small flower in a bud vase at the back.
    vx = cx + 23
    o.append(
        f'<path d="M{f(vx)} {deck - 53}Q{f(vx + 1)} {deck - 68} {f(vx - 1)} {deck - 76}" fill="none" stroke="#4f8452" stroke-width="2.6" stroke-linecap="round"/>'
    )
    o.append(_leaf(vx + 0.5, deck - 62, -30, 11, 6, "#5d9c58", 1))
    for a in range(0, 360, 60):
        o.append(
            f'<circle cx="{f(vx - 1 + 6.4 * math.cos(math.radians(a)))}" cy="{f(deck - 80 + 6.4 * math.sin(math.radians(a)))}" r="5" fill="#ef6f9f" {s(1.3)}/>'
        )
    o.append(
        f'<circle cx="{f(vx - 1)}" cy="{deck - 80}" r="3.6" fill="#ffd84d" {s(1.1)}/>'
    )
    o.append(
        f'<path d="M{f(vx - 3)} {deck - 57}Q{f(vx - 2)} {deck - 49} {f(vx - 7)} {deck - 44}Q{f(vx - 8)} {deck - 39} {f(vx - 5)} {deck - 37}H{f(vx + 5)}Q{f(vx + 8)} {deck - 39} {f(vx + 7)} {deck - 44}Q{f(vx + 2)} {deck - 49} {f(vx + 3)} {deck - 57}Z" fill="{grad("fun-porcelain")}" {s(1.8)}/>'
    )
    # Teacup on its saucer, handle to the left, steaming.
    tx = cx - 15
    o.append(
        f'<ellipse cx="{f(tx)}" cy="{deck - 28}" rx="17" ry="6.5" fill="#fdfdfb" {s(1.8)}/>'
    )
    o.append(
        k.outlined(
            f"M{f(tx - 11)} {deck - 45}q-9 0 -8 7 q1 5 9 4",
            "#fdfdfb",
            2.4,
            ink_width=5,
        )
    )
    o.append(
        f'<path d="M{f(tx - 13)} {deck - 48}Q{f(tx - 12)} {deck - 30} {f(tx)} {deck - 29}Q{f(tx + 12)} {deck - 30} {f(tx + 13)} {deck - 48}Z" fill="{grad("fun-porcelain")}" {s()}/>'
        f'<ellipse cx="{f(tx)}" cy="{deck - 48}" rx="13" ry="4.4" fill="#fdfdfb" {s(1.8)}/>'
        f'<ellipse cx="{f(tx)}" cy="{f(deck - 47.6)}" rx="10" ry="3" fill="#b4652b"/>'
        f'<path d="M{f(tx - 11.6)} {deck - 41}Q{f(tx)} {deck - 36} {f(tx + 11.6)} {deck - 41}" fill="none" stroke="#ef6f9f" stroke-width="2.4"/>'
    )
    steam = f"M{f(tx - 4)} {deck - 54}q-4 -5 0 -9t0 -9M{f(tx + 4)} {deck - 54}q-4 -5 0 -9t0 -9"
    o.append(
        f'<path d="{steam}" fill="none" stroke="#7d8a8c" stroke-opacity=".5" stroke-width="3.6" stroke-linecap="round"/>'
        f'<path d="{steam}" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round"/>'
    )
    # Two slices of toast and a pat of butter on a plate.
    px = cx + 17
    o.append(
        f'<ellipse cx="{f(px)}" cy="{f(deck - 27.5)}" rx="18" ry="6.8" fill="#fdfdfb" {s(1.8)}/>'
    )
    for dx, rot, inner in ((-5, -9, "#e7b56c"), (5, 7, "#f0c67e")):
        o.append(
            f'<g transform="rotate({rot} {f(px + dx)} {deck - 33})">'
            f'<path d="M{f(px + dx - 9.5)} {deck - 25}V{deck - 37}Q{f(px + dx - 13)} {deck - 45} {f(px + dx - 5)} {deck - 45}H{f(px + dx + 5)}Q{f(px + dx + 13)} {deck - 45} {f(px + dx + 9.5)} {deck - 37}V{deck - 25}Z" fill="#b5722e" {s(1.8)}/>'
            f'<path d="M{f(px + dx - 7)} {deck - 27}V{deck - 38}Q{f(px + dx - 9.5)} {deck - 43} {f(px + dx - 4)} {deck - 43}H{f(px + dx + 4)}Q{f(px + dx + 9.5)} {deck - 43} {f(px + dx + 7)} {deck - 38}V{deck - 27}Z" fill="{inner}"/>'
            f"</g>"
        )
    o.append(
        f'<rect x="{f(px + 1)}" y="{deck - 38}" width="9" height="6.4" rx="1.2" fill="#ffe27a" {s(1.1)} transform="rotate(-8 {f(px + 5)} {deck - 35})"/>'
    )
    return "".join(o)


SKINS = {
    "caesar_bust": caesar_bust,
    "roman_pillar": roman_pillar,
    "laurel_wreath": laurel_wreath,
    "stone_rabbit": stone_rabbit,
    "egg_basket": egg_basket,
    "painted_egg": painted_egg,
    "jester": jester,
    "jack_in_box": jack_in_box,
    "whoopee_cushion": whoopee_cushion,
    "carnations": carnations,
    "gift_hatbox": gift_hatbox,
    "breakfast_tray": breakfast_tray,
}
# Everything but the cushion reaches the wall, or the band below it where a room's plaque hangs.
TALL = set(SKINS) - {"whoopee_cushion"}
