"""Artwork styles. The legacy styles are frozen; `casebook` is the illustrated case-file look."""

LEGACY_STYLES = ("art", "diagram", "fluent", "classic")
CASEBOOK = "casebook"
STYLES = (CASEBOOK,) + LEGACY_STYLES

# Records exported before the casebook existed carry no style field and were drawn as `art`.
RECORD_DEFAULT_STYLE = "art"
DEFAULT_STYLE = "art"

THEMES = ("day", "night")

# Layers the player app draws itself on top of the static scene.
DYNAMIC_LAYERS = frozenset({"notes", "people", "hit", "labels", "axes"})
ALL_LAYERS = frozenset(
    {
        "paper",
        "floor",
        "terrain",
        "walls",
        "doors",
        "props",
        "plaques",
        "blocked",
    }
    | DYNAMIC_LAYERS
)
STATIC_LAYERS = ALL_LAYERS - DYNAMIC_LAYERS


def check_style(style):
    if style not in STYLES:
        raise ValueError("style must be one of: " + ", ".join(STYLES))
    return style


def check_theme(theme):
    if theme not in THEMES:
        raise ValueError("theme must be day or night")
    return theme
