"""Floor finishes and terrain as SVG patterns.

Finishes are decoration: they give each room an identity and never touch the formal terrain.
Terrain patterns are information: tile, rug, water, sand, fairway and rough must stay readable
and must never be mistaken for a finish, so a finish that resembles a terrain on the same board
is skipped (see `FINISH_CONFLICTS`).
"""

PREFIX = "mk-"

FINISHES = (
    "planks",
    "herringbone",
    "parquet",
    "flagstone",
    "carpet",
    "checker",
    "terracotta",
    "marble",
    "deck",
    "boards",
    "lawn",
    "paving",
)

# finish -> formal terrains it could be confused with
FINISH_CONFLICTS = {
    "checker": {"tile"},
    "terracotta": {"tile"},
    "paving": {"tile"},
    "carpet": {"rug"},
    "lawn": {"fairway", "rough"},
}

TERRAIN_BASE = {
    "water": "#94c4cf",
    "sand": "#ecd9a8",
    "rug": "#e7b3ad",
    "fairway": "#b7d398",
    "rough": "#9cb985",
}


def finish_id(name):
    return f"{PREFIX}fin-{name}"


def terrain_id(name):
    return f"{PREFIX}ter-{name}"


HATCH_ID = PREFIX + "hatch"


def _pattern(pid, w, h, body, transform=""):
    extra = f' patternTransform="{transform}"' if transform else ""
    return (
        f'<pattern id="{pid}" width="{w}" height="{h}" patternUnits="userSpaceOnUse"{extra}>'
        f"{body}</pattern>"
    )


def finish_pattern(name, ink, strength=1.0):
    """A finish drawn in `ink` at low opacity; `strength` scales every opacity."""
    o = lambda v: f"{min(1, v * strength):.3f}"  # noqa: E731
    line = f'fill="none" stroke="{ink}" stroke-linecap="round"'
    if name == "planks":
        body = (
            f'<path d="M0 20H100M0 40H100M0 60H100M0 80H100M0 100H100" {line} stroke-width="1.2" stroke-opacity="{o(.10)}"/>'
            f'<path d="M30 0V20M78 20V40M14 40V60M55 60V80M90 80V100" {line} stroke-width="1.2" stroke-opacity="{o(.10)}"/>'
            f'<path d="M8 9h9M62 31h7M33 52h10M74 71h6M20 90h8" {line} stroke-width="1" stroke-opacity="{o(.06)}"/>'
        )
        return _pattern(finish_id(name), 100, 100, body)
    if name == "boards":
        body = (
            f'<path d="M0 25H100M0 50H100M0 75H100M0 100H100" {line} stroke-width="1.6" stroke-opacity="{o(.12)}"/>'
            f'<path d="M62 0V25M18 25V50M80 50V75M40 75V100" {line} stroke-width="1.4" stroke-opacity="{o(.10)}"/>'
            f'<circle cx="31" cy="12" r="2.4" {line} stroke-width="1" stroke-opacity="{o(.10)}"/>'
            f'<circle cx="57" cy="62" r="2" {line} stroke-width="1" stroke-opacity="{o(.10)}"/>'
        )
        return _pattern(finish_id(name), 100, 100, body)
    if name == "deck":
        body = (
            f'<path d="M0 16.5H100M0 33H100M0 49.5H100M0 66H100M0 82.5H100M0 99H100" {line} stroke-width="2" stroke-opacity="{o(.14)}"/>'
            f'<g fill="{ink}" fill-opacity="{o(.12)}"><circle cx="20" cy="8" r="1.3"/><circle cx="70" cy="25" r="1.3"/><circle cx="35" cy="41" r="1.3"/><circle cx="85" cy="58" r="1.3"/><circle cx="12" cy="74" r="1.3"/><circle cx="58" cy="91" r="1.3"/></g>'
        )
        return _pattern(finish_id(name), 100, 99, body)
    if name == "herringbone":
        body = (
            f'<path d="M0 10L10 0M0 30L30 0M10 40L40 10M30 40L40 30" {line} stroke-width="1.2" stroke-opacity="{o(.11)}"/>'
            f'<path d="M10 10L30 30M0 20L20 40M20 0L40 20" {line} stroke-width="1.2" stroke-opacity="{o(.07)}"/>'
        )
        return _pattern(finish_id(name), 40, 40, body)
    if name == "parquet":
        body = (
            f'<path d="M0 0H50V50H0Z" {line} stroke-width="1.2" stroke-opacity="{o(.10)}"/>'
            f'<path d="M25 0V25M0 25H50M12.5 25V50M37.5 25V50" {line} stroke-width="1" stroke-opacity="{o(.08)}"/>'
            f'<path d="M0 8.3H25M0 16.6H25M33.3 0V25M41.6 0V25" {line} stroke-width=".8" stroke-opacity="{o(.06)}"/>'
        )
        return _pattern(finish_id(name), 50, 50, body)
    if name == "flagstone":
        body = f'<path d="M0 34L38 30 44 0M38 30 52 62 0 66M52 62 100 58M44 0 100 4M70 4 66 32 100 36M66 32 52 62M52 62 48 100M80 58 84 100M0 66V100" {line} stroke-width="1.6" stroke-opacity="{o(.11)}"/>'
        return _pattern(finish_id(name), 100, 100, body)
    if name == "carpet":
        body = f'<g fill="{ink}" fill-opacity="{o(.07)}"><circle cx="3" cy="3" r="1.1"/><circle cx="9" cy="9" r="1.1"/></g>'
        return _pattern(finish_id(name), 12, 12, body)
    if name == "checker":
        body = f'<path d="M0 0h25v25H0ZM25 25h25v25H25Z" fill="{ink}" fill-opacity="{o(.055)}"/>'
        return _pattern(finish_id(name), 50, 50, body)
    if name == "terracotta":
        body = f'<path d="M0 0H33.33V33.33" {line} stroke-width="2.2" stroke-opacity="{o(.12)}"/>'
        return _pattern(finish_id(name), 33.33, 33.33, body)
    if name == "paving":
        body = f'<path d="M0 0H50M0 25H50M25 0V25M0 25V50M50 25V50" {line} stroke-width="1.6" stroke-opacity="{o(.11)}"/>'
        return _pattern(finish_id(name), 50, 50, body)
    if name == "marble":
        body = (
            f'<path d="M0 30Q30 22 46 40T100 46M8 100Q28 70 60 76T100 90M70 0Q66 18 84 26" {line} stroke-width="1.1" stroke-opacity="{o(.08)}"/>'
            f'<path d="M0 0H100V100" {line} stroke-width="1.4" stroke-opacity="{o(.06)}"/>'
        )
        return _pattern(finish_id(name), 100, 100, body)
    if name == "lawn":
        body = f'<path d="m6 18 2-5 2 5m12 9 2-6 2 6m-8-20 1-4 2 4" {line} stroke="#3f6a45" stroke-width="1.4" stroke-opacity="{o(.22)}"/>'
        return _pattern(finish_id(name), 32, 32, body)
    raise ValueError(f"unknown finish {name!r}")


def terrain_pattern(name):
    if name == "water":
        body = '<path d="M4 9q7 6 14 0t14 0M22 25q7 6 14 0t14 0" fill="none" stroke="#f3fbf8" stroke-width="2.2" stroke-linecap="round" stroke-opacity=".75"/>'
        return _pattern(terrain_id(name), 44, 32, body)
    if name == "sand":
        body = '<g fill="#8f7445" fill-opacity=".38"><circle cx="5" cy="6" r="1.4"/><circle cx="17" cy="15" r="1.1"/><circle cx="9" cy="20" r="1"/><circle cx="21" cy="3" r=".9"/></g>'
        return _pattern(terrain_id(name), 24, 24, body)
    if name == "rug":
        body = '<path d="M0 0L18 18M18 0L0 18" stroke="#8c4552" stroke-width="1.6" stroke-opacity=".32"/>'
        return _pattern(terrain_id(name), 18, 18, body)
    if name == "tile":
        body = '<path d="M25 0H0V25" fill="none" stroke="#2f4a46" stroke-width="1.6" stroke-opacity=".22"/><circle cx="12.5" cy="12.5" r="2" fill="#2f4a46" fill-opacity=".14"/>'
        return _pattern(terrain_id(name), 25, 25, body)
    if name == "fairway":
        body = '<path d="M0 0H50V25H0Z" fill="#ffffff" fill-opacity=".14"/>'
        return _pattern(terrain_id(name), 50, 50, body)
    if name == "rough":
        body = '<path d="m4 14 2-6 2 6m8 10 2-7 2 7m4-18 2-5 2 5" fill="none" stroke="#2f5a3a" stroke-width="1.5" stroke-linecap="round" stroke-opacity=".38"/>'
        return _pattern(terrain_id(name), 30, 30, body)
    return None


def hatch_pattern(color):
    body = f'<path d="M-2 2L2 -2M0 12L12 0M10 14L14 10" stroke="{color}" stroke-width="1.6" stroke-opacity=".22"/>'
    return _pattern(HATCH_ID, 12, 12, body)
