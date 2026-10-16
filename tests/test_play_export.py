"""Player case bundles: public facts in the clear, answers sealed, nothing else leaks."""

import json

import pytest

from murdoku_lab.visual import play_export
from murdoku_lab.visual.seal import seal, unseal


@pytest.fixture(scope="module")
def library(tmp_path_factory):
    out = tmp_path_factory.mktemp("cases")
    index = play_export.export(out, thumbs=False)
    return out, index


def test_seal_vectors_round_trip():
    from pathlib import Path

    vectors = json.loads(
        (Path(__file__).parent / "fixtures" / "seal_vectors.json").read_text()
    )
    for v in vectors:
        assert seal(v["value"], v["id"], v["salt"]) == v["sealed"]
        assert unseal(v["sealed"], v["id"], v["salt"]) == v["value"]


def test_library_lists_every_bundle(library):
    out, index = library
    assert index["schema"] == play_export.LIBRARY
    assert {c["id"] for c in index["cases"]} >= {"glasshouse", "lily-pond", "estate"}
    for entry in index["cases"]:
        assert (out / entry["url"]).exists()
        assert (out / f"{entry['id']}.day.svg").exists()
        assert (out / f"{entry['id']}.night.svg").exists()


def test_bundles_keep_answers_sealed(library):
    out, index = library
    for entry in index["cases"]:
        bundle = json.loads((out / entry["url"]).read_text())
        assert bundle["schema"] == play_export.SCHEMA
        secret = unseal(bundle["secret"], bundle["id"])
        assert set(secret["solution"]) == {p["id"] for p in bundle["public"]["people"]}
        public = json.dumps(bundle["public"]) + json.dumps(bundle["meta"])
        for field in play_export.SESSION_FIELDS:
            assert field not in bundle["public"]
        assert "solution" not in public and "murderer" not in bundle["public"]
        pairs = [f'"{p}": "{c}"' for p, c in secret["solution"].items()]
        assert not any(pair in public for pair in pairs)
        if secret["goal_type"] == "murderer":
            assert secret["murderer"] in secret["solution"]


def test_static_scenes_hold_no_people_or_hit_targets(library):
    out, index = library
    svg = (out / f"{index['cases'][0]['id']}.day.svg").read_text()
    assert 'class="cell-hit"' not in svg and "placement-notes" not in svg
    assert 'data-style="casebook"' in svg


def test_hint_data_is_sound(library):
    out, index = library
    for entry in index["cases"]:
        bundle = json.loads((out / entry["url"]).read_text())
        secret = unseal(bundle["secret"], bundle["id"])
        hints, solution = secret["hints"], secret["solution"]
        assert sorted(hints["order"]) == sorted(solution)
        for person, cell in solution.items():
            assert cell in hints["candidates"][person]
            assert cell not in hints["forbid"][person], (entry["id"], person, cell)


def test_restyled_classics_keep_their_words_and_take_the_packs_look(library):
    """The large built-in cases are drawn with a setting pack's look in the player, but their
    title, setting name and every clue read exactly as written."""
    from murdoku_lab.environment.state import Scratchpad
    from murdoku_lab.setter import settings
    from murdoku_lab.visual import demos
    from murdoku_lab.visual.projection import public_observation

    out, _ = library
    for slug, spec in settings.restyles().items():
        entry = demos.catalogue()[slug]
        bundle = json.loads((out / f"{slug}.json").read_text())
        assert bundle["kind"] == "classic"
        assert bundle["meta"]["title"] == entry.theme.title
        assert bundle["meta"]["setting"] == {"id": spec["look"], "name": entry.setting}
        assert bundle["meta"]["frame"] == settings.load(spec["look"])["visual"]["frame"]
        written = public_observation(Scratchpad(entry.case, entry.theme))["clues"]
        assert [c["text"] for c in bundle["public"]["clues"]] == [
            c["text"] for c in written
        ]
