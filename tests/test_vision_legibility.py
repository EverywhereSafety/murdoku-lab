"""The casebook stays legible for vision models in every setting, day and night.

Each setting dresses the demo cases; every board must pass `legibility.check` (key coverage,
plaques, WCAG AA text, floor ΔE00, coordinate size at export widths), and no two of a setting's
object drawings may look alike once rasterised.
"""

import pytest

from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.setter import settings
from murdoku_lab.visual.art import legibility
from murdoku_lab.visual.demos import glasshouse, lily_pond
from murdoku_lab.visual.projection import public_observation


@pytest.mark.parametrize("setting_id", settings.available())
@pytest.mark.parametrize("theme", ("day", "night"))
def test_dressed_boards_pass_the_legibility_gate(setting_id, theme):
    for entry in (glasshouse(), lily_pond()):
        dressed = settings.dress(entry.case, setting_id)
        obs = public_observation(Scratchpad(entry.case, dressed))
        found = legibility.check(obs, theme=theme)
        assert found["problems"] == [], (setting_id, entry.slug, found["problems"])


def test_png_decoder_reads_what_resvg_writes():
    from murdoku_lab.visual.raster import bundled_profile, png_from_svg

    items = [("chair", None), ("table", None)]
    png = png_from_svg(legibility.glyph_sheet(items), profile=bundled_profile())
    width, height, channels, rows = legibility.decode_png(png)
    assert (width, height) == (legibility.GLYPH * 2, legibility.GLYPH)
    assert channels in (3, 4) and len(rows) == height


@pytest.mark.parametrize("setting_id", settings.available())
def test_no_two_objects_of_a_setting_look_alike(setting_id):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "check_vision_legibility",
        Path(__file__).resolve().parents[1] / "scripts" / "check_vision_legibility.py",
    )
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    rows = script.glyph_report(setting_id)
    assert all(row["ok"] for row in rows), rows[:3]
