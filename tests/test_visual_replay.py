"""Screenshot observations survive fresh teacher replay into SFT messages."""

import asyncio
import json
from pathlib import Path
from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import canonical_theme
from murdoku_lab.environment.queries import make_record
from murdoku_lab.core.render import cell_label
from murdoku_lab.environment.replay import replay_candidate


def test_board_frame_is_kept_between_tool_turns():
    root = Path(__file__).resolve().parents[1]
    case = Case.from_json(
        json.loads((root / "tests/fixtures/quality_base_case.json").read_text())
    )
    record = make_record(
        case,
        canonical_theme(case),
        view="vision",
        image_path="initial.png",
        image_bytes=b"\x89PNG\r\n\x1a\nfixture",
    )

    def event(identifier, arguments):
        return {
            "text": "Use the tools.",
            "tool_calls": [
                {
                    "id": identifier,
                    "type": "function",
                    "function": {"name": "murdoku", "arguments": json.dumps(arguments)},
                }
            ],
        }

    candidate = {
        "events": [
            event("board", {"action": "board"}),
            event(
                "submit",
                {
                    "action": "submit",
                    "placements": {
                        p: cell_label(case, k) for p, k in case.solution.items()
                    },
                    "murderer": case.answer_key,
                },
            ),
        ]
    }
    trace = asyncio.run(replay_candidate(record, candidate))
    assert trace["replay_strict_success"]
    frames = [m for m in trace["messages"][2:] if m["role"] == "user"]
    assert len(frames) == 1
    assert frames[0]["content"][1]["image_url"]["url"].startswith(
        "data:image/png;base64,"
    )
    assert trace["messages"].index(frames[0]) < len(trace["messages"]) - 2
