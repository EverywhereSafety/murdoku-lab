"""Theme skins: extra prop drawings and wallpapers contributed by setting packs.

Each module here (one per setting) exports:

    SKINS = {"deck_chair": drawer, ...}       # drawer(w, h) -> SVG in the footprint frame
    WALLPAPERS = {"hull_white": pattern, ...}  # pattern(pid) -> <pattern id=pid ...>
    TALL = {"figurehead", ...}                 # skins that rise in front of the wall
    STRETCH = {"lifeboat", ...}                # skins drawn once over a rectangular footprint
    GRADIENTS = {"teak": (top, bottom), ...}   # extra `mk-g-*` gradients the drawings use

The registry merges them so the board renderer, keys and setting validation see one catalogue.
"""

import importlib
import pkgutil

SKINS, WALLPAPERS, TALL, STRETCH, GRADIENTS = {}, {}, set(), set(), {}
SOURCES = {}

for _info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
    _module = importlib.import_module(f"{__name__}.{_info.name}")
    for _name in getattr(_module, "SKINS", {}):
        if _name in SKINS:
            raise ValueError(
                f"skin {_name!r} defined twice ({SOURCES[_name]}, {_info.name})"
            )
        SOURCES[_name] = _info.name
    for _name, _stops in getattr(_module, "GRADIENTS", {}).items():
        if GRADIENTS.get(_name, _stops) != _stops:
            raise ValueError(f"gradient {_name!r} defined twice with different stops")
        GRADIENTS[_name] = _stops
    SKINS.update(getattr(_module, "SKINS", {}))
    WALLPAPERS.update(getattr(_module, "WALLPAPERS", {}))
    TALL |= set(getattr(_module, "TALL", ()))
    STRETCH |= set(getattr(_module, "STRETCH", ()))
