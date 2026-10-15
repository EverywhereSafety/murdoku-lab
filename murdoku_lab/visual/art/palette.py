"""One source for every casebook colour, and the colour maths that keeps them legible.

The casebook look borrows Everywhere Safety's brand tokens (ink, accent, the coral "attack" red)
so a player who follows a link to the research site feels no seam. Room tints and person accents
are checked with CIEDE2000 and WCAG contrast instead of being eyeballed.
"""

from functools import lru_cache
import math

# Measured from everywheresafety.github.io (:root custom properties).
ES = {
    "ink": "#102725",
    "soft": "#445c58",
    "muted": "#71847f",
    "accent": "#0b7469",
    "accent_light": "#cfe4df",
    "attack": "#d7654f",
    "intervene": "#397eb8",
    "state": "#18836f",
    "context": "#8462b8",
    "embodied": "#516dc1",
    "evaluate": "#c77a25",
    "train": "#168a8b",
    "bg": "#eef3f2",
    "surface": "#f8fbfa",
}

DAY = {
    "paper": "#fbf7ee",
    "paper_2": "#f4eedf",
    "mat": "#efe5cf",
    "ink": ES["ink"],
    "ink_soft": ES["soft"],
    "ink_muted": ES["muted"],
    "grid": "#102725",
    "wall": "#1d332e",
    "wall_light": "#fdf9ef",
    "brass": "#b98a3e",
    "brass_dark": "#8a6427",
    "evidence": ES["attack"],
    "evidence_text": "#b14a37",
    "accent": ES["accent"],
    "blocked": "#6d5444",
    "shadow": "#102725",
    "note": "#0b7469",
    "exclusion": "#9b3f80",
}

NIGHT = {
    **DAY,
    "paper": "#14211e",
    "paper_2": "#173430",
    "mat": "#0d1a17",
    "ink": "#efe8d8",
    "ink_soft": "#cfc6b2",
    "ink_muted": "#a49c88",
    "grid": "#efe8d8",
    "wall": "#e9dcc0",
    "wall_light": "#fff7e6",
    "shadow": "#000000",
    "note": "#7fd3c4",
    "exclusion": "#e3a1cf",
}

THEMES = {"day": DAY, "night": NIGHT}

# Twelve light room tints, ordered so that consecutive ids already differ; graph colouring picks
# among them per board so that touching rooms never share a tint.
ROOM_TINTS = (
    "#f1d8b4",  # apricot parchment
    "#d3e4c3",  # sage
    "#efe0a6",  # straw
    "#c6dfe2",  # duck egg
    "#f1cdc4",  # blush
    "#d9cfeb",  # lavender
    "#cde8da",  # mint
    "#e9d2a0",  # honey
    "#c9d7f1",  # powder blue
    "#ecc8db",  # mauve
    "#dde2c0",  # pistachio
    "#bfe1d9",  # seafoam
)

# Person accents: Everywhere Safety's research hues first, then game hues. Badges carry white
# letters, so every accent is darkened until white text passes 4.5:1.
PERSON_ACCENTS = (
    ES["attack"],
    ES["intervene"],
    ES["state"],
    ES["context"],
    ES["evaluate"],
    ES["embodied"],
    ES["train"],
    "#a3456f",  # plum
    "#6c7a24",  # olive
    "#9c5a2c",  # rust
    "#4f6475",  # slate
    "#b7465f",  # rose
)


# ----------------------------------------------------------------------------- colour maths
def hex_to_rgb(color):
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    return tuple(int(color[i : i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(v * 255))):02x}" for v in rgb)


def mix(a, b, t):
    """Linear blend in sRGB: t=0 gives a, t=1 gives b."""
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def _linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def luminance(color):
    r, g, b = (_linear(v) for v in hex_to_rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def darken_for_contrast(color, against="#ffffff", target=4.5):
    """Darken towards ink until `against` text on `color` reaches the target ratio."""
    out = color
    for step in range(1, 41):
        if contrast(out, against) >= target:
            return out
        out = mix(color, "#000000", step * 0.025)
    return out


@lru_cache(maxsize=4096)
def lab(color):
    r, g, b = (_linear(v) for v in hex_to_rgb(color))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a, b):
    """CIEDE2000 colour difference between two hex colours."""
    l1, a1, b1 = lab(a)
    l2, a2, b2 = lab(b)
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    cbar = (c1 + c2) / 2
    g = 0.5 * (1 - math.sqrt(cbar**7 / (cbar**7 + 25**7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dlp, dcp = l2 - l1, c2p - c1p
    if c1p * c2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dhp_big = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp / 2))
    lbar, cbarp = (l1 + l2) / 2, (c1p + c2p) / 2
    if c1p * c2p == 0:
        hbarp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbarp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbarp = (h1p + h2p + 360) / 2
    else:
        hbarp = (h1p + h2p - 360) / 2
    t = (
        1
        - 0.17 * math.cos(math.radians(hbarp - 30))
        + 0.24 * math.cos(math.radians(2 * hbarp))
        + 0.32 * math.cos(math.radians(3 * hbarp + 6))
        - 0.20 * math.cos(math.radians(4 * hbarp - 63))
    )
    sl = 1 + 0.015 * (lbar - 50) ** 2 / math.sqrt(20 + (lbar - 50) ** 2)
    sc = 1 + 0.045 * cbarp
    sh = 1 + 0.015 * cbarp * t
    dtheta = 30 * math.exp(-(((hbarp - 275) / 25) ** 2))
    rc = 2 * math.sqrt(cbarp**7 / (cbarp**7 + 25**7))
    rt = -rc * math.sin(math.radians(2 * dtheta))
    return math.sqrt(
        (dlp / sl) ** 2
        + (dcp / sc) ** 2
        + (dhp_big / sh) ** 2
        + rt * (dcp / sc) * (dhp_big / sh)
    )


def person_accent(index):
    base = PERSON_ACCENTS[index % len(PERSON_ACCENTS)]
    if index >= len(PERSON_ACCENTS):
        # Larger casts reuse the hues at a different depth; looks, not colour, carry identity.
        base = mix(base, "#102725", 0.28 * (index // len(PERSON_ACCENTS)))
    return darken_for_contrast(base)


def night_tint(color):
    """A room tint for the night casebook: the same hue, deep and quiet."""
    return mix(color, "#0f1d1a", 0.72)
