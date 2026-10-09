import random
import pytest
from murdoku_lab.setter.scene_spec import normalize_spec, sampling_rates
from murdoku_lab.setter.sampler import gen_scene
from murdoku_lab.core.board import OBJECTS


def test_density_budget_reaches_the_scene_before_clue_generation():
    palette = tuple(
        p for p in ("chair", "table", "bed", "carpet", "shelf", "tv") if p in OBJECTS
    )
    spec = normalize_spec(
        {
            "schema": "murdoku.scene_spec/1",
            "blocker_rate": 0.14,
            "furniture_rate": 0.30,
        },
        size=8,
    )
    base = gen_scene(8, 4, random.Random(1), objects=palette)
    dense = gen_scene(8, 4, random.Random(1), objects=palette, **sampling_rates(spec))
    assert sum(len(p.cells) for p in base.props) == int(64 * 0.14) + int(64 * 0.10)
    assert sum(len(p.cells) for p in dense.props) == int(64 * 0.14) + int(64 * 0.30)
    assert len(dense.open_cells) >= 8


@pytest.mark.parametrize("rate", [True, -0.1, 0.7, float("nan"), float("inf")])
def test_invalid_density_is_rejected(rate):
    with pytest.raises(ValueError):
        normalize_spec(
            {"schema": "murdoku.scene_spec/1", "furniture_rate": rate}, size=8
        )


def test_excess_combined_density_is_rejected():
    with pytest.raises(ValueError):
        normalize_spec(
            {
                "schema": "murdoku.scene_spec/1",
                "blocker_rate": 0.4,
                "furniture_rate": 0.4,
            },
            size=8,
        )


def test_unspecified_budget_preserves_defaults():
    assert (
        sampling_rates(normalize_spec({"schema": "murdoku.scene_spec/1"}, size=8)) == {}
    )
