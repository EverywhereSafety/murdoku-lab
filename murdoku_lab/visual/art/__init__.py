"""Board artwork for every export and the interactive boards.

`casebook` is the illustrated case-file style. The four legacy styles (`art`, `diagram`,
`fluent`, `classic`) are frozen byte for byte in `legacy.py` because published datasets were
drawn with them; `tests/test_legacy_art.py` guards that. Callers import from this package only.

No remote fonts, bitmap dependencies or official-game artwork. Geometry is read only from the
public observation; illustration can never access the hidden solution.
"""

import re

from . import casebook, legacy
from .legacy import (
    CELL,
    CLASSIC_PALETTE,
    INK,
    PAD,
    PAPER,
    connected_components,
    dimensions,
    esc,
    portrait_inner,
    portrait_svg,
    prop_shape,
    prop_svg,
    txt,
)
from .styles import (
    CASEBOOK,
    DEFAULT_STYLE,
    LEGACY_STYLES,
    RECORD_DEFAULT_STYLE,
    STATIC_LAYERS,
    STYLES,
    THEMES,
    check_style,
    check_theme,
)


def scene_svg(
    observation,
    *,
    style=DEFAULT_STYLE,
    selected=None,
    focus_cells=(),
    theme="day",
    layers=None,
    cell_labels="tabs",
    reveal=None,
):
    check_style(style)
    if style in LEGACY_STYLES:
        return legacy.scene_svg(
            observation, style=style, selected=selected, focus_cells=focus_cells
        )
    return casebook.scene_svg(
        observation,
        theme=check_theme(theme),
        selected=selected,
        focus_cells=focus_cells,
        layers=layers,
        cell_labels=cell_labels,
        reveal=reveal,
    )


def board_svg(observation, *, style=DEFAULT_STYLE, theme="day"):
    check_style(style)
    if style in LEGACY_STYLES:
        return legacy.board_svg(observation, style=style)
    from . import keys

    return keys.board_svg(observation, theme=check_theme(theme))


def observation_svg(
    observation, *, style=DEFAULT_STYLE, selected=None, focus_cells=(), theme="day"
):
    check_style(style)
    if style in LEGACY_STYLES:
        return legacy.observation_svg(
            observation, style=style, selected=selected, focus_cells=focus_cells
        )
    from . import keys

    return keys.observation_svg(
        observation,
        theme=check_theme(theme),
        selected=selected,
        focus_cells=focus_cells,
    )


def thumbnail_svg(observation, *, px=320, theme="day"):
    """A case-library thumbnail: the static casebook scene (rooms, walls, furniture, frame)
    with no people, notes, axes or hit targets, sized to `px` wide."""
    svg = casebook.scene_svg(
        observation,
        theme=check_theme(theme),
        layers=STATIC_LAYERS,
        cell_labels="none",
        backdrop=False,
    )
    width, height = dimensions(observation)
    size = f'width="{px}" height="{round(px * height / width)}"'
    return re.sub(r'width="\d+" height="\d+"', size, svg, count=1)


def share_card_svg(card, layout="og"):
    from . import cards

    return cards.share_card_svg(card, layout)


__all__ = [
    "CASEBOOK",
    "CELL",
    "CLASSIC_PALETTE",
    "DEFAULT_STYLE",
    "INK",
    "LEGACY_STYLES",
    "PAD",
    "PAPER",
    "RECORD_DEFAULT_STYLE",
    "STATIC_LAYERS",
    "STYLES",
    "THEMES",
    "board_svg",
    "check_style",
    "check_theme",
    "connected_components",
    "dimensions",
    "esc",
    "observation_svg",
    "portrait_inner",
    "portrait_svg",
    "prop_shape",
    "prop_svg",
    "scene_svg",
    "share_card_svg",
    "thumbnail_svg",
    "txt",
]
