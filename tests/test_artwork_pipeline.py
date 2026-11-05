"""Exports keep their artwork: every frame of an episode is drawn in its record's style.

Records exported before the casebook existed carry no style and keep the legacy `art` look,
so published datasets render exactly as they did.
"""

import os
import subprocess
import sys

import pytest

from murdoku_lab.environment.queries import make_record
from murdoku_lab.environment.vision import environment_for
from murdoku_lab.visual.art.styles import (
    CASEBOOK,
    DEFAULT_STYLE,
    RECORD_DEFAULT_STYLE,
    STYLES,
    record_style,
)
from murdoku_lab.visual.demos import glasshouse
from murdoku_lab.visual.raster import profile_for, renderer_info


def _vision_record(style=None):
    entry = glasshouse()
    record = make_record(entry.case, entry.theme, view="text")
    record["murdoku_observation"] = "vision"
    if style:
        record["artwork_style"] = style
    return record


def test_defaults_keep_old_records_on_the_legacy_art():
    assert RECORD_DEFAULT_STYLE == "art"
    assert DEFAULT_STYLE == CASEBOOK
    assert record_style({}) == "art"
    assert record_style({"artwork_style": "casebook"}) == "casebook"
    with pytest.raises(ValueError):
        record_style({"artwork_style": "watercolour"})


@pytest.mark.parametrize("style", STYLES)
def test_episode_frames_follow_the_record_style(style):
    env = environment_for(_vision_record(style))
    assert env.artwork_style == style
    svg = env.render_svg(scope="board")
    assert ('data-style="casebook"' in svg) == (style == CASEBOOK)


def test_records_without_a_style_render_as_before():
    env = environment_for(_vision_record())
    assert env.artwork_style == "art"
    assert 'data-style="casebook"' not in env.render_svg(scope="board")


def test_casebook_rasterises_with_bundled_fonts_only():
    profile = profile_for(CASEBOOK)
    assert profile["loadSystemFonts"] is False and profile["fontFiles"]
    assert profile_for("art") is None
    info = renderer_info(CASEBOOK)
    assert info["style"] == CASEBOOK and len(info["font_sha256"]) == 64
    assert renderer_info("classic")["fonts"] == "system"


def test_casebook_scenes_do_not_depend_on_the_hash_seed():
    """Set order follows PYTHONHASHSEED, so a scene that lists its floors from a set would make
    every daily build write different files."""
    script = (
        "from murdoku_lab.environment.state import Scratchpad\n"
        "from murdoku_lab.setter import settings\n"
        "from murdoku_lab.visual.art import casebook\n"
        "from murdoku_lab.visual.demos import glasshouse\n"
        "from murdoku_lab.visual.projection import public_observation\n"
        "case = glasshouse().case\n"
        "obs = public_observation(Scratchpad(case, settings.dress(case, 'manor')))\n"
        "print(casebook.scene_svg(obs))\n"
    )
    scenes = {
        subprocess.run(
            [sys.executable, "-c", script],
            env={**os.environ, "PYTHONHASHSEED": seed},
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        for seed in ("1", "2")
    }
    assert len(scenes) == 1
