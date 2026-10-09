"""Publishing and evaluation keep dataset identities and independent attempts intact."""

import asyncio
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from murdoku_lab.environment import release
from murdoku_lab.evaluation import tools


def test_case_split_gate_preserves_existing_output(
    puzzle_record, tmp_path, monkeypatch
):
    source, output = tmp_path / "input.jsonl", tmp_path / "query_rollouts.jsonl"
    output.write_text("old complete release\n")
    first = deepcopy(puzzle_record)
    first["split"] = "train"
    second = deepcopy(first)
    second["prompt_uid"] += "-vision"
    second["murdoku_observation"] = "vision"
    second["split"] = "test"
    source.write_text(
        "\n".join(json.dumps({"query": q, "rollout": None}) for q in (first, second))
        + "\n"
    )
    monkeypatch.setattr("sys.argv", ["export", str(source), "--output", str(output)])
    with pytest.raises(ValueError, match="multiple splits"):
        release.main()
    assert output.read_text() == "old complete release\n"
    second["split"] = "train"
    source.write_text(
        "\n".join(json.dumps({"query": q, "rollout": None}) for q in (first, second))
        + "\n"
    )
    release.main()
    assert len(output.read_text().splitlines()) == 2
    first["paired_case_id"] = "false-group"
    with pytest.raises(ValueError, match="paired_case_id"):
        release.release_row({"query": first, "rollout": None})


def test_release_drops_provenance_and_rejects_changed_tools(puzzle_record):
    q = deepcopy(puzzle_record)
    q["split"] = "train"
    trace = {
        "prompt_uid": q["prompt_uid"],
        "messages": deepcopy(q["messages"]),
        "tools": [
            {"type": "function", "function": deepcopy(s)} for s in q["tool_schemas"]
        ],
        "replay_strict_success": True,
        "provenance": {
            "teacher_model": "example/model",
            "revision": "known-revision",
            "sampling": {
                "temperature": 1,
                "seed": 7,
                "worker_path": "/storage/private",
            },
            "candidate_file": "/storage/private",
        },
    }
    row = {"query": q, "rollout": trace}
    clean = release.release_row(row)
    assert "provenance" not in clean["rollout"]
    assert "private" not in json.dumps(clean)
    trace["tools"][0]["function"]["parameters"]["required"] = ["wrong"]
    with pytest.raises(ValueError, match="tool schema"):
        release.release_row(row)


@pytest.mark.parametrize("unified", [False, True])
def test_eval_rejects_old_notes_before_environment_start(
    puzzle_record, tmp_path, monkeypatch, unified
):
    query = tmp_path / "query.jsonl"
    query.write_text(
        json.dumps(
            {"query": puzzle_record, "rollout": None} if unified else puzzle_record
        )
        + "\n"
    )
    endpoint = tmp_path / "endpoint.json"
    endpoint.write_text('{"model":"unused","base_url":"http://unused/v1"}')
    note = tmp_path / (puzzle_record["prompt_uid"] + ".memory.json")
    note.write_text("old note")
    args = tools.p.parse_args(
        ["--input", str(query), "--out", str(tmp_path), "--endpoint", str(endpoint)]
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("environment/model must not start")

    monkeypatch.setattr(tools, "make_environment", forbidden)
    with pytest.raises(ValueError, match="existing attempt artifacts"):
        asyncio.run(tools.main(args))
    assert note.read_text() == "old note"
    note.unlink()
    # A pre-created input-only directory passes conflict validation. A factory
    # failure is then recorded per case instead of aborting the batch.
    asyncio.run(tools.main(args))
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["infrastructure_failures"] == 1
    attempt = json.loads(
        (tmp_path / (puzzle_record["prompt_uid"] + ".json")).read_text()
    )
    assert "must not start" in attempt["events"][0]["error"]


def test_download_snapshot_is_transactional(tmp_path, monkeypatch):
    path = Path(__file__).parents[1] / "scripts/download_data.py"
    spec = importlib.util.spec_from_file_location("download_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshot, output = tmp_path / "source", tmp_path / "data"
    snapshot.mkdir()
    (snapshot / "query_rollouts.jsonl").write_text("first\n")
    (snapshot / "LICENSE-Fluent.txt").write_text("artwork license\n")
    first = module.install_snapshot(snapshot, output, "example/repo", "rev-one")
    assert (output / "LICENSE-Fluent.txt").read_text() == "artwork license\n"
    assert "LICENSE-Fluent.txt" in first["files"]
    assert module.install_snapshot(snapshot, output, "example/repo", "rev-one") == first
    (snapshot / "query_rollouts.jsonl").write_text("second\n")
    with pytest.raises(ValueError, match="different snapshot"):
        module.install_snapshot(snapshot, output, "example/repo", "rev-two")

    def broken(*args):
        raise OSError("copy interrupted")

    monkeypatch.setattr(module.shutil, "copyfile", broken)
    with pytest.raises(OSError, match="interrupted"):
        module.install_snapshot(
            snapshot, tmp_path / "new-data", "example/repo", "rev-two"
        )
    assert (output / "query_rollouts.jsonl").read_text() == "first\n"
    assert json.loads((output / "receipt.json").read_text()) == first


@pytest.mark.parametrize("text", ["lounge/storage/foyer", "/home/**/*png*"])
def test_release_path_guard_allows_room_lists_and_generic_globs(text):
    assert release.INTERNAL.search(text) is None


@pytest.mark.parametrize(
    "text", ["/storage/ice1/user/file", "/Users/name/file", "/home/name/file"]
)
def test_release_path_guard_rejects_private_paths(text):
    assert release.INTERNAL.search(text) is not None


@pytest.mark.parametrize("view", ["text", "vision"])
def test_release_rejects_different_rollout_prompt_in_both_views(puzzle_record, view):
    query = deepcopy(puzzle_record)
    query["split"] = "train"
    query["murdoku_observation"] = view
    if view == "vision":
        query["messages"][1]["content"] = [
            {"type": "text", "text": "Read the board."},
            {"type": "image_url", "image_url": {"url": "images/board.png"}},
        ]
    rollout = {
        "prompt_uid": query["prompt_uid"],
        "messages": deepcopy(query["messages"]),
        "tools": [
            {"type": "function", "function": deepcopy(s)} for s in query["tool_schemas"]
        ],
        "replay_strict_success": True,
    }
    row = {"query": query, "rollout": rollout}
    assert release.release_row(row)["rollout"]["messages"] == query["messages"]
    if view == "vision":
        rollout["messages"][1]["content"][1]["image_url"]["url"] = "images/other.png"
    else:
        rollout["messages"][0]["content"] += "Use a different tool."
    with pytest.raises(ValueError, match="rollout prompt differs"):
        release.release_row(row)


@pytest.mark.parametrize("bad_input", ["missing", "checksum", "outside"])
def test_bad_visual_input_does_not_start_environment_or_abort_batch(
    puzzle_record, tmp_path, monkeypatch, bad_input
):
    good = deepcopy(puzzle_record)
    good["prompt_uid"] = "good"
    bad = deepcopy(good)
    bad["prompt_uid"] = "bad"
    bad["murdoku_observation"] = "vision"
    path = "board.png" if bad_input != "outside" else "../outside.png"
    bad["messages"][1]["content"] = [{"type": "image_url", "image_url": {"url": path}}]
    if bad_input == "checksum":
        (tmp_path / path).write_bytes(b"different image")
        bad["image_assets"] = [{"path": path, "sha256": "wrong"}]
    created, closed = [], []

    class Environment:
        memory = {}
        done = False

        async def start(self):
            return self

        async def finalize(self, reason):
            return {"reward": 0, "score": None}

        async def close(self):
            closed.append("good")

    def factory(record, **kwargs):
        created.append(record["prompt_uid"])
        assert record["prompt_uid"] == "good"
        return Environment()

    monkeypatch.setattr(tools, "make_environment", factory)
    source, endpoint, output = (
        tmp_path / "input.jsonl",
        tmp_path / "endpoint.json",
        tmp_path / "out",
    )
    source.write_text("\n".join(json.dumps(q) for q in [bad, good]) + "\n")
    endpoint.write_text('{"model":"unused","base_url":"http://unused/v1"}')
    args = tools.p.parse_args(
        [
            "--input",
            str(source),
            "--endpoint",
            str(endpoint),
            "--out",
            str(output),
            "--turns",
            "0",
        ]
    )
    asyncio.run(tools.main(args))
    summary = json.loads((output / "summary.json").read_text())
    failed = json.loads((output / "bad.json").read_text())
    assert created == closed == ["good"]
    assert summary["cases"] == 2
    assert summary["invalid_inputs"] == summary["invalid_attempts"] == 1
    assert summary["infrastructure_failures"] == 0
    assert failed["result"]["termination"] == "invalid_input"
    assert failed["result"]["reward"] is None
    assert failed["events"][0]["phase"] == "input"


@pytest.mark.parametrize("failure", ["start", "close"])
def test_environment_lifecycle_failure_is_recorded_and_batch_continues(
    puzzle_record, tmp_path, monkeypatch, failure
):
    created, closed = [], []

    class Environment:
        memory = {}
        done = False

        def __init__(self, uid):
            self.uid = uid

        async def start(self):
            if self.uid == "bad" and failure == "start":
                raise RuntimeError("startup failed")
            return self

        async def finalize(self, reason):
            return {"reward": 0, "score": None}

        async def close(self):
            closed.append(self.uid)
            if self.uid == "bad" and failure == "close":
                raise RuntimeError("cleanup failed")

    def factory(record, **kwargs):
        created.append(record["prompt_uid"])
        return Environment(record["prompt_uid"])

    monkeypatch.setattr(tools, "make_environment", factory)
    rows = [dict(deepcopy(puzzle_record), prompt_uid=uid) for uid in ["bad", "good"]]
    source, endpoint, output = (
        tmp_path / "input.jsonl",
        tmp_path / "endpoint.json",
        tmp_path / "out",
    )
    source.write_text("\n".join(json.dumps(q) for q in rows) + "\n")
    endpoint.write_text('{"model":"unused","base_url":"http://unused/v1"}')
    args = tools.p.parse_args(
        [
            "--input",
            str(source),
            "--endpoint",
            str(endpoint),
            "--out",
            str(output),
            "--turns",
            "0",
        ]
    )
    asyncio.run(tools.main(args))
    summary = json.loads((output / "summary.json").read_text())
    failed = json.loads((output / "bad.json").read_text())
    assert created == closed == ["bad", "good"]
    assert summary["cases"] == 2
    assert summary["infrastructure_failures"] == summary["invalid_attempts"] == 1
    assert summary["invalid_inputs"] == 0
    assert failed["result"]["reward"] is None
    assert failed["result"]["termination"] == "request_or_environment_failure"
