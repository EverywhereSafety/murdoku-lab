"""Share cards and thumbnails show public facts only: they cannot spoil a case."""

import re
from xml.etree import ElementTree as ET

import pytest

from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.setter import settings
from murdoku_lab.visual import art
from murdoku_lab.visual.art import cards
from murdoku_lab.visual.demos import glasshouse
from murdoku_lab.visual.projection import public_observation

COORDINATE = re.compile(r"\b[a-p](?:1[0-6]|[1-9])\b")


@pytest.fixture(scope="module")
def dressed():
    entry = glasshouse()
    return entry.case, settings.dress(entry.case, "theatre")


@pytest.mark.parametrize("layout", tuple(cards.LAYOUTS))
@pytest.mark.parametrize("state", cards.STATES)
def test_cards_render_and_never_name_the_culprit_or_a_square(dressed, layout, state):
    case, theme = dressed
    card = cards.card_for(
        case, theme, state=state, number=7, stars=2, hints=1, url="example.org/d/7"
    )
    svg = art.share_card_svg(card, layout)
    root = ET.fromstring(svg)
    width, height = cards.LAYOUTS[layout]
    assert root.attrib["width"] == str(width) and root.attrib["height"] == str(height)
    words = " ".join(root.itertext())
    assert theme.title.split()[0] in words
    assert "GUILTY" not in words and not COORDINATE.search(words)
    # No one is named at all, so neither is the culprit.
    for person in case.characters:
        assert theme.name(person) not in words


def test_card_faces_are_the_suspects_not_the_victim(dressed):
    case, theme = dressed
    card = cards.card_for(case, theme)
    obs = public_observation(Scratchpad(case, theme))
    victim = next(p for p in obs["people"] if p.get("victim"))
    assert victim["look"] not in card["faces"]
    assert set(card) >= {"title", "setting", "size", "state", "faces"}
    assert not set(card) & {"solution", "murderer", "answer", "placements"}


def test_thumbnail_is_the_static_scene_only(dressed):
    case, theme = dressed
    obs = public_observation(Scratchpad(case, theme))
    obs["placements"] = {case.characters[0]: obs["scene"]["cells"][0]["cell"]}
    root = ET.fromstring(art.thumbnail_svg(obs, px=320))
    assert root.attrib["width"] == "320"
    assert not [n for n in root.iter() if "data-cell" in n.attrib]
    assert not [n for n in root.iter() if n.attrib.get("class") == "placement-notes"]
