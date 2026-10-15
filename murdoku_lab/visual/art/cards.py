"""Share cards and link previews in the sticker style: die-cut stickers on the setting's colour.

    share_card_svg(card, layout="og")        # 1200×630 link preview
    share_card_svg(card, layout="portrait")  # 1080×1350 image for chats and stories

A card is built from public facts only — title, setting, size, difficulty, date, the cast's
faces and (once solved) the player's stars and hints. It never names the culprit, a square or
a placement, so a shared card cannot spoil the case.

`card` keys: title, setting (setting id), size ("7×7"), difficulty ("Medium"), state
("unsolved" | "solved"), and optionally number (daily case number), date ("Thu 15 Oct"),
url, product ("Murdoku Lab"), stars (0–3), hints (int), streak (int), faces (look ids).
"""

import math
import re

from . import brand, portraits, props
from .palette import ES, mix
from .svg import FONT_MONO, FONT_SANS, FONT_SERIF, esc, num, text

LAYOUTS = {"og": (1200, 630), "portrait": (1080, 1350)}
STATES = ("unsolved", "solved")
STICKER = "mk-sticker"
DEFAULT_EMBLEMS = {
    "manor": "cabinet_radio",
    "liner": "life_ring",
    "museum": "sarcophagus",
    "theatre": "pumpkin_coach",
    "chalet": "snowman",
    "glasshouse": "gnome",
    "train": "samovar",
    "library": "owl",
}


def _defs():
    return (
        props.defs()
        + f'<filter id="{STICKER}" x="-20%" y="-20%" width="140%" height="140%">'
        '<feMorphology in="SourceAlpha" operator="dilate" radius="7" result="grown"/>'
        '<feGaussianBlur in="grown" stdDeviation="5" result="blur"/>'
        '<feOffset in="blur" dx="4" dy="8" result="offset"/>'
        '<feFlood flood-color="#1b130e" flood-opacity=".28"/>'
        '<feComposite in2="offset" operator="in" result="shadow"/>'
        '<feFlood flood-color="#ffffff"/>'
        '<feComposite in2="grown" operator="in" result="edge"/>'
        '<feMerge><feMergeNode in="shadow"/><feMergeNode in="edge"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
        '<clipPath id="mk-card-face"><circle cx="50" cy="50" r="48"/></clipPath>'
    )


def _setting(card):
    from murdoku_lab.setter import settings

    setting_id = card.get("setting") or "manor"
    pack = settings.load(setting_id)
    visual = pack["visual"]
    emblem = visual.get("emblem") or DEFAULT_EMBLEMS.get(setting_id)
    skins = visual.get("skins", {})
    kind = next((k for k, v in skins.items() if v == emblem), "generic")
    return pack, visual.get("accent", ES["accent"]), kind, emblem


def _wrap(value, size, width):
    """Greedy word wrap with a measured average advance for Newsreader semibold."""
    words, lines, line = str(value).split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if len(trial) * size * 0.5 > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def _background(w, h, accent):
    light = mix(accent, "#ffffff", 0.16)
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="2.4"/>'
        for x in (12, 42)
        for y in ((12, 42) if x == 12 else (27, 57))
    )
    return (
        f'<defs><pattern id="mk-card-dots" width="60" height="60" patternUnits="userSpaceOnUse">'
        f'<g fill="{light}" fill-opacity=".55">{dots}</g></pattern></defs>'
        f'<rect width="{w}" height="{h}" fill="{accent}"/>'
        f'<rect width="{w}" height="{h}" fill="url(#mk-card-dots)"/>'
    )


# A prop's soft floor shadow would be cut out as part of the sticker; stickers drop it.
_SOFT_SHADOW = re.compile(
    r'<(?:ellipse|rect|path)[^>]*filter="url\(#mk-soft(?:er)?\)"[^>]*/>'
)


def _cutout(kind, skin):
    return _SOFT_SHADOW.sub("", props.draw(kind, 100, 100, skin=skin))


def _bubble(x, y, w, line, *, tail="right"):
    h = 64
    tip = (
        f"M{num(x + w - 30)} {num(y + h)}l26 18-6 -18Z"
        if tail == "right"
        else f"M{num(x + 30)} {num(y + h)}l-26 18 6 -18Z"
    )
    return (
        f'<g filter="url(#{STICKER})"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{h}" rx="22" fill="#ffffff"/>'
        f'<path d="{tip}" fill="#ffffff"/></g>'
        + text(
            x + w / 2,
            y + 42,
            line,
            28,
            ES["ink"],
            anchor="middle",
            weight="700",
            family=FONT_SANS,
        )
    )


def _sticker(inner, x, y, scale=1.0, rotate=0):
    return (
        f'<g transform="translate({num(x)} {num(y)}) rotate({num(rotate)}) scale({num(scale)})">'
        f'<g filter="url(#{STICKER})">{inner}</g></g>'
    )


def _face(look_id, state=None):
    look = portraits.roster()[look_id]
    return (
        '<circle cx="50" cy="50" r="50" fill="#fbf7ee"/>'
        f'<g clip-path="url(#mk-card-face)">{portraits.look_inner(look, state)}</g>'
        '<circle cx="50" cy="50" r="49" fill="none" stroke="#2a221d" stroke-width="2.4"/>'
    )


def _stars(x, y, count, size=30):
    out = []
    for i in range(3):
        cx = x + i * (size + 8)
        filled = i < count
        points = []
        for j in range(10):
            a = math.radians(-90 + 36 * j)
            r = size / 2 if j % 2 == 0 else size * 0.22
            points.append(f"{num(cx + r * math.cos(a))} {num(y + r * math.sin(a))}")
        out.append(
            f'<path d="M{"L".join(points)}Z" fill="{"#f2c13a" if filled else "#e6dcc6"}" '
            f'stroke="#2a221d" stroke-width="2" stroke-linejoin="round"/>'
        )
    return "".join(out)


def _stamp(x, y, state, size=1.0):
    solved = state == "solved"
    label = "CASE CLOSED" if solved else "UNSOLVED"
    colour = ES["accent"] if solved else ES["attack"]
    w = (300 if solved else 250) * size
    h = 74 * size
    return (
        f'<g transform="translate({num(x)} {num(y)}) rotate(-9)" opacity=".92">'
        f'<rect x="{num(-w / 2)}" y="{num(-h / 2)}" width="{num(w)}" height="{num(h)}" rx="{num(10 * size)}" '
        f'fill="#fbf7ee" fill-opacity=".55" stroke="{colour}" stroke-width="{num(6 * size)}"/>'
        f'<rect x="{num(-w / 2 + 9 * size)}" y="{num(-h / 2 + 9 * size)}" width="{num(w - 18 * size)}" height="{num(h - 18 * size)}" '
        f'rx="{num(6 * size)}" fill="none" stroke="{colour}" stroke-width="{num(2 * size)}"/>'
        + text(
            0,
            15 * size,
            label,
            40 * size,
            colour,
            anchor="middle",
            weight="700",
            family=FONT_MONO,
            spacing=3 * size,
        )
        + "</g>"
    )


def _case_file(card, pack, x, y, w, h, *, title_size):
    """The cream case-file card that carries every word on the share card."""
    product = card.get("product", "Murdoku Lab")
    number = card.get("number")
    eyebrow = (
        f"{product} · Daily case #{number}" if number else f"{product} · {pack['name']}"
    )
    details = " · ".join(
        str(v)
        for v in (
            pack["name"],
            card.get("size"),
            card.get("difficulty"),
            card.get("date"),
        )
        if v
    )
    out = [
        f'<g transform="translate({num(x)} {num(y)}) rotate(-1.6)">',
        f'<g filter="url(#{STICKER})"><rect width="{num(w)}" height="{num(h)}" rx="26" fill="#fbf7ee"/>'
        f'<rect y="0" width="{num(w)}" height="56" rx="26" fill="#efe5cf"/>'
        f'<rect y="30" width="{num(w)}" height="26" fill="#efe5cf"/></g>',
        text(
            36,
            38,
            eyebrow.upper(),
            18,
            ES["soft"],
            weight="500",
            family=FONT_MONO,
            spacing=1.6,
        ),
    ]
    lines = _wrap(card.get("title", "A Case"), title_size, w - 72)[:3]
    ty = 56 + title_size * 1.22
    for line in lines:
        out.append(
            text(36, ty, line, title_size, ES["ink"], weight="600", family=FONT_SERIF)
        )
        ty += title_size * 1.08
    out.append(
        text(36, ty + 16, details, 24, ES["soft"], weight="500", family=FONT_SANS)
    )
    by = ty + 70
    if card.get("state") == "solved":
        out.append(_stars(52, by - 8, int(card.get("stars", 0))))
        hints = int(card.get("hints", 0))
        tail = "no hints" if hints == 0 else f"{hints} hint{'s' if hints != 1 else ''}"
        streak = card.get("streak")
        if streak:
            tail += f" · {streak}-day streak"
        out.append(text(176, by, tail, 24, ES["ink"], weight="600", family=FONT_SANS))
    else:
        out.append(
            text(
                36,
                by,
                "Who did it? Place every suspect to find out.",
                24,
                ES["ink"],
                weight="600",
                family=FONT_SANS,
            )
        )
    if card.get("url"):
        out.append(
            text(
                36,
                h - 30,
                card["url"],
                20,
                ES["accent"],
                weight="500",
                family=FONT_MONO,
            )
        )
    out.append("</g>")
    return "".join(out)


def share_card_svg(card, layout="og"):
    if layout not in LAYOUTS:
        raise ValueError(f"layout must be one of {tuple(LAYOUTS)}")
    state = card.get("state", "unsolved")
    if state not in STATES:
        raise ValueError(f"state must be one of {STATES}")
    w, h = LAYOUTS[layout]
    pack, accent, kind, emblem = _setting(card)
    faces = list(card.get("faces", ()))[:5]
    pose = "celebrating" if state == "solved" else "thinking"
    mascot = (
        brand.donut_detective(pose)
        if brand.mascot_mode() != "placeholder"
        else brand.placeholder(pose)
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{esc(card.get("title", "Murdoku case"))}">',
        f"<defs>{_defs()}</defs>",
        _background(w, h, accent),
    ]
    mascot_card = f'<rect width="128" height="128" rx="30" fill="#fbf7ee"/>{mascot}'
    line = "Case closed!" if state == "solved" else "Can you crack it?"
    if layout == "og":
        out.append(_sticker(_cutout(kind, emblem), 760, 96, 2.4, 7))
        out.append(_sticker(mascot_card, 1040, 40, 1.0, 8))
        for i, look in enumerate(faces):
            out.append(
                _sticker(
                    _face(look), 736 + i * 88, 436 + (i % 2) * 18, 0.92, -6 + i * 4
                )
            )
        out.append(_case_file(card, pack, 52, 64, 650, 500, title_size=58))
        out.append(_stamp(536, 446, state, 0.8))
    else:
        out.append(_case_file(card, pack, 70, 80, 940, 520, title_size=76))
        out.append(_stamp(790, 470, state, 1.0))
        out.append(_sticker(_cutout(kind, emblem), 96, 660, 3.1, -6))
        spots = ((520, 680), (680, 700), (840, 680), (600, 850), (760, 862))
        for (fx, fy), look in zip(spots, faces):
            out.append(_sticker(_face(look), fx, fy, 1.3, -8 + fx % 7 * 2))
        out.append(_sticker(mascot_card, 800, 1070, 1.55, 7))
        out.append(_bubble(380, 1110, 360, line))
    out.append("</svg>")
    return "".join(out)


def card_for(case, theme, *, state="unsolved", **extra):
    """A share card for a dressed case: public facts only."""
    from murdoku_lab.environment.state import Scratchpad
    from murdoku_lab.visual.projection import public_observation

    obs = public_observation(Scratchpad(case, theme))
    faces = [
        p["look"]
        for p in obs["people"]
        if p.get("look") is not None and not p.get("victim")
    ]
    card = {
        "title": theme.title,
        "setting": theme.setting_id or "manor",
        "size": f"{case.scene.W}×{case.scene.H}",
        "state": state,
        "faces": faces,
    }
    card.update(extra)
    return card


__all__ = ["LAYOUTS", "STATES", "share_card_svg", "card_for"]
