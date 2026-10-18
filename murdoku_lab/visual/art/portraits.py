"""Casebook portraits: parametric busts assembled from a frozen roster of looks.

A *look* is a tuple of attribute indices (face, skin, hair style and colour, hat, glasses,
facial hair, earrings, outfit cut and colour, extras). `roster.py` freezes at least 96 looks that
differ pairwise in two or more salient attributes. People get looks from their public name and
tag class only, so the same name wears the same face in every case and no private seed is
involved. Gender-coded features (facial hair, earrings) appear only in the matching pools.
"""

import hashlib

from .legacy import portrait_inner
from .palette import mix
from .svg import num

INK = "#102725"

SKINS = ("#f7d7bd", "#efc39f", "#dca37d", "#bc7c56", "#8e5a3a", "#5f3c29")
HAIR = (
    "#2b2522",  # black
    "#4b3024",  # dark brown
    "#74503a",  # brown
    "#93492b",  # auburn
    "#d8b46c",  # blonde
    "#c4672e",  # ginger
    "#a7a7a0",  # grey
    "#e8e3d6",  # white
)
BACKGROUNDS = (
    "#f2d6ad",
    "#d4e3c8",
    "#cfe0e4",
    "#e9d4e6",
    "#f2e2b0",
    "#d9d3ef",
    "#f0cfc6",
    "#cde7da",
)
OUTFITS = (
    "#3d5a73",  # navy
    "#7a3b48",  # wine
    "#46705c",  # bottle green
    "#b9733a",  # mustard
    "#6c5a8e",  # violet
    "#2f3b37",  # charcoal
    "#b04a3a",  # brick
    "#3d7f87",  # teal
    "#8b6b4a",  # tweed
    "#d7cdb7",  # oatmeal
)

FACES = ("oval", "round", "square", "long")
HAIR_STYLES = (
    "crop",  # 0
    "side_part",  # 1
    "swept",  # 2
    "curls",  # 3
    "afro",  # 4
    "bob",  # 5
    "long",  # 6
    "wavy",  # 7
    "bun",  # 8
    "ponytail",  # 9
    "bald",  # 10
    "braids",  # 11
)
HATS = ("none", "beret", "flat_cap", "bowler", "cloche", "headscarf", "fedora")
GLASSES = ("none", "round", "square", "monocle")
FACIAL_HAIR = ("none", "moustache", "beard", "goatee")
EARRINGS = ("none", "studs", "hoops")
CUTS = (
    "suit",
    "blouse",
    "turtleneck",
    "cardigan",
    "waistcoat",
    "scarf",
    "jumper",
    "dress",
)
EXTRAS = ("none", "freckles", "mole", "pipe", "pearls", "blush")

POOLS = ("neutral", "woman", "man")

# Hair styles and accessories each pool draws from. Neutral looks never carry gender-coded
# features, so a portrait can never imply a tag the case does not have.
POOL_RULES = {
    "neutral": {
        "hair": (0, 1, 2, 3, 4, 5, 7, 10),
        "facial": (0,),
        "earrings": (0,),
        "extras": (0, 1, 2, 5),
        "cuts": (0, 2, 3, 5, 6),
    },
    "woman": {
        "hair": (3, 4, 5, 6, 7, 8, 9, 11),
        "facial": (0,),
        "earrings": (0, 1, 2),
        "extras": (0, 1, 2, 4, 5),
        "cuts": (1, 2, 3, 5, 6, 7),
    },
    "man": {
        "hair": (0, 1, 2, 3, 4, 10),
        "facial": (0, 1, 2, 3),
        "earrings": (0,),
        "extras": (0, 1, 2, 3),
        "cuts": (0, 2, 3, 4, 5, 6),
    },
}


def look_from(values):
    keys = (
        "pool",
        "face",
        "skin",
        "hair",
        "hair_colour",
        "hat",
        "glasses",
        "facial",
        "earrings",
        "cut",
        "outfit",
        "background",
        "extras",
    )
    return dict(zip(keys, values))


def roster():
    from .roster import LOOKS

    return [look_from(v) for v in LOOKS]


def pool_of(person, pronoun=None):
    tags = {str(t).lower() for t in person.get("tags", ())}
    if "woman" in tags or "female" in tags:
        return "woman"
    if "man" in tags or "male" in tags:
        return "man"
    if pronoun in ("she", "he"):
        return {"she": "woman", "he": "man"}[pronoun]
    return "neutral"


def assign_looks(people, pronouns=None):
    """Stable, collision-free look ids for a cast: hash of (name, pool) then linear probing."""
    pronouns = pronouns or {}
    looks = roster()
    by_pool = {p: [i for i, l in enumerate(looks) if l["pool"] == p] for p in POOLS}
    taken, out = set(), {}
    for person in people:
        pool = pool_of(person, pronouns.get(person["id"]))
        ids = by_pool[pool] or by_pool["neutral"]
        digest = hashlib.sha256(f"look/1|{person['name']}|{pool}".encode()).digest()
        start = int.from_bytes(digest[:4], "big") % len(ids)
        for step in range(len(ids)):
            candidate = ids[(start + step) % len(ids)]
            if candidate not in taken:
                break
        taken.add(candidate)
        out[person["id"]] = candidate
    return out


# ------------------------------------------------------------------------------- drawing
def _desaturate(color, state):
    if state == "victim":
        return mix(color, "#9aa3a0", 0.6)
    return color


def look_inner(look, state=None):
    """Draw one look in a 100×100 box (circle background of radius 48)."""
    c = lambda col: _desaturate(col, state)  # noqa: E731
    skin = c(SKINS[look["skin"]])
    skin_shade = mix(skin, "#6b3f2a", 0.18)
    hair = c(HAIR[look["hair_colour"]])
    hair_dark = mix(hair, "#000000", 0.25)
    outfit = c(OUTFITS[look["outfit"]])
    outfit_dark = mix(outfit, "#000000", 0.22)
    bg = c(BACKGROUNDS[look["background"]])
    style = HAIR_STYLES[look["hair"]]
    face = FACES[look["face"]]
    hat = HATS[look["hat"]]
    glasses = GLASSES[look["glasses"]]
    facial = FACIAL_HAIR[look["facial"]]
    earrings = EARRINGS[look["earrings"]]
    cut = CUTS[look["cut"]]
    extras = EXTRAS[look["extras"]]
    s = f'stroke="{INK}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"'
    o = [f'<circle cx="50" cy="50" r="48" fill="{bg}"/>']

    # Back hair, behind the head.
    if style in ("long", "wavy", "braids"):
        if style == "wavy":
            o.append(
                f'<path d="M26 42Q16 66 22 86Q34 92 40 80L60 80Q66 92 78 86Q84 66 74 42Z" fill="{hair}" {s}/>'
            )
        elif style == "braids":
            o.append(
                f'<path d="M27 46Q22 70 26 88" fill="none" stroke="{hair}" stroke-width="9"/><path d="M73 46Q78 70 74 88" fill="none" stroke="{hair}" stroke-width="9"/>'
            )
            o.append(
                f'<path d="M22 60h8M21 70h8M22 80h8M70 60h8M71 70h8M70 80h8" stroke="{hair_dark}" stroke-width="1.6"/>'
            )
        else:
            o.append(
                f'<path d="M26 40Q20 70 24 84H76Q80 70 74 40Z" fill="{hair}" {s}/>'
            )
    if style == "ponytail":
        o.append(f'<path d="M70 34Q90 44 80 74Q76 60 70 52Z" fill="{hair}" {s}/>')
    if style == "afro":
        o.append(f'<circle cx="50" cy="36" r="28" fill="{hair}" {s}/>')

    # Shoulders and outfit.
    o.append(f'<path d="M12 100Q12 74 34 70H66Q88 74 88 100Z" fill="{outfit}" {s}/>')
    o.append(f'<path d="M41 62H59V74L50 80 41 74Z" fill="{skin_shade}" {s}/>')
    if cut == "suit":
        o.append(
            f'<path d="M36 71 50 92 64 71" fill="#f6f1e4" {s}/><path d="M48 76h4l2 18h-8Z" fill="{c("#9a3f3a")}" stroke="{INK}" stroke-width="1.2"/>'
        )
        o.append(
            f'<path d="M36 71 44 90M64 71 56 90" stroke="{outfit_dark}" stroke-width="2"/>'
        )
    elif cut == "blouse":
        o.append(f'<path d="M36 71 50 82 64 71 58 86H42Z" fill="#fbf6ea" {s}/>')
    elif cut == "turtleneck":
        o.append(
            f'<path d="M38 66Q50 72 62 66V76Q50 82 38 76Z" fill="{outfit_dark}" {s}/>'
        )
    elif cut == "cardigan":
        o.append(
            f'<path d="M38 71 50 88 62 71" fill="#efe6cf" {s}/><path d="M50 88V100" stroke="{outfit_dark}" stroke-width="2"/>'
        )
        o.append(
            f'<circle cx="54" cy="92" r="1.6" fill="{INK}"/><circle cx="54" cy="98" r="1.6" fill="{INK}"/>'
        )
    elif cut == "waistcoat":
        o.append(
            f'<path d="M38 71 50 86 62 71" fill="#fbf6ea" {s}/><path d="M43 76 50 79 57 76 50 82Z" fill="{c("#c9a052")}" stroke="{INK}" stroke-width="1.2"/>'
        )
        o.append(
            f'<path d="M30 74 42 98M70 74 58 98" stroke="{outfit_dark}" stroke-width="3"/>'
        )
    elif cut == "scarf":
        o.append(
            f'<path d="M34 70Q50 82 66 70L68 78Q50 90 32 78Z" fill="{c("#c4573f")}" {s}/><path d="M58 80 62 98H54Z" fill="{c("#c4573f")}" {s}/>'
        )
    elif cut == "jumper":
        o.append(
            f'<path d="M38 71Q50 80 62 71" fill="none" stroke="{outfit_dark}" stroke-width="3"/>'
        )
        o.append(
            f'<path d="M24 88h52M22 94h56" stroke="{outfit_dark}" stroke-width="1.6" stroke-opacity=".6"/>'
        )
    elif cut == "dress":
        o.append(f'<path d="M38 71Q50 84 62 71" fill="{skin_shade}" {s}/>')
    if extras == "pearls":
        o.append(
            '<g fill="#fbf8f0" stroke="#102725" stroke-width=".8">'
            + "".join(
                f'<circle cx="{num(38 + i * 3.4)}" cy="{num(75 + abs(i - 3.5) * -1.1 + 4)}" r="1.9"/>'
                for i in range(8)
            )
            + "</g>"
        )

    # Head.
    rx, ry, cy = {
        "oval": (21, 26, 43),
        "round": (23, 24, 44),
        "square": (22, 25, 43),
        "long": (19, 28, 42),
    }[face]
    o.append(
        f'<ellipse cx="29" cy="{cy + 2}" rx="4" ry="6" fill="{skin}" {s}/><ellipse cx="71" cy="{cy + 2}" rx="4" ry="6" fill="{skin}" {s}/>'
    )
    if face == "square":
        o.append(
            f'<path d="M{50 - rx} {cy - 10}Q{50 - rx} {cy - ry} 50 {cy - ry}Q{50 + rx} {cy - ry} {50 + rx} {cy - 10}V{cy + 8}Q{50 + rx} {cy + ry} 50 {cy + ry}Q{50 - rx} {cy + ry} {50 - rx} {cy + 8}Z" fill="{skin}" {s}/>'
        )
    else:
        o.append(f'<ellipse cx="50" cy="{cy}" rx="{rx}" ry="{ry}" fill="{skin}" {s}/>')
    if earrings == "studs":
        o.append(
            f'<circle cx="29" cy="{cy + 8}" r="2" fill="{c("#e7c25e")}"/><circle cx="71" cy="{cy + 8}" r="2" fill="{c("#e7c25e")}"/>'
        )
    elif earrings == "hoops":
        o.append(
            f'<circle cx="29" cy="{cy + 11}" r="4" fill="none" stroke="{c("#d9ad48")}" stroke-width="1.8"/><circle cx="71" cy="{cy + 11}" r="4" fill="none" stroke="{c("#d9ad48")}" stroke-width="1.8"/>'
        )

    # Face details.
    ey = cy - 1
    if state == "victim":
        o.append(
            f'<path d="M37 {ey}q4 3 8 0M55 {ey}q4 3 8 0" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
        )
    else:
        o.append(
            f'<circle cx="41" cy="{ey}" r="2.1" fill="{INK}"/><circle cx="59" cy="{ey}" r="2.1" fill="{INK}"/>'
        )
    brow = hair_dark if look["hair_colour"] < 6 else "#6f6a60"
    o.append(
        f'<path d="M35 {ey - 7}q6 -3 11 0M54 {ey - 7}q5 -3 11 0" fill="none" stroke="{brow}" stroke-width="2.2" stroke-linecap="round"/>'
    )
    o.append(
        f'<path d="M50 {ey + 2}l-2.5 8h4" fill="none" stroke="{mix(skin, "#6b3f2a", 0.45)}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    if extras == "blush":
        o.append(
            f'<ellipse cx="38" cy="{ey + 9}" rx="4" ry="2.4" fill="#e58f8f" fill-opacity=".45"/><ellipse cx="62" cy="{ey + 9}" rx="4" ry="2.4" fill="#e58f8f" fill-opacity=".45"/>'
        )
    if extras == "freckles":
        o.append(
            f'<g fill="{mix(skin, "#6b3f2a", 0.55)}"><circle cx="37" cy="{ey + 8}" r=".9"/><circle cx="40" cy="{ey + 10}" r=".9"/><circle cx="43" cy="{ey + 8}" r=".9"/><circle cx="57" cy="{ey + 8}" r=".9"/><circle cx="60" cy="{ey + 10}" r=".9"/><circle cx="63" cy="{ey + 8}" r=".9"/></g>'
        )
    if extras == "mole":
        o.append(f'<circle cx="60" cy="{ey + 13}" r="1.2" fill="{INK}"/>')
    mouth_y = cy + ry * 0.55
    if facial in ("beard",):
        o.append(
            f'<path d="M{50 - rx + 2} {cy + 4}Q{50 - rx + 4} {cy + ry + 8} 50 {cy + ry + 10}Q{50 + rx - 4} {cy + ry + 8} {50 + rx - 2} {cy + 4}Q{50 + rx - 8} {mouth_y + 6} 50 {mouth_y + 4}Q{50 - rx + 8} {mouth_y + 6} {50 - rx + 2} {cy + 4}Z" fill="{hair}" {s}/>'
        )
    if facial == "goatee":
        o.append(
            f'<path d="M45 {mouth_y + 4}Q50 {mouth_y + 14} 55 {mouth_y + 4}Z" fill="{hair}" {s}/>'
        )
    if state != "victim":
        o.append(
            f'<path d="M44 {num(mouth_y)}q6 5 12 0" fill="none" stroke="{INK}" stroke-width="1.7" stroke-linecap="round"/>'
        )
    else:
        o.append(
            f'<path d="M45 {num(mouth_y + 1)}h10" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>'
        )
    if facial in ("moustache", "beard"):
        o.append(
            f'<path d="M41 {num(mouth_y - 3)}Q46 {num(mouth_y - 8)} 50 {num(mouth_y - 4)}Q54 {num(mouth_y - 8)} 59 {num(mouth_y - 3)}Q55 {num(mouth_y)} 50 {num(mouth_y - 2)}Q45 {num(mouth_y)} 41 {num(mouth_y - 3)}Z" fill="{hair}" {s}/>'
        )
    if extras == "pipe":
        o.append(
            f'<path d="M55 {num(mouth_y + 1)}L66 {num(mouth_y + 5)}" stroke="#5a3a26" stroke-width="2.4" stroke-linecap="round"/><path d="M64 {num(mouth_y + 2)}h7v6q-3.5 3-7 0Z" fill="#7a4e32" {s}/>'
        )

    # Front hair.
    top = cy - ry
    if style == "crop":
        o.append(
            f'<path d="M{50 - rx} {cy - 6}Q{50 - rx - 1} {top - 4} 50 {top - 3}Q{50 + rx + 1} {top - 4} {50 + rx} {cy - 6}Q{50 + rx - 4} {top + 6} 50 {top + 5}Q{50 - rx + 4} {top + 6} {50 - rx} {cy - 6}Z" fill="{hair}" {s}/>'
        )
    elif style == "side_part":
        o.append(
            f'<path d="M{50 - rx - 1} {cy - 2}Q{50 - rx - 3} {top - 6} 52 {top - 4}Q{50 + rx + 3} {top - 2} {50 + rx + 1} {cy - 4}Q{50 + rx - 2} {top + 4} 58 {top + 4}Q46 {top + 12} {50 - rx + 4} {top + 14}Z" fill="{hair}" {s}/>'
        )
    elif style == "swept":
        o.append(
            f'<path d="M{50 - rx} {cy - 5}Q{50 - rx - 2} {top - 8} 48 {top - 7}Q{50 + rx + 6} {top - 6} {50 + rx} {cy - 6}Q{50 + rx - 6} {top + 2} 50 {top + 4}Q{50 - rx + 6} {top + 6} {50 - rx} {cy - 5}Z" fill="{hair}" {s}/><path d="M38 {top + 1}Q50 {top - 5} 64 {top + 1}" fill="none" stroke="{hair_dark}" stroke-width="1.4"/>'
        )
    elif style == "curls":
        bumps = "".join(
            f'<circle cx="{num(50 + dx)}" cy="{num(top + dy)}" r="7.5" fill="{hair}" {s}/>'
            for dx, dy in ((-16, 8), (-9, 1), (0, -2), (9, 1), (16, 8))
        )
        o.append(bumps)
    elif style == "afro":
        o.append(
            f'<path d="M{50 - rx} {cy - 4}Q50 {top - 2} {50 + rx} {cy - 4}Q{50 + rx - 4} {top + 8} 50 {top + 8}Q{50 - rx + 4} {top + 8} {50 - rx} {cy - 4}Z" fill="{hair}"/>'
        )
    elif style == "bob":
        o.append(
            f'<path d="M{50 - rx - 4} {cy + 12}Q{50 - rx - 6} {top - 6} 50 {top - 5}Q{50 + rx + 6} {top - 6} {50 + rx + 4} {cy + 12}L{50 + rx - 3} {cy + 12}Q{50 + rx - 2} {top + 10} 50 {top + 9}Q{50 - rx + 2} {top + 10} {50 - rx + 3} {cy + 12}Z" fill="{hair}" {s}/>'
        )
    elif style in ("long", "wavy", "braids", "ponytail"):
        o.append(
            f'<path d="M{50 - rx - 2} {cy + 2}Q{50 - rx - 4} {top - 6} 50 {top - 5}Q{50 + rx + 4} {top - 6} {50 + rx + 2} {cy + 2}Q{50 + rx - 2} {top + 4} 54 {top + 8}Q44 {top + 4} {50 - rx + 2} {top + 14}Z" fill="{hair}" {s}/>'
        )
    elif style == "bun":
        o.append(f'<circle cx="50" cy="{top - 6}" r="9" fill="{hair}" {s}/>')
        o.append(
            f'<path d="M{50 - rx - 1} {cy - 2}Q{50 - rx - 3} {top - 4} 50 {top - 3}Q{50 + rx + 3} {top - 4} {50 + rx + 1} {cy - 2}Q{50 + rx - 4} {top + 6} 50 {top + 6}Q{50 - rx + 4} {top + 6} {50 - rx - 1} {cy - 2}Z" fill="{hair}" {s}/>'
        )
    elif style == "bald":
        o.append(
            f'<path d="M{50 - rx - 1} {cy - 1}Q{50 - rx} {cy - 12} {50 - rx + 5} {cy - 14}V{cy - 4}ZM{50 + rx + 1} {cy - 1}Q{50 + rx} {cy - 12} {50 + rx - 5} {cy - 14}V{cy - 4}Z" fill="{hair}" {s}/>'
        )
        o.append(
            f'<path d="M40 {top + 6}q6 -3 12 -2" fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-width="2.4" stroke-linecap="round"/>'
        )

    # Hats.
    if hat == "beret":
        o.append(
            f'<path d="M{50 - rx - 4} {top + 6}Q48 {top - 14} {50 + rx + 6} {top + 2}Q50 {top + 10} {50 - rx - 4} {top + 6}Z" fill="{c("#b24a3f")}" {s}/><path d="M56 {top - 7}v-4" stroke="{INK}" stroke-width="2"/>'
        )
    elif hat == "flat_cap":
        o.append(
            f'<path d="M{50 - rx - 2} {top + 9}Q{50 - rx} {top - 6} 50 {top - 6}Q{50 + rx} {top - 6} {50 + rx + 2} {top + 6}Q60 {top + 4} {50 - rx - 2} {top + 9}Z" fill="{c("#8b7355")}" {s}/><path d="M{50 + rx - 6} {top + 6}Q{50 + rx + 8} {top + 6} {50 + rx + 10} {top + 11}Q{50 + rx} {top + 12} {50 + rx - 6} {top + 9}Z" fill="{c("#76603f")}" {s}/>'
        )
    elif hat == "bowler":
        o.append(
            f'<path d="M{50 - rx + 2} {top + 4}Q{50 - rx + 2} {top - 16} 50 {top - 16}Q{50 + rx - 2} {top - 16} {50 + rx - 2} {top + 4}Z" fill="{c("#2f3b37")}" {s}/><path d="M{50 - rx - 6} {top + 5}Q50 {top - 1} {50 + rx + 6} {top + 5}Q50 {top + 9} {50 - rx - 6} {top + 5}Z" fill="{c("#2f3b37")}" {s}/><path d="M{50 - rx + 3} {top - 1}H{50 + rx - 3}" stroke="{c("#7a3b48")}" stroke-width="3"/>'
        )
    elif hat == "cloche":
        o.append(
            f'<path d="M{50 - rx - 3} {top + 12}Q{50 - rx - 2} {top - 12} 50 {top - 12}Q{50 + rx + 2} {top - 12} {50 + rx + 3} {top + 12}Q50 {top + 6} {50 - rx - 3} {top + 12}Z" fill="{c("#6c5a8e")}" {s}/><path d="M{50 - rx} {top + 4}Q50 {top - 1} {50 + rx} {top + 4}" stroke="{c("#e7c25e")}" stroke-width="2.4" fill="none"/>'
        )
    elif hat == "headscarf":
        o.append(
            f'<path d="M{50 - rx - 3} {cy + 4}Q{50 - rx - 4} {top - 8} 50 {top - 8}Q{50 + rx + 4} {top - 8} {50 + rx + 3} {cy + 4}Q{50 + rx - 2} {top + 8} 50 {top + 8}Q{50 - rx + 2} {top + 8} {50 - rx - 3} {cy + 4}Z" fill="{c("#3d7f87")}" {s}/><path d="M38 {top + 1}l4 3M50 {top - 2}l2 4M60 {top + 1}l3 3" stroke="#e8f2ee" stroke-width="2" stroke-linecap="round"/>'
        )
    elif hat == "fedora":
        o.append(
            f'<path d="M{50 - rx + 3} {top + 3}Q{50 - rx + 4} {top - 15} 50 {top - 12}Q{50 + rx - 4} {top - 15} {50 + rx - 3} {top + 3}Z" fill="{c("#6b5a45")}" {s}/><path d="M{50 - rx - 8} {top + 5}Q50 {top - 2} {50 + rx + 8} {top + 5}Q50 {top + 9} {50 - rx - 8} {top + 5}Z" fill="{c("#6b5a45")}" {s}/><path d="M{50 - rx + 4} {top - 1}H{50 + rx - 4}" stroke="{c("#2f3b37")}" stroke-width="3"/>'
        )

    # Glasses.
    if glasses == "round":
        o.append(
            f'<g fill="#ffffff" fill-opacity=".25" stroke="{INK}" stroke-width="1.8"><circle cx="41" cy="{ey}" r="6.5"/><circle cx="59" cy="{ey}" r="6.5"/></g><path d="M47.5 {ey}h5M34.5 {ey - 1}l-5 -2M65.5 {ey - 1}l5 -2" stroke="{INK}" stroke-width="1.6"/>'
        )
    elif glasses == "square":
        o.append(
            f'<g fill="#ffffff" fill-opacity=".25" stroke="{INK}" stroke-width="1.8"><rect x="34" y="{ey - 5.5}" width="13" height="10" rx="2.5"/><rect x="53" y="{ey - 5.5}" width="13" height="10" rx="2.5"/></g><path d="M47 {ey}h6" stroke="{INK}" stroke-width="1.6"/>'
        )
    elif glasses == "monocle":
        o.append(
            f'<circle cx="59" cy="{ey}" r="6.5" fill="#ffffff" fill-opacity=".25" stroke="{c("#c9a052")}" stroke-width="2"/><path d="M64 {ey + 5}Q68 {ey + 16} 62 {ey + 26}" fill="none" stroke="{c("#c9a052")}" stroke-width="1.2"/>'
        )

    o.append(
        f'<circle cx="50" cy="50" r="48" fill="none" stroke="{INK}" stroke-width="1.6"/>'
    )
    return "".join(o)


def look_svg(look_id, state=None, *, size=100):
    look = roster()[look_id]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 100 100">'
        f'<defs><clipPath id="mk-face-clip"><circle cx="50" cy="50" r="48"/></clipPath></defs>'
        f'<g clip-path="url(#mk-face-clip)">{look_inner(look, state)}</g></svg>'
    )


def portrait_for(person, *, state=None, cast_size=0):
    """The board/legend portrait for a person of the public observation."""
    if person.get("look") is not None:
        return look_inner(roster()[person["look"]], state)
    return portrait_inner(
        person["portrait"], person.get("victim"), large_cast=cast_size > 8
    )
