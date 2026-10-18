"""Player case bundles: public facts in the clear, answers sealed, nothing else leaks."""

import json

import pytest

from murdoku_lab.visual import play_export
from murdoku_lab.visual.seal import seal, unseal

# Release identities from the reviewed website PR, before rebuilding its artwork.
EXPECTED_RELEASE_HASHES = {
    "tutorial": "bdc00b96d4d72fbc",
    "glasshouse": "58fb36f5bebe4db6",
    "lily-pond": "e471484f3cf10744",
    "last-place": "d327550a13c79155",
    "estate": "ae95a26b66350e46",
    "museum": "0817fe2c9cf0ddd5",
    "chalet-6x6": "0ee2cf0e88a55ad0",
    "chalet-7x7": "550bb4e8c449e773",
    "chalet-8x8": "7e07605c5448434a",
    "glasshouse-6x6": "4cf6bb6db23627d9",
    "glasshouse-7x7": "c84cdc20ec3fed30",
    "glasshouse-8x8": "4dd0b24e31a9693e",
    "library-6x6": "000e213b408a2df2",
    "library-7x7": "804614d282372238",
    "library-8x8": "a4db2e9e1990f1b0",
    "liner-6x6": "545ee46a2094a79e",
    "liner-7x7": "d61908dd28ab9e54",
    "liner-8x8": "ba29c4f0d6fe7504",
    "manor-6x6": "732a340c49c3f6bf",
    "manor-7x7": "16e68f5180b4cca4",
    "manor-8x8": "82672717c6ba2f9c",
    "museum-6x6": "acb8285aad14dee7",
    "museum-7x7": "ce789ec14fe17047",
    "museum-8x8": "7370b608566a3373",
    "theatre-6x6": "e5ef0aeae2ec3e25",
    "theatre-7x7": "8ddc7b54a73c034c",
    "theatre-8x8": "5e4d795b2a5e9327",
    "train-6x6": "027214b6e8217673",
    "train-7x7": "75bc976307644aaf",
    "train-8x8": "7fbc07d58213b425",
}


@pytest.fixture(scope="module")
def library(tmp_path_factory):
    out = tmp_path_factory.mktemp("cases")
    index = play_export.export(out)
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
    from collections import Counter

    out, index = library
    assert index["schema"] == play_export.LIBRARY
    assert len(index["cases"]) == 30
    assert {
        c["id"]: c["content_hash"] for c in index["cases"]
    } == EXPECTED_RELEASE_HASHES
    assert Counter(c["kind"] for c in index["cases"]) == {
        "themed": 24,
        "classic": 5,
        "tutorial": 1,
    }
    for entry in index["cases"]:
        assert (out / entry["url"]).exists()
        assert (out / f"{entry['id']}.day.svg").exists()
        assert (out / f"{entry['id']}.night.svg").exists()
        assert (out / entry["thumb"]).exists()


def test_frozen_showcase_bundles_survive_export_unchanged(library):
    out, index = library
    frozen = [
        json.loads(line)
        for line in play_export.FROZEN_SHOWCASE.read_text().splitlines()
        if line.strip()
    ]
    assert {data["id"] for data in frozen} == {
        entry["id"] for entry in index["cases"] if entry["kind"] == "themed"
    }
    for data in frozen:
        assert json.loads((out / f"{data['id']}.json").read_text()) == data
        for asset in [*data["scene"].values(), data["thumb"]]:
            svg = (out / asset).read_text()
            assert 'data-revision="0"' in svg
            assert 'data-style="casebook"' in svg
            assert 'class="cell-hit"' not in svg and "placement-notes" not in svg


def test_missing_showcase_preserves_existing_library(tmp_path, monkeypatch):
    monkeypatch.setattr(play_export, "FROZEN_SHOWCASE", tmp_path / "missing.jsonl")
    out = tmp_path / "cases"
    out.mkdir()
    previous = out / "index.json"
    previous.write_text("previous complete library")
    with pytest.raises(FileNotFoundError, match="Missing release showcase"):
        play_export.export(out)
    assert previous.read_text() == "previous complete library"


def test_explicit_records_replace_the_frozen_showcase(tmp_path, monkeypatch):
    monkeypatch.setattr(play_export, "FROZEN_SHOWCASE", tmp_path / "missing.jsonl")
    row = json.loads(play_export.TUTORIAL.read_text())
    row["visual_case_id"] = "custom-training"
    records = tmp_path / "custom.jsonl"
    records.write_text(json.dumps(row) + "\n")
    out = tmp_path / "cases"
    index = play_export.export(out, records=records, thumbs=False)
    assert {entry["id"] for entry in index["cases"]} == {
        "tutorial",
        "glasshouse",
        "lily-pond",
        "last-place",
        "estate",
        "museum",
        "custom-training",
    }
    custom = json.loads((out / "custom-training.json").read_text())
    assert custom["kind"] == "themed"
    assert custom["content_hash"] == EXPECTED_RELEASE_HASHES["tutorial"]
    assert not list(out.glob("*.thumb.svg"))


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


def test_room_plaques_leave_all_doorways_visible(library):
    """Check rendered plaque bounds against door frames on every built-in board."""
    import xml.etree.ElementTree as ET
    from murdoku_lab.visual.art.geometry import door_geometry

    out, index = library
    ns = {"s": "http://www.w3.org/2000/svg"}
    for entry in index["cases"]:
        data = json.loads((out / entry["url"]).read_text())
        observation = data["public"]
        doors = []
        for door in observation["scene"]["doors"]:
            x, y, vertical = door_geometry(observation, door)
            doors.append(
                (x - 12, y - 28, x + 12, y + 28)
                if vertical
                else (x - 28, y - 11, x + 28, y + 30)
            )
        svg = ET.fromstring((out / f"{entry['id']}.day.svg").read_text())
        plaques = svg.findall('.//s:g[@class="room-plaque"]', ns)
        assert plaques
        for plaque in plaques:
            for rect in plaque.findall("s:rect", ns):
                x, y, w, h = (
                    float(rect.attrib[k]) for k in ("x", "y", "width", "height")
                )
                for x1, y1, x2, y2 in doors:
                    assert not (x < x2 and x + w > x1 and y < y2 and y + h > y1), (
                        entry["id"],
                        plaque.attrib,
                    )
