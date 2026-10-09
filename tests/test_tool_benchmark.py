"""The public runner preserves collected visual queries and screenshot feedback."""

import asyncio
import json

from murdoku_lab.core.theme import canonical_theme
from murdoku_lab.core.render import cell_label
from murdoku_lab.evaluation.tools import main, p
from murdoku_lab.setter.export_queries import export_case


def test_prepared_visual_query_runs_through_shared_benchmark(
    base_case, tmp_path, monkeypatch
):
    import urllib.request

    bundle = tmp_path / "bundle"
    record = export_case(
        base_case, canonical_theme(base_case), bundle, views=("vision",)
    )["vision"]
    original_prompt = "Keep the exact collection prompt; solve from the screenshot."
    record["messages"][0]["content"] = original_prompt
    query = bundle / "query.jsonl"
    query.write_text(json.dumps(record) + "\n")
    endpoint = tmp_path / "endpoint.json"
    endpoint.write_text(
        json.dumps({"base_url": "http://fixture/v1", "model": "fixture"})
    )
    submit = {
        "action": "submit",
        "placements": {
            p: cell_label(base_case, k) for p, k in base_case.solution.items()
        },
        "murderer": base_case.answer_key,
    }
    actions = [{"action": "board"}, submit]
    requests = []

    class Response:
        def __init__(self, payload):
            self.payload = json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return self.payload

    def respond(request, timeout=0):
        payload = json.loads(request.data)
        if request.full_url.endswith("/tokenize"):
            return Response({"count": 200})
        requests.append(payload)
        return Response(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Use the visible board.",
                            "tool_calls": [
                                {
                                    "id": str(len(requests)),
                                    "type": "function",
                                    "function": {
                                        "name": "murdoku",
                                        "arguments": json.dumps(
                                            actions[len(requests) - 1]
                                        ),
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {"completion_tokens": 100},
            }
        )

    monkeypatch.setattr(urllib.request, "urlopen", respond)
    output = tmp_path / "output"
    args = p.parse_args(
        [
            "--input",
            str(query),
            "--endpoint",
            str(endpoint),
            "--out",
            str(output),
            "--turns",
            "2",
            "--keep-input-protocol",
            "--asset-root",
            str(bundle),
        ]
    )
    asyncio.run(main(args))
    assert len(requests) == 2
    assert all(r["messages"][0]["content"] == original_prompt for r in requests)
    assert requests[0]["messages"][1]["content"][1]["image_url"]["url"].startswith(
        "data:image/png;base64,"
    )
    frames = [m for m in requests[1]["messages"] if m["role"] == "user"]
    assert len(frames) == 2 and frames[-1]["content"][1]["image_url"]["url"].startswith(
        "data:image/png;base64,"
    )
    summary = json.loads((output / "summary.json").read_text())
    assert summary["solved"] == 1 and summary["results"][0]["termination"] == "terminal"
