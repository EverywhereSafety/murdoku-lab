"""Public/private boundary, tool parity, terminal semantics and faithful geometry."""

import asyncio
from dataclasses import replace
import json
import threading
import urllib.error
import urllib.request
from xml.etree import ElementTree as ET
import pytest
from murdoku_lab.core.board import Prop, Scene
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.core.render import cell_label
from murdoku_lab.environment.tools import apply_structured_action
from murdoku_lab.visual.art import scene_svg, observation_svg
from murdoku_lab.visual.demos import glasshouse, lily_pond, estate
from murdoku_lab.environment.vision import IllustratedMurdokuEnvironment
from murdoku_lab.visual.projection import public_observation
from murdoku_lab.visual.server import make_server
from murdoku_lab.visual.session import VisualSession, SessionError, StaleRevision


def keys(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(keys(v) for v in value))
    return set()


def test_public_allowlist_excludes_private_fields_and_oracle_data():
    e = glasshouse()
    e = replace(
        e,
        case=replace(
            e.case,
            seed=7654321,
            certificate={"secret": "canary"},
            meta={"canary": "DO_NOT_EXPORT"},
        ),
    )
    session = VisualSession(e)
    state = session.observe()
    assert not keys(state) & {
        "solution",
        "answer_key",
        "seed",
        "certificate",
        "meta",
        "atoms",
        "target_band",
    }
    assert state["placements"] == state["marks"] == {}
    assert "DO_NOT_EXPORT" not in json.dumps(state)
    assert "7654321" not in observation_svg(state)
    result = session.act({"action": "check"})
    assert "score" not in result["result"] and "reward" not in result["result"]
    assert result["observation"]["terminal"] is None


def test_actions_match_existing_harness_including_wrong_claims():
    e = glasshouse()
    session, upstream = VisualSession(e), Scratchpad(e.case, e.theme)
    actions = [
        dict(action="mark", person="A", cell="b1 b2"),
        dict(action="place", person="A", cell="a1"),
        dict(action="place", person="B", cell="a1"),
        dict(action="check"),
        dict(action="unmark", person="A", cell="b2"),
        dict(action="unplace", person="B"),
    ]
    for action in actions:
        assert session.act(action)["result"] == apply_structured_action(
            upstream, action
        )
        assert (
            session.pad.placed == upstream.placed
            and session.pad.marks == upstream.marks
        )


def test_invalid_submission_is_atomic_and_does_not_finish():
    session = VisualSession(glasshouse())
    session.act(dict(action="place", person="A", cell="b2"))
    before = session.observe()
    for positions in ({"A": "b1", "B": "z99"}, {"A": "b1", "Ada": "b2"}):
        with pytest.raises(SessionError):
            session.act(dict(action="submit", placements=positions, murderer="A"))
        assert session.observe() == before


def test_undo_redo_and_new_edit_history_do_not_change_other_sessions():
    a, b = VisualSession(glasshouse()), VisualSession(glasshouse())
    a.act(dict(action="mark", person="A", cell="b1"))
    a.act(dict(action="place", person="A", cell="b1"))
    a.act(dict(action="undo"))
    assert a.pad.placed == {} and a.pad.marks["A"]
    a.act(dict(action="redo"))
    assert a.observe()["placements"] == {"A": "b1"}
    a.act(dict(action="undo"))
    a.act(dict(action="place", person="A", cell="b2"))
    assert not a.observe()["can_redo"]
    assert b.observe()["placements"] == b.observe()["marks"] == {}
    assert a.frames[0]["placements"] == {} and a.frames[2]["placements"] == {"A": "b1"}


def test_revision_guard_prevents_stale_writes():
    session = VisualSession(glasshouse())
    session.act(dict(action="place", person="A", cell="b1"), expected_revision=0)
    with pytest.raises(StaleRevision):
        session.act(dict(action="place", person="B", cell="b2"), expected_revision=0)
    assert session.observe()["placements"] == {"A": "b1"}


@pytest.mark.parametrize("open_case", [False, True])
def test_terminal_result_requires_grid_and_goal_and_fences_edits(open_case):
    e = glasshouse(open_case=open_case)
    session = VisualSession(e)
    placements = {p: cell_label(e.case, k) for p, k in e.case.solution.items()}
    verdict = (
        {"answer": placements["V"]} if open_case else {"murderer": e.case.murderer}
    )
    out = session.act(dict(action="submit", placements=placements, **verdict))
    assert out["result"]["reward"] == 1 and out["observation"]["done"]
    for action in (dict(action="undo"), dict(action="place", person="A", cell="b2")):
        with pytest.raises(SessionError):
            session.act(action)
    assert not keys(out["observation"]) & {"solution", "answer_key", "certificate"}
    assert (
        VisualSession(e).act(dict(action="submit", **verdict))["result"]["reward"] == 0
    )


def test_annotations_are_only_presentation_and_xml_is_escaped():
    session = VisualSession(glasshouse())
    note = {
        "summary": "This is my hypothesis.",
        "clue_ids": ["clue-1"],
        "focus_person": "A",
        "focus_cells": ["b1"],
    }
    result = session.act({"action": "present"}, note=note)
    assert (
        result["observation"]["last_event"]["note"] == note and session.pad.placed == {}
    )
    with pytest.raises(SessionError):
        session.act({"action": "present"}, note={"clue_ids": ["clue-999"]})
    e = glasshouse()
    theme = replace(e.theme, areas=("<script>bad</script>", *e.theme.areas[1:]))
    svg = observation_svg(public_observation(Scratchpad(e.case, theme)))
    ET.fromstring(svg)
    assert "<script>" not in svg and "&lt;script&gt;" in svg


def test_both_views_keep_cells_doors_and_conflicting_occupants():
    for entry in (glasshouse(), lily_pond()):
        session = VisualSession(entry)
        session.act(dict(action="place", person="A", cell="b1"))
        session.act(dict(action="place", person="B", cell="b1"))
        state = session.observe()
        for mode in ("art", "diagram"):
            root = ET.fromstring(scene_svg(state, style=mode))
            hits = [n for n in root.iter() if "data-cell" in n.attrib]
            assert {n.attrib["data-cell"] for n in hits} == {
                c["cell"] for c in state["scene"]["cells"]
            }
            assert len(hits) == entry.case.scene.n_cells
            b1 = next(n for n in hits if n.attrib["data-cell"] == "b1")
            assert "Ada, Basil" in b1.attrib["aria-label"]
            assert len([n for n in root.iter() if "data-door" in n.attrib]) == len(
                entry.case.scene.doors
            )
        all_text = " ".join(ET.fromstring(observation_svg(state)).itertext())
        for clue in state["clues"]:
            assert " ".join(clue["text"].split()) in " ".join(all_text.split())
        for prop in state["scene"]["props"]:
            assert prop["name"] in all_text
        for terrain in state["scene"]["terrains"]:
            assert terrain["name"] in all_text


def test_unknown_props_keep_exact_nonrectangular_footprint():
    e = glasshouse()
    s = e.case.scene
    prop = Prop("custom_p10", False, frozenset((0, 1, 6)))
    scene = Scene(s.W, s.H, s.area_of, (None,) * s.n_cells, props=(prop,))
    state = public_observation(Scratchpad(replace(e.case, scene=scene), e.theme))
    p = state["scene"]["props"][0]
    assert p["art"] == "generic" and p["cells"] == ["a1", "b1", "a2"]
    root = ET.fromstring(scene_svg(state))
    assert (
        len([n for n in root.iter() if n.attrib.get("data-prop") == "custom_p10"]) == 3
    )
    assert sum(not c["standable"] for c in state["scene"]["cells"]) == 3


def test_async_adapter_reuses_tools_and_records_public_notes():
    e = glasshouse()
    env = IllustratedMurdokuEnvironment(
        {"murdoku_case": e.case.to_json(), "murdoku_theme": e.theme.to_json()}
    )
    asyncio.run(
        env.step(
            {
                "tool": "case_note",
                "arguments": {
                    "summary": "I will try the chair.",
                    "clue_ids": ["clue-1"],
                },
            }
        )
    )
    result = asyncio.run(
        env.step(
            {
                "tool": "murdoku",
                "arguments": {"action": "place", "person": "A", "cell": "b1"},
            }
        )
    )
    assert not result["done"] and env.observe()["placements"] == {"A": "b1"}
    assert env.export_trace()["steps"][-1]["note"]["summary"] == "I will try the chair."
    ET.fromstring(env.render_svg())
    assert not keys(env.observe()) & {"solution", "atoms", "answer_key"}


@pytest.fixture
def http_server():
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_http_private_source_blocked_and_frame_review_is_read_only(http_server):
    def get(path):
        with urllib.request.urlopen(http_server + path) as r:
            return r.read()

    def post(path, data):
        req = urllib.request.Request(
            http_server + path,
            json.dumps(data).encode(),
            {"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    for path in (
        "/visual/demos.py",
        "/../visual/demos.py",
        "/%2e%2e/visual/demos.py",
        "/core/instance.py",
    ):
        with pytest.raises(urllib.error.HTTPError) as e:
            get(path)
        assert e.value.code == 404
    state = post("/api/sessions", {"case_id": "glasshouse"})
    path = "/api/sessions/" + state["session_id"]
    post(path + "/actions", {"action": "place", "person": "A", "cell": "b1"})
    assert json.loads(get(path + "/frames?index=0"))["observation"]["placements"] == {}
    ET.fromstring(get(path + "/scene.svg?frame=0"))
    assert json.loads(get(path))["placements"] == {"A": "b1"}
    assert get(path + "/observation.png").startswith(b"\x89PNG\r\n\x1a\n")
    post(
        path + "/tools",
        {
            "tool": "case_note",
            "arguments": {"summary": "Public note", "clue_ids": ["clue-1"]},
        },
    )
    out = post(
        path + "/tools",
        {
            "tool": "murdoku",
            "arguments": {"action": "mark", "person": "A", "cell": "b2"},
        },
    )
    assert out["observation"]["last_event"]["note"]["summary"] == "Public note"
    assert len(json.loads(get("/api/tools"))["schemas"]) == 2


def test_large_scene_retains_native_resolution_and_all_256_targets():
    session = VisualSession(estate())
    state = session.observe()
    root = ET.fromstring(scene_svg(state))
    hits = [n for n in root.iter() if "data-cell" in n.attrib]
    assert len(hits) == 256 and any(n.attrib["data-cell"] == "p16" for n in hits)
    full = ET.fromstring(observation_svg(state))
    assert int(full.attrib["width"]) > int(root.attrib["width"])
    assert "Victor" in " ".join(full.itertext())
