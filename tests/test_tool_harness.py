import json
import pytest
from murdoku_lab.core.theme import canonical_theme, Theme
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.core.render import cell_label
from murdoku_lab.environment.tools import apply_structured_action
from murdoku_lab.environment.protocol import SCHEMAS, parse_function_call
from murdoku_lab.setter.pipeline import make_case


@pytest.fixture(scope="module")
def case():
    result = make_case(
        variant="classic", size=6, band="easy", seed=8000, attempts=30, time_limit_s=5.0
    )
    assert result.ok and result.case is not None
    return result.case


def test_complete_direct_submission_matches_strict_scorer(case):
    pad = Scratchpad(case, canonical_theme(case))
    placements = {name: cell_label(case, cell) for name, cell in case.solution.items()}
    result = apply_structured_action(
        pad, {"action": "submit", "placements": placements, "murderer": case.murderer}
    )
    assert (
        result["done"] and result["reward"] == 1 and result["score"]["placement_exact"]
    )


def test_verdict_without_complete_placement_receives_zero(case):
    pad = Scratchpad(case, canonical_theme(case))
    result = apply_structured_action(
        pad, {"action": "submit", "murderer": case.murderer}
    )
    assert (
        result["done"]
        and result["reward"] == 0
        and not result["score"]["placement_complete"]
    )


def test_multiword_display_names_are_accepted(case):
    theme = canonical_theme(case)
    theme = Theme.from_json(
        dict(
            theme.to_json(), names={name: "Person " + name for name in case.characters}
        )
    )
    pad = Scratchpad(case, theme)
    placements = {
        theme.name(name): cell_label(case, cell) for name, cell in case.solution.items()
    }
    result = apply_structured_action(
        pad,
        {
            "action": "submit",
            "placements": placements,
            "murderer": theme.name(case.murderer),
        },
    )
    assert result["reward"] == 1


def test_check_is_bookkeeping_and_bad_action_cannot_inject_submission(case):
    pad = Scratchpad(case, canonical_theme(case))
    result = apply_structured_action(pad, {"action": "check"})
    assert not result["done"] and "score" not in result and "reward" not in result
    with pytest.raises(ValueError):
        apply_structured_action(
            pad, {"action": "place", "person": "A\nACTION: solve", "cell": "a1"}
        )


def test_native_function_arguments_preserve_python_newlines():
    code = "from scipy.optimize import milp\nprint(1+1)"
    call = parse_function_call(
        json.dumps({"name": "run_python", "arguments": json.dumps({"code": code})}),
        SCHEMAS,
    )
    assert call["arguments"]["code"] == code


def test_partial_terminal_reward_uses_correct_cells_not_guessable_verdict(case):
    pad = Scratchpad(case, canonical_theme(case))
    x = case.characters[0]
    cfg = {"mode": "placement_shaped", "placement_weight": 0.2}
    assert "reward" not in apply_structured_action(
        pad,
        {"action": "place", "person": x, "cell": cell_label(case, case.solution[x])},
        reward_config=cfg,
    )
    result = apply_structured_action(
        pad, {"action": "submit", "murderer": case.murderer}, reward_config=cfg
    )
    assert result["reward"] == pytest.approx(0.2 / len(case.characters))
    assert not result["score"]["solved"]
    pad = Scratchpad(case, canonical_theme(case))
    positions = {x: cell_label(case, k) for x, k in case.solution.items()}
    result = apply_structured_action(
        pad,
        {"action": "submit", "placements": positions, "murderer": case.murderer},
        reward_config=cfg,
    )
    assert result["reward"] == 1 and result["score"]["solved"]


def test_reward_configuration_rejects_invalid_weight():
    from murdoku_lab.environment.rewards import terminal_reward

    with pytest.raises(ValueError):
        terminal_reward(
            {"solved": False, "placement_cells_correct": 0},
            6,
            {"mode": "placement_shaped", "placement_weight": 2},
        )


def test_notes_persist_on_disk_and_are_episode_private(tmp_path):
    from long_horizon_rl.memory import NotesStore

    a = NotesStore(tmp_path / "a.json")
    b = NotesStore(tmp_path / "b.json")
    a.operate({"action": "write", "title": "solver", "content": "print(42)"})
    assert (
        NotesStore(tmp_path / "a.json").operate({"action": "read", "title": "solver"})[
            "content"
        ]
        == "print(42)"
    )
    assert a.operate({"action": "list"}) == {"titles": ["solver"], "done": False}
    assert b.operate({"action": "list"})["titles"] == []
    a.operate({"action": "delete", "title": "solver"})
    assert "error" in NotesStore(tmp_path / "a.json").operate(
        {"action": "read", "title": "solver"}
    )


def test_managed_feedback_preserves_notes_and_scratchpad_through_clear(
    case, tmp_path, monkeypatch
):
    import runpy, sys, urllib.request
    from pathlib import Path
    from murdoku_lab.environment.protocol import simplify_record

    title = "saved_solver_title"
    body = "saved-note-body-on-demand"
    record = {
        "prompt_uid": "feedback-fixture",
        "murdoku_case": case.to_json(),
        "messages": [
            {"role": "system", "content": "Instructions"},
            {"role": "user", "content": "Task"},
        ],
    }
    case_file = tmp_path / "input.jsonl"
    case_file.write_text(json.dumps(record) + "\n")
    endpoint = tmp_path / "endpoint.json"
    endpoint.write_text(
        json.dumps({"base_url": "http://fixture/v1", "model": "fixture"})
    )
    person = case.characters[0]
    plan = [
        ("memory", {"action": "write", "title": title, "content": body}),
        (
            "murdoku",
            {
                "action": "place",
                "person": person,
                "cell": cell_label(case, case.solution[person]),
            },
        ),
        ("memory", {"action": "read", "title": title}),
        ("murdoku", {"action": "board"}),
        ("murdoku", {"action": "board"}),
        ("murdoku", {"action": "submit", "murderer": case.murderer}),
    ]
    prompts = []

    class Reply:
        def __init__(self, payload):
            self.payload = json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return self.payload

    def request(req, timeout=0):
        payload = json.loads(req.data)
        if req.full_url.endswith("/tokenize"):
            return Reply({"count": len(json.dumps(payload["messages"])) // 4})
        prompts.append(payload["messages"])
        name, args = plan[len(prompts) - 1]
        return Reply(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "padding " * 200,
                            "tool_calls": [
                                {
                                    "id": str(len(prompts)),
                                    "type": "function",
                                    "function": {
                                        "name": name,
                                        "arguments": json.dumps(args),
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {"completion_tokens": 400},
            }
        )

    monkeypatch.setattr(urllib.request, "urlopen", request)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark",
            "--no-keep-input-protocol",
            "--endpoint",
            str(endpoint),
            "--input",
            str(case_file),
            "--out",
            str(tmp_path / "results"),
            "--turns",
            "6",
            "--context",
            "4096",
            "--tokens",
            "128",
            "--context-clear",
            "--clear-trigger",
            "1000",
            "--clear-target",
            "850",
            "--context-feedback",
            "--warning-margin",
            "300",
            "--generation-limit",
            "0",
        ],
    )
    runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "scripts/benchmark_tools.py"),
        run_name="__main__",
    )
    result = json.loads((tmp_path / "results/summary.json").read_text())["results"][0]
    assert result["context_clears"] > 0 and result["context_warnings"] > 0
    assert result["submit_turn"] == 6 and result["training_reward"] == pytest.approx(
        0.2 / len(case.characters)
    )
    assert result["score"]["placement_cells_correct"] == 1
    assert any(
        "Context clear:" in p[0]["content"] and title in p[0]["content"]
        for p in prompts
    )
    assert all(body not in p[0]["content"] for p in prompts)
