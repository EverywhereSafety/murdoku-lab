"""Old RL-record compatibility and genuine image observations, without model calls."""

import asyncio
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import canonical_theme
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.environment.queries import (
    frame_message,
    make_record,
    model_inputs,
    public_record,
    public_tool_result,
    vision_statement,
)
from murdoku_lab.core.render import cell_label
from murdoku_lab.environment.replay import replay_candidate
from murdoku_lab.environment.tools import MurdokuToolEnvironment
from murdoku_lab.environment.protocol import SCHEMAS, simplify_record
from murdoku_lab.setter.export_queries import export_case, write_bundle
from murdoku_lab.environment.vision import (
    IllustratedMurdokuEnvironment,
    environment_for,
)


@pytest.fixture(scope="module")
def case():
    return Case.from_json(
        json.loads(
            (Path(__file__).parent / "fixtures/quality_base_case.json").read_text()
        )
    )


def all_keys(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(all_keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(all_keys(v) for v in value))
    return set()


def test_text_records_keep_original_shapes_and_original_harness(case):
    record = make_record(case)
    assert isinstance(record["messages"][0]["content"], str)
    assert isinstance(record["messages"][1]["content"], str)
    assert record["prompt_uid"] == case.content_hash()
    assert {"murdoku", "memory", "workspace", "run_python"} == {
        s["name"] for s in record["tool_schemas"]
    }
    assert record["python_workspace"]
    assert "murdoku_protocol_version" not in record
    assert type(environment_for(record)) is MurdokuToolEnvironment
    legacy = {
        k: v
        for k, v in record.items()
        if k not in ("paired_case_id", "murdoku_observation")
    }
    before = deepcopy(legacy)
    env = MurdokuToolEnvironment(legacy)
    result = asyncio.run(
        env.step({"tool": "murdoku", "arguments": {"action": "board"}})
    )
    assert "image_request" not in result and result["observations"]
    assert legacy == before


def test_old_style_teacher_trace_replays_against_its_original_case(case):
    record = make_record(case)
    record.pop("murdoku_observation")
    record.pop("paired_case_id")
    before = deepcopy(record)
    placements = {p: cell_label(case, k) for p, k in case.solution.items()}
    candidate = {
        "events": [
            {
                "text": "Submitting the arrangement.",
                "tool_calls": [
                    {
                        "id": "legacy-call",
                        "type": "function",
                        "function": {
                            "name": "murdoku",
                            "arguments": json.dumps(
                                {
                                    "action": "submit",
                                    "placements": placements,
                                    "murderer": case.murderer,
                                }
                            ),
                        },
                    }
                ],
            }
        ]
    }
    replay = asyncio.run(replay_candidate(record, candidate))
    assert replay["replay_strict_success"] and record == before
    tool = json.loads(replay["messages"][-1]["content"])
    assert not {"score", "reward", "final_state_variable"} & tool.keys()


def test_paired_export_has_same_case_and_no_geometry_in_visual_text(case, tmp_path):
    records = export_case(case, canonical_theme(case), tmp_path)
    text, vision = records["text"], records["vision"]
    assert text["paired_case_id"] == vision["paired_case_id"] == case.content_hash()
    assert text["murdoku_case"] == vision["murdoku_case"]
    assert text["prompt_uid"] != vision["prompt_uid"]
    public = public_record(vision)
    assert not {
        "murdoku_case",
        "solution",
        "answer_key",
        "certificate",
        "area_of",
        "obj_of",
        "cells",
    } & all_keys(public)
    statement = vision["messages"][1]["content"][0]["text"]
    assert statement == vision_statement(case, canonical_theme(case))
    assert "CLUES" in statement and "AREA NAMES" in statement and "TERMS" in statement
    inputs = model_inputs(vision, asset_root=tmp_path)
    assert set(inputs) == {"messages", "tools"}
    image_url = inputs["messages"][1]["content"][1]["image_url"]["url"]
    data = base64.b64decode(image_url.split(",", 1)[1])
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert hashlib.sha256(data).hexdigest() == vision["image_assets"][0]["sha256"]
    assert not vision["messages"][1]["content"][1]["image_url"]["url"].startswith(
        "data:"
    )


def test_vision_board_is_an_image_request_and_changes_after_an_action(case, tmp_path):
    vision = export_case(case, canonical_theme(case), tmp_path, views=("vision",))[
        "vision"
    ]
    for environment_class in (MurdokuToolEnvironment, IllustratedMurdokuEnvironment):
        env = environment_class(vision)
        first = asyncio.run(
            env.step({"tool": "murdoku", "arguments": {"action": "board"}})
        )
        assert set(first) == {"done", "observations", "image_request"}
        assert "area_of" not in json.dumps(first) and "cells" not in json.dumps(first)
        before = frame_message(env, first["image_request"])
        placed = asyncio.run(
            env.step(
                {
                    "tool": "murdoku",
                    "arguments": {"action": "place", "person": "A", "cell": "a1"},
                }
            )
        )
        assert not placed["done"] and not {"score", "reward"} & placed.keys()
        second = asyncio.run(
            env.step({"tool": "murdoku", "arguments": {"action": "board"}})
        )
        after = frame_message(env, second["image_request"])
        assert before["content"][1] != after["content"][1]


def test_simplifier_preserves_vision_observation_contract(case, tmp_path):
    vision = export_case(case, canonical_theme(case), tmp_path, views=("vision",))[
        "vision"
    ]
    simplified = simplify_record(vision)
    assert simplified["murdoku_observation"] == "vision"
    assert isinstance(simplified["messages"][1]["content"], list)
    assert "does not return a textual tile map" in simplified["messages"][0]["content"]
    assert "case_note" in {s["name"] for s in simplified["tool_schemas"]}


def test_image_reference_integrity_and_public_terminal_filter(case, tmp_path):
    vision = export_case(case, canonical_theme(case), tmp_path, views=("vision",))[
        "vision"
    ]
    path = tmp_path / vision["image_assets"][0]["path"]
    path.write_bytes(b"changed image")
    with pytest.raises(ValueError, match="checksum"):
        model_inputs(vision, asset_root=tmp_path)
    assert public_tool_result(
        {
            "done": True,
            "score": {"solved": True},
            "reward": 1,
            "final_state_variable": 1,
            "observations": ["Submitted."],
        }
    ) == {"done": True, "observations": ["Submitted."]}


def test_text_export_needs_no_image_renderer_and_keeps_identity_and_split(
    case, tmp_path, monkeypatch
):
    import murdoku_lab.visual.raster

    def forbidden(*args, **kwargs):
        raise AssertionError("text-only export must not invoke the image renderer")

    monkeypatch.setattr(murdoku_lab.visual.raster, "png_from_svg", forbidden)
    old = make_record(case)
    old["prompt_uid"] = "legacy-query-001"
    old["split"] = "validation"
    manifest = write_bundle([old], tmp_path / "bundle", views=("text",), time_limit_s=5)
    assert manifest["accepted_cases"] == 1
    exported = json.loads((tmp_path / "bundle/text.rl.jsonl").read_text())
    assert (
        exported["prompt_uid"] == old["prompt_uid"]
        and exported["split"] == "validation"
    )
    assert not (tmp_path / "bundle/images").exists()


from copy import deepcopy
import pytest

from murdoku_lab.environment.release import release_row
from long_horizon_rl.queries import query_from_row
from murdoku_lab.core.instance import Case


def row(record):
    query = deepcopy(record)
    query["split"] = "train"
    return {
        "query": query,
        "rollout": {
            "prompt_uid": query["prompt_uid"],
            "messages": deepcopy(query["messages"])
            + [{"role": "assistant", "content": "Done."}],
            "replay_strict_success": True,
            "tools": [
                {"type": "function", "function": s} for s in query["tool_schemas"]
            ],
        },
    }


def test_minimal_row_preserves_environment_and_message_supervision(puzzle_record):
    source = row(puzzle_record)
    clean = release_row(source)
    assert set(clean) == {"query", "rollout"}
    assert query_from_row(clean) == clean["query"]
    Case.from_json(clean["query"]["murdoku_case"]).self_check()
    assert clean["rollout"]["messages"] == source["rollout"]["messages"]
    assert "tools" in clean["rollout"]


def test_internal_fields_dropped_at_all_structural_layers(puzzle_record):
    source = row(puzzle_record)
    source["rollout_metadata"] = {"job_id": 123}
    source["query"]["provenance"] = {"path": "/storage/private"}
    source["query"]["murdoku_case"]["meta"] = {"model": "internal"}
    source["query"]["murdoku_case"]["seed"] = 999
    source["query"]["messages"][0]["provider"] = "internal"
    source["query"]["tool_schemas"][0]["parameters"]["metadata"] = {"job_id": 123}
    source["rollout"]["provenance"] = {"candidate_file": "/storage/private"}
    clean = release_row(source)
    import json

    text = json.dumps(clean)
    for key in [
        "rollout_metadata",
        "provenance",
        "job_id",
        "provider",
        '"meta"',
        '"seed"',
    ]:
        assert key not in text


def test_internal_strings_are_rejected_without_rewriting_trajectory(puzzle_record):
    source = row(puzzle_record)
    source["rollout"]["messages"][-1]["content"] = "Traceback: /storage/private/code.py"
    with pytest.raises(ValueError, match="Internal path"):
        release_row(source)


def test_query_only_and_unqualified_rollout(puzzle_record):
    source = row(puzzle_record)
    source["rollout"] = None
    assert release_row(source)["rollout"] is None
    source = row(puzzle_record)
    source["rollout"]["replay_strict_success"] = False
    with pytest.raises(ValueError, match="replay-qualified"):
        release_row(source)
