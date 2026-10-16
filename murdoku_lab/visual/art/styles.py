"""Artwork styles. The legacy styles are frozen; `casebook` is the illustrated case-file look."""

LEGACY_STYLES = ("art", "diagram", "fluent", "classic")
CASEBOOK = "casebook"
STYLES = (CASEBOOK,) + LEGACY_STYLES

# Records exported before the casebook existed carry no style field and were drawn as `art`.
RECORD_DEFAULT_STYLE = "art"
# The Lab, the player app and new previews draw the casebook. RL exports choose their style
# explicitly (export_queries / farm --artwork-style) and keep it in the record.
DEFAULT_STYLE = CASEBOOK
# Bumped whenever casebook output changes in a way a dataset should record.
CASEBOOK_VERSION = "casebook/1"

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


def record_style(record):
    """The style a record's images were drawn in; later frames of its episode match it."""
    return check_style(record.get("artwork_style") or RECORD_DEFAULT_STYLE)


def check_theme(theme):
    if theme not in THEMES:
        raise ValueError("theme must be day or night")
    return theme
