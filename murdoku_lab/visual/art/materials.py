"""Floors, wallpapers and terrain for the 3/4 casebook board.

Floors are real materials (oak, checker tiles, carpets…) so rooms read as places; touching rooms
always get visibly different floors. Wallpapers dress the south face of each room's north wall.
Formal terrain (tile, rug, water, sand, fairway, rough) is information, not decoration: it is
drawn as its own inset patch, and a floor that could be mistaken for a terrain on the same board
is never chosen (`FINISH_CONFLICTS`).
"""

PREFIX = "mk-"
FACE = 26  # height of a wall's visible south face

FINISHES = (
    "planks",
    "boards",
    "herringbone",
    "parquet",
    "carpet",
    "checker",
    "terracotta",
    "marble",
    "flagstone",
    "paving",
    "deck",
    "lawn",
    "terrazzo",
)

# finish -> formal terrains it could be confused with
FINISH_CONFLICTS = {
    "checker": {"tile"},
    "terracotta": {"tile"},
    "paving": {"tile"},
    "marble": {"tile"},
    "terrazzo": {"tile"},
    "carpet": {"rug"},
    "lawn": {"fairway", "rough"},
}

# finish -> variants: (name, base, light, line)
FLOOR_VARIANTS = {
    "planks": (
        ("oak", "#d4a26c", "#ddb07c", "#a8743f"),
        ("ash", "#e1c18f", "#e9cd9f", "#b8925f"),
        ("walnut", "#a77452", "#b2805d", "#6e472f"),
    ),
    "boards": (
        ("walnut", "#9c6b47", "#a8774f", "#664128"),
        ("driftwood", "#bcae99", "#c8bba6", "#857761"),
    ),
    "herringbone": (
        ("honey", "#c9935f", "#d6a46f", "#9c6a40"),
        ("smoke", "#b8a28a", "#c6b29a", "#83705a"),
    ),
    "parquet": (
        ("amber", "#c98f58", "#d8a26c", "#94612f"),
        ("chestnut", "#a8714b", "#b8835b", "#6b4428"),
    ),
    "carpet": (
        ("teal", "#6e9a92", "#86b0a7", "#e3c98f"),
        ("rose", "#c48078", "#d69a91", "#f3d7a6"),
        ("navy", "#506b8b", "#6984a3", "#e3c98f"),
        ("sage", "#8ca981", "#a5c19a", "#f3e3b8"),
        ("plum", "#8b6280", "#a37b98", "#e9c98f"),
    ),
    "checker": (
        ("sage", "#f3ead2", "#b9d0b2", "#8fa58b"),
        ("noir", "#f1ead8", "#57605c", "#3a413e"),
        ("blue", "#f3ecdc", "#a9c1d8", "#7f97ad"),
    ),
    "terracotta": (("terra", "#d58b62", "#e09c74", "#a9603d"),),
    "marble": (
        ("white", "#efebe3", "#f7f4ee", "#c4bdb0"),
        ("verde", "#cfe0d3", "#e0ece3", "#93ad9a"),
    ),
    "flagstone": (
        ("grey", "#c9c6bb", "#d6d3c9", "#8f8b7e"),
        ("sandstone", "#d6c4a3", "#e1d2b5", "#a38d68"),
    ),
    "paving": (("stone", "#d9d2c3", "#e4ddcf", "#a89e8a"),),
    "deck": (("teak", "#c48a57", "#d09764", "#8a5a33"),),
    "lawn": (("grass", "#9cc57f", "#acd18f", "#6f9a5a"),),
    "terrazzo": (
        ("cream", "#e9e0cf", "#c9b89c", "#8f7f66"),
        ("rose", "#e7cfc4", "#c39a8c", "#8f6a5c"),
        ("slate", "#c3c8c6", "#8f9894", "#5f6864"),
    ),
}

WALLPAPERS = (
    "stripe_green",
    "damask_rose",
    "tile_cream",
    "panel_blue",
    "floral_yellow",
    "panel_wood",
    "brick",
    "stone",
)

TERRAIN_BASE = {
    "water": "#8fc5d1",
    "sand": "#ecd9a8",
    "rug": "#d98a7f",
    "fairway": "#a9d08d",
    "rough": "#86ad6c",
    "tile": "#f7f4ec",
}


def floor_id(finish, variant):
    return f"{PREFIX}fl-{finish}-{variant}"


def wallpaper_id(name):
    return f"{PREFIX}wp-{name}"


def terrain_id(name):
    return f"{PREFIX}ter-{name}"


HATCH_ID = PREFIX + "hatch"


def variant(finish, name):
    for v in FLOOR_VARIANTS[finish]:
        if v[0] == name:
            return v
    return FLOOR_VARIANTS[finish][0]


def _pattern(pid, w, h, body):
    return f'<pattern id="{pid}" width="{w}" height="{h}" patternUnits="userSpaceOnUse">{body}</pattern>'


def floor_pattern(finish, name):
    _, base, light, line = variant(finish, name)
    pid = floor_id(finish, name)
    if finish == "planks":
        body = (
            f'<rect width="100" height="40" fill="{base}"/><rect width="100" height="20" fill="{light}"/>'
            f'<path d="M0 20H100M0 40H100M62 0V20M18 20V40" stroke="{line}" stroke-width="1.6" stroke-opacity=".8"/>'
            f'<path d="M8 9h10M70 30h8" stroke="{line}" stroke-width="1" stroke-opacity=".35" stroke-linecap="round"/>'
        )
        return _pattern(pid, 100, 40, body)
    if finish == "boards":
        body = (
            f'<rect width="100" height="50" fill="{base}"/><rect width="100" height="25" fill="{light}"/>'
            f'<path d="M0 25H100M0 50H100M40 0V25M84 25V50" stroke="{line}" stroke-width="2" stroke-opacity=".75"/>'
            f'<circle cx="20" cy="12" r="2.2" fill="none" stroke="{line}" stroke-opacity=".5"/><circle cx="64" cy="37" r="1.8" fill="none" stroke="{line}" stroke-opacity=".5"/>'
        )
        return _pattern(pid, 100, 50, body)
    if finish == "herringbone":
        body = (
            f'<rect width="40" height="40" fill="{base}"/>'
            f'<path d="M0 0L20 20 20 30 0 10ZM20 20L40 0 40 10 20 30ZM0 20L20 40 10 40 0 30ZM40 20 20 40 30 40 40 30Z" fill="{light}"/>'
            f'<path d="M0 10L20 30M20 20L40 0M0 0L20 20M20 30L40 10M0 20 20 40M40 20 20 40" stroke="{line}" stroke-width="1.2" stroke-opacity=".6"/>'
        )
        return _pattern(pid, 40, 40, body)
    if finish == "parquet":
        body = (
            f'<rect width="50" height="50" fill="{base}"/><path d="M0 0h25v25H0ZM25 25h25v25H25Z" fill="{light}"/>'
            f'<path d="M0 0H50V50M25 0V50M0 25H50" fill="none" stroke="{line}" stroke-width="1.3" stroke-opacity=".7"/>'
            f'<path d="M0 8.3H25M0 16.6H25M33.3 0V25M41.6 0V25M8.3 25V50M16.6 25V50M25 33.3H50M25 41.6H50" stroke="{line}" stroke-width=".8" stroke-opacity=".4"/>'
        )
        return _pattern(pid, 50, 50, body)
    if finish == "carpet":
        body = (
            f'<rect width="34" height="34" fill="{base}"/><path d="M17 5 29 17 17 29 5 17Z" fill="none" stroke="{light}" stroke-width="1.6"/>'
            f'<circle cx="17" cy="17" r="2.2" fill="{line}"/><circle cx="0" cy="0" r="1.6" fill="{line}" fill-opacity=".6"/><circle cx="34" cy="34" r="1.6" fill="{line}" fill-opacity=".6"/>'
        )
        return _pattern(pid, 34, 34, body)
    if finish == "checker":
        body = (
            f'<rect width="50" height="50" fill="{base}"/><path d="M0 0h25v25H0ZM25 25h25v25H25Z" fill="{light}"/>'
            f'<path d="M0 0H50V50M25 0V50M0 25H50" fill="none" stroke="{line}" stroke-width="1" stroke-opacity=".55"/>'
        )
        return _pattern(pid, 50, 50, body)
    if finish == "terracotta":
        body = (
            f'<rect width="33.34" height="33.34" fill="{base}"/><rect x="2" y="2" width="29.3" height="29.3" rx="3" fill="{light}"/>'
            f'<path d="M0 0H33.34V33.34" fill="none" stroke="{line}" stroke-width="2.4" stroke-opacity=".7"/>'
        )
        return _pattern(pid, 33.34, 33.34, body)
    if finish == "marble":
        body = (
            f'<rect width="50" height="50" fill="{base}"/><rect width="25" height="25" fill="{light}"/><rect x="25" y="25" width="25" height="25" fill="{light}"/>'
            f'<path d="M0 0H50V50M25 0V50M0 25H50" fill="none" stroke="{line}" stroke-width="1" stroke-opacity=".6"/>'
            f'<path d="M3 18Q12 10 22 14M28 40Q38 32 47 36" stroke="{line}" stroke-width=".9" stroke-opacity=".45" fill="none"/>'
        )
        return _pattern(pid, 50, 50, body)
    if finish == "flagstone":
        body = (
            f'<rect width="100" height="100" fill="{base}"/>'
            f'<path d="M3 3H44L40 30H3ZM48 3H97V36H52ZM3 34H36L44 64H3ZM40 34H97V62L48 66ZM3 68H50V97H3ZM54 70L97 66V97H56Z" fill="{light}" stroke="{line}" stroke-width="1.6" stroke-opacity=".7"/>'
        )
        return _pattern(pid, 100, 100, body)
    if finish == "paving":
        body = (
            f'<rect width="50" height="50" fill="{base}"/>'
            f'<path d="M2 2H48V23H2ZM2 27H23V48H2ZM27 27H48V48H27Z" fill="{light}" stroke="{line}" stroke-width="1.2" stroke-opacity=".6"/>'
        )
        return _pattern(pid, 50, 50, body)
    if finish == "deck":
        body = (
            f'<rect width="100" height="33.34" fill="{base}"/><rect width="100" height="16.67" fill="{light}"/>'
            f'<path d="M0 16.67H100M0 33.34H100" stroke="{line}" stroke-width="2.4" stroke-opacity=".8"/>'
            f'<g fill="{line}" fill-opacity=".6"><circle cx="20" cy="8" r="1.3"/><circle cx="70" cy="25" r="1.3"/></g>'
        )
        return _pattern(pid, 100, 33.34, body)
    if finish == "lawn":
        body = (
            f'<rect width="32" height="32" fill="{base}"/><rect width="32" height="16" fill="{light}" fill-opacity=".6"/>'
            f'<path d="m6 18 2-5 2 5m12 9 2-6 2 6m-8-20 1-4 2 4" stroke="{line}" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
        )
        return _pattern(pid, 32, 32, body)
    if finish == "terrazzo":
        chips = "".join(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'
            for x, y, r, c in (
                (6, 7, 1.6, light),
                (19, 4, 1.1, line),
                (31, 11, 1.9, light),
                (12, 19, 1.2, line),
                (26, 24, 1.5, light),
                (4, 30, 1.0, line),
                (35, 33, 1.3, line),
                (17, 34, 2.0, light),
            )
        )
        body = (
            f'<rect width="40" height="40" fill="{base}"/>{chips}'
            f'<path d="M0 0H40V40" fill="none" stroke="{line}" stroke-width=".9" stroke-opacity=".35"/>'
        )
        return _pattern(pid, 40, 40, body)
    raise ValueError(f"unknown finish {finish!r}")


def wallpaper_pattern(name):
    pid = wallpaper_id(name)
    if name == "stripe_green":
        body = '<rect width="18" height="40" fill="#3d6a5b"/><rect width="6" height="40" fill="#46775f"/><circle cx="12" cy="13" r="1.4" fill="#d9c08a" fill-opacity=".7"/>'
        return _pattern(pid, 18, 40, body)
    if name == "damask_rose":
        body = '<rect width="22" height="26" fill="#c98d84"/><path d="M11 5q4 4 0 8q-4-4 0-8ZM0 18q4 4 0 8M22 18q-4 4 0 8" fill="#dca69c"/>'
        return _pattern(pid, 22, 26, body)
    if name == "tile_cream":
        body = '<rect width="16" height="12" fill="#f1e9d5"/><path d="M0 0H16M0 6H16M8 0V6M0 6V12" stroke="#cfc3a6" stroke-width="1"/>'
        return _pattern(pid, 16, 12, body)
    if name == "panel_blue":
        body = '<rect width="30" height="26" fill="#6f8fa8"/><rect x="4" y="4" width="22" height="13" rx="2" fill="none" stroke="#89a7bd" stroke-width="1.4"/>'
        return _pattern(pid, 30, 26, body)
    if name == "floral_yellow":
        body = '<rect width="24" height="26" fill="#e9c97e"/><circle cx="12" cy="9" r="3" fill="#f6e2ac"/><circle cx="0" cy="22" r="2.4" fill="#d7b268"/><circle cx="24" cy="22" r="2.4" fill="#d7b268"/>'
        return _pattern(pid, 24, 26, body)
    if name == "panel_wood":
        body = '<rect width="40" height="26" fill="#8a5a37"/><rect x="3" y="3" width="34" height="17" rx="2" fill="#9a6847" stroke="#6e4527" stroke-width="1"/>'
        return _pattern(pid, 40, 26, body)
    if name == "brick":
        body = '<rect width="30" height="16" fill="#b5654a"/><path d="M0 0H30M0 8H30M15 0V8M0 8V16M30 8V16" stroke="#e3c3ad" stroke-width="1.2"/>'
        return _pattern(pid, 30, 16, body)
    if name == "stone":
        body = '<rect width="34" height="26" fill="#9a9a8c"/><path d="M0 0H34M0 13H34M12 0V13M28 13V26" stroke="#c9c8bb" stroke-width="1.4"/>'
        return _pattern(pid, 34, 26, body)
    from . import skins

    if name in skins.WALLPAPERS:
        return skins.WALLPAPERS[name](pid)
    if name == "hedge":
        body = '<rect width="20" height="26" fill="#4f8452"/><circle cx="5" cy="6" r="5" fill="#5d9154"/><circle cx="15" cy="12" r="6" fill="#5d9154"/><circle cx="6" cy="20" r="5" fill="#6ea65f"/>'
        return _pattern(pid, 20, 26, body)
    raise ValueError(f"unknown wallpaper {name!r}")


def terrain_pattern(name):
    if name == "water":
        body = '<rect width="44" height="32" fill="#8fc5d1"/><path d="M4 9q7 6 14 0t14 0M22 25q7 6 14 0t14 0" fill="none" stroke="#eaf8f8" stroke-width="2.2" stroke-linecap="round" stroke-opacity=".85"/>'
        return _pattern(terrain_id(name), 44, 32, body)
    if name == "sand":
        body = '<rect width="24" height="24" fill="#ecd9a8"/><g fill="#a5884f" fill-opacity=".45"><circle cx="5" cy="6" r="1.4"/><circle cx="17" cy="15" r="1.1"/><circle cx="9" cy="20" r="1"/><circle cx="21" cy="3" r=".9"/></g>'
        return _pattern(terrain_id(name), 24, 24, body)
    if name == "rug":
        body = '<rect width="20" height="20" fill="#d98a7f"/><path d="M0 0L20 20M20 0L0 20" stroke="#a24f48" stroke-width="1.6" stroke-opacity=".5"/><circle cx="10" cy="10" r="2" fill="#f3d39b"/>'
        return _pattern(terrain_id(name), 20, 20, body)
    if name == "tile":
        body = '<rect width="25" height="25" fill="#f7f4ec"/><path d="M25 0H0V25" fill="none" stroke="#7d98a2" stroke-width="1.8" stroke-opacity=".7"/><rect x="9" y="9" width="7" height="7" fill="#9fc4d0" fill-opacity=".7"/>'
        return _pattern(terrain_id(name), 25, 25, body)
    if name == "fairway":
        body = '<rect width="50" height="50" fill="#a9d08d"/><rect width="50" height="25" fill="#b8da9d"/>'
        return _pattern(terrain_id(name), 50, 50, body)
    if name == "rough":
        body = '<rect width="30" height="30" fill="#86ad6c"/><path d="m4 14 2-6 2 6m8 10 2-7 2 7m4-18 2-5 2 5" fill="none" stroke="#3d6a3e" stroke-width="1.6" stroke-linecap="round" stroke-opacity=".7"/>'
        return _pattern(terrain_id(name), 30, 30, body)
    return None


def hatch_pattern(colour):
    body = f'<path d="M-2 2L2 -2M0 12L12 0M10 14L14 10" stroke="{colour}" stroke-width="1.6" stroke-opacity=".25"/>'
    return _pattern(HATCH_ID, 12, 12, body)
