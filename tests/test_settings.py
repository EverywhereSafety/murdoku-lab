"""Setting packs: the words and the look of a case, never its maths.

Every pack must validate, name every classic prop, draw every skin it names at every footprint a
generator can produce, and dress a case without touching its content hash or solution.
"""

import copy
import html
import json
from xml.etree import ElementTree as ET

import pytest

from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.setter import settings
from murdoku_lab.visual import art
from murdoku_lab.visual.art import frames, materials, props, skins
from murdoku_lab.visual.demos import glasshouse, lily_pond
from murdoku_lab.visual.projection import public_observation

SVG = 'xmlns="http://www.w3.org/2000/svg"'


def well_formed(fragment, w=200, h=200):
    doc = f'<svg {SVG} width="{w}" height="{h}"><defs>{props.defs()}</defs>{fragment}</svg>'
    ET.fromstring(doc)
    assert "nan" not in fragment and "inf" not in fragment
    return doc


@pytest.mark.parametrize("setting_id", settings.available())
def test_every_pack_validates_and_names_every_classic_prop(setting_id):
    pack = settings.load(setting_id)
    assert set(settings.CLASSIC_KINDS) <= set(pack["objects"])
    assert len(pack["rooms"]) >= settings.MIN_ROOMS
    assert pack["visual"].get("frame") in frames.FRAMES
    for kind, skin in pack["visual"].get("skins", {}).items():
        assert skin in props.all_skins(), (setting_id, kind, skin)


def test_at_least_eight_settings_ship():
    assert len(settings.available()) >= 8


@pytest.mark.parametrize("skin", sorted(props.all_skins()))
def test_every_skin_draws_at_every_footprint(skin):
    shapes = [(100, 100), (200, 100), (100, 200)]
    if props.stretches("generic", skin):
        shapes += [(200, 200), (300, 100), (100, 300)]
    for w, h in shapes:
        well_formed(props.draw("generic", w, h, skin=skin), w, h)
    well_formed(props.glyph("generic", 40, skin=skin), 40, 40)


def test_theme_skins_never_shadow_base_names():
    assert not set(skins.SKINS) & set(props.SKINS)
    assert not set(skins.SKINS) & set(props.BASE)


@pytest.mark.parametrize(
    "name", sorted(set(materials.WALLPAPERS) | set(skins.WALLPAPERS))
)
def test_every_wallpaper_renders(name):
    pattern = materials.wallpaper_pattern(name)
    assert f'id="{materials.wallpaper_id(name)}"' in pattern
    well_formed(f"<defs>{pattern}</defs>")


def test_unknown_names_are_rejected():
    pack = copy.deepcopy(settings.load("liner"))
    pack["visual"]["skins"]["chair"] = "no_such_skin"
    with pytest.raises(ValueError, match="unknown skin"):
        settings.validate(pack)
    pack = copy.deepcopy(settings.load("liner"))
    pack["rooms"][0]["wallpaper"] = "no_such_wallpaper"
    with pytest.raises(ValueError, match="unknown wallpaper"):
        settings.validate(pack)


def test_titles_and_blurbs_may_not_leak_rooms_objects_people_or_directions():
    base = settings.load("train")
    for leak in ("Dining Car", "milk churn", "Basil", "left"):
        pack = copy.deepcopy(base)
        pack["blurbs"] = pack["blurbs"] + [f"Nobody expected the {leak} tonight."]
        with pytest.raises(ValueError, match="mentions"):
            settings.validate(pack)


@pytest.fixture(scope="module")
def demo_cases():
    return [glasshouse().case, lily_pond().case]


@pytest.mark.parametrize("setting_id", settings.available())
def test_dressing_never_changes_the_case(setting_id, demo_cases):
    for case in demo_cases:
        before = (case.content_hash(), json.dumps(case.to_json(), sort_keys=True))
        theme = settings.dress(case, setting_id)
        after = (case.content_hash(), json.dumps(case.to_json(), sort_keys=True))
        assert before == after
        assert theme.setting_id == setting_id
        assert settings.dress(case, setting_id).to_json() == theme.to_json()
        theme.validate(case)


@pytest.mark.parametrize("setting_id", settings.available())
def test_dressed_boards_render_with_their_names_and_frame(setting_id, demo_cases):
    case = demo_cases[0]
    theme = settings.dress(case, setting_id)
    obs = public_observation(Scratchpad(case, theme))
    svg = art.scene_svg(obs, style="casebook")
    ET.fromstring(svg)
    pack = settings.load(setting_id)
    assert f'url(#mk-g-{frames.get(pack["visual"]["frame"])["fill"]})' in svg
    for area in obs["scene"]["areas"]:
        assert html.escape(area["name"], quote=True) in svg
    for prop in obs["scene"]["props"]:
        assert f'data-prop="{prop["id"]}"' in svg


def test_epilogue_fills_every_field(demo_cases):
    case = demo_cases[0]
    theme = settings.dress(case, "theatre")
    murderer = next(p for p in case.characters if p != case.victim)
    line = settings.epilogue(theme, case, murderer, 0)
    assert "{" not in line and theme.area(0) in line
