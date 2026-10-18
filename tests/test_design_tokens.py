"""The player app reads colours and geometry from web/src/generated, which must match the art."""

import json

from murdoku_lab.visual.art import design_tokens, tokens
from murdoku_lab.visual.art.geometry import CELL, PAD


def test_generated_tokens_match_the_renderer():
    for name, body in design_tokens.rendered().items():
        path = design_tokens.OUT / name
        assert (
            path.exists()
        ), f"run python -m murdoku_lab.visual.art.design_tokens --write"
        assert path.read_text() == body, f"{name} drifted; rerun design_tokens --write"


def test_token_geometry_is_the_board_geometry():
    values = json.loads((design_tokens.OUT / "tokens.json").read_text())
    assert values["geometry"]["cell"] == CELL and values["geometry"]["pad"] == PAD
    assert values["token"] == tokens.TOKEN
    assert set(values["settings"]) >= {"manor", "liner", "theatre"}
