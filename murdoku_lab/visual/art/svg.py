"""Small SVG helpers shared by the casebook modules."""

from html import escape

FONT_SANS = "'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif"
FONT_MONO = "'DM Mono', Menlo, 'DejaVu Sans Mono', monospace"
FONT_SERIF = "Newsreader, Georgia, 'DejaVu Serif', serif"


def esc(value):
    return escape(str(value), quote=True)


def num(value):
    """Compact, deterministic number formatting for coordinates."""
    if isinstance(value, int):
        return str(value)
    out = f"{value:.2f}".rstrip("0").rstrip(".")
    return out if out not in ("-0", "") else "0"


def text(
    x,
    y,
    value,
    size,
    fill,
    *,
    anchor="start",
    weight=None,
    family=FONT_SANS,
    spacing=None,
    **attrs,
):
    extra = [f'font-family="{esc(family)}"']
    if anchor != "start":
        extra.append(f'text-anchor="{anchor}"')
    if weight:
        extra.append(f'font-weight="{weight}"')
    if spacing:
        extra.append(f'letter-spacing="{spacing}"')
    extra.extend(f'{k.replace("_", "-")}="{esc(v)}"' for k, v in attrs.items())
    return (
        f'<text x="{num(x)}" y="{num(y)}" font-size="{num(size)}" fill="{fill}" '
        f'{" ".join(extra)}>{esc(value)}</text>'
    )
