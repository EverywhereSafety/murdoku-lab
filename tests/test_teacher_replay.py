import asyncio, json
import pytest
from murdoku_lab.core.instance import Case
from murdoku_lab.core.render import cell_label
from murdoku_lab.environment.replay import replay_candidate


def fixture(record):
    case = Case.from_json(record["murdoku_case"])
    args = {
        "action": "submit",
        "placements": {p: cell_label(case, k) for p, k in case.solution.items()},
        "murderer": case.answer_key,
    }
    return record, {
        "events": [
            {
                "text": "Submitting the arrangement.",
                "tool_calls": [
                    {
                        "id": "test-call",
                        "type": "function",
                        "function": {"name": "murdoku", "arguments": json.dumps(args)},
                    }
                ],
            }
        ]
    }


def test_correct_full_submission_replayed_without_private_grading_fields(puzzle_record):
    record, candidate = fixture(puzzle_record)
    trace = asyncio.run(replay_candidate(record, candidate))
    assert trace["replay_strict_success"]
    tool = json.loads(trace["messages"][-1]["content"])
    assert not {"score", "reward", "final_state_variable"} & tool.keys()


def test_claimed_success_does_not_override_wrong_submission(puzzle_record):
    record, candidate = fixture(puzzle_record)
    candidate["result"] = {"reward": 1, "score": {"solved": True}}
    f = candidate["events"][0]["tool_calls"][0]["function"]
    args = json.loads(f["arguments"])
    args["placements"] = {}
    args["murderer"] = "wrong"
    f["arguments"] = json.dumps(args)
    with pytest.raises(ValueError, match="not strictly correct"):
        asyncio.run(replay_candidate(record, candidate))


def test_no_submission_is_rejected(puzzle_record):
    record, candidate = fixture(puzzle_record)
    candidate["events"][0]["tool_calls"][0]["function"][
        "arguments"
    ] = '{"action":"board"}'
    with pytest.raises(ValueError, match="never submitted"):
        asyncio.run(replay_candidate(record, candidate))


def test_teacher_reasoning_is_preserved_for_sft(puzzle_record):
    record, candidate = fixture(puzzle_record)
    candidate["events"][0]["reasoning"] = "I checked the row and column constraints."
    trace = asyncio.run(replay_candidate(record, candidate))
    assert (
        trace["messages"][-2]["reasoning_content"]
        == candidate["events"][0]["reasoning"]
    )


@pytest.mark.parametrize("legacy_version", [None, 5, 6, 7])
def test_replay_preserves_collected_query_and_workspace(puzzle_record, legacy_version):
    from copy import deepcopy

    record, candidate = fixture(puzzle_record)
    record["messages"][0]["content"] = "The exact instructions used during collection."
    if legacy_version is not None:
        record["murdoku_protocol_version"] = legacy_version
    calls = [
        {
            "id": "write",
            "type": "function",
            "function": {
                "name": "workspace",
                "arguments": json.dumps(
                    {"action": "write", "path": "solver.py", "content": "print(42)"}
                ),
            },
        },
        {
            "id": "read",
            "type": "function",
            "function": {
                "name": "workspace",
                "arguments": json.dumps({"action": "read", "path": "solver.py"}),
            },
        },
    ]
    candidate["events"].insert(0, {"tool_calls": calls})
    before = deepcopy(record)
    trace = asyncio.run(replay_candidate(record, candidate))
    assert record == before
    assert trace["messages"][: len(record["messages"])] == record["messages"]
    assert trace["tools"] == [
        {"type": "function", "function": s} for s in record["tool_schemas"]
    ]
    replies = [
        json.loads(m["content"]) for m in trace["messages"] if m["role"] == "tool"
    ]
    assert replies[1]["content"] == "print(42)"
    assert trace["turns"] == 2


def test_replay_checks_recoverable_error_consistency(puzzle_record):
    record, candidate = fixture(puzzle_record)
    candidate["events"].insert(
        0,
        {
            "tool_calls": [
                {
                    "id": "bad",
                    "type": "function",
                    "function": {
                        "name": "workspace",
                        "arguments": json.dumps(
                            {"action": "read", "path": "../outside"}
                        ),
                    },
                }
            ],
            "observations": [{"error": "invalid path"}],
        },
    )
    trace = asyncio.run(
        replay_candidate(record, candidate, allow_recoverable_errors=True)
    )
    assert trace["recovered_tool_errors"] == 1
    candidate["events"][0]["observations"] = [{}]
    with pytest.raises(ValueError, match="success/error changed"):
        asyncio.run(replay_candidate(record, candidate, allow_recoverable_errors=True))


def test_legacy_inline_query_replays_without_enabling_workspace(puzzle_record):
    from murdoku_lab.environment.protocol import simplify_record

    record = simplify_record(puzzle_record, workspace=False)
    record["murdoku_protocol_version"] = 5
    record["messages"][0]["content"] = "Original inline-only collection prompt."
    record, candidate = fixture(record)
    trace = asyncio.run(replay_candidate(record, candidate))
    assert trace["messages"][:2] == record["messages"]
    assert "workspace" not in {t["function"]["name"] for t in trace["tools"]}
    assert record["python_workspace"] is False
