import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: real work rather than a unit check (deselect with -m 'not slow')",
    )


import json
import pytest
from murdoku_lab.core.instance import Case


@pytest.fixture
def base_case():
    return Case.from_json(
        json.loads(
            (Path(__file__).parent / "fixtures" / "quality_base_case.json").read_text()
        )
    )


@pytest.fixture
def puzzle_record(base_case):
    from murdoku_lab.environment.queries import make_record

    return make_record(base_case)
