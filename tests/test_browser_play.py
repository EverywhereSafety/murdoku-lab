"""Static play shares game semantics and reconstructs progress from JSON events."""

import json

from murdoku_lab.visual.browser import BrowserGame, dispatch


def test_browser_progress_restores_notes_undo_frames_and_solution():
    game = BrowserGame()
    initial = game.request("/api/sessions", {"case_id": "glasshouse"})["result"]
    path = f"/api/sessions/{initial['session_id']}"
    for action in (
        {"action": "mark", "person": "A", "cell": "b1"},
        {"action": "place", "person": "A", "cell": "b1"},
        {"action": "note", "text": "A is on a chair."},
        {"action": "undo"},
        {"action": "redo"},
    ):
        reply = game.request(path + "/actions", {"action": action, "source": "human"})
    resumed = BrowserGame()
    response = json.loads(
        dispatch(resumed, json.dumps({"restore": reply["saved"], "path": path}))
    )
    assert response["result"] == game.request(path)["result"]
    assert (
        resumed.request(path + "/frames?index=0")["result"]["observation"]["session_id"]
        == initial["session_id"]
    )
    assert (
        resumed.request(path + "/frames?index=0")["result"]["observation"]["placements"]
        == {}
    )
    assert (
        resumed.request(path + "/scene.svg?style=diagram&frame=0")["result"]
        != resumed.request(path + "/scene.svg?style=art")["result"]
    )
    entry = resumed.cases["glasshouse"]
    from murdoku_lab.core.render import cell_label

    action = {
        "action": "submit",
        "placements": {
            p: cell_label(entry.case, c) for p, c in entry.case.solution.items()
        },
        "murderer": "A",
    }
    result = resumed.request(path + "/actions", {"action": action})["result"]
    assert result["result"]["reward"] == 1
    assert result["observation"]["done"]


def test_bad_saved_progress_does_not_block_casebook():
    game = BrowserGame()
    result = json.loads(
        dispatch(
            game,
            json.dumps({"path": "/api/cases", "restore": {"case_id": "removed-case"}}),
        )
    )
    assert len(result["result"]["cases"]) == 4


def test_continue_failed_attempt_keeps_edits_without_reopening_original():
    import pytest
    from murdoku_lab.visual.session import SessionError

    game = BrowserGame()
    state = game.request("/api/sessions", {"case_id": "glasshouse"})["result"]
    path = f"/api/sessions/{state['session_id']}"
    for action in (
        {"action": "mark", "person": "B", "cell": "e3"},
        {"action": "place", "person": "A", "cell": "b1"},
        {"action": "note", "text": "Follow the chairs."},
    ):
        game.request(path + "/actions", {"action": action})
    before = game.request(path)["result"]
    game.request(path + "/actions", {"action": {"action": "submit", "murderer": "B"}})
    resumed = game.request(path + "/retry", {})
    state = resumed["result"]
    assert state["session_id"] != before["session_id"]
    assert state["placements"] == before["placements"]
    assert state["marks"] == before["marks"]
    assert state["notebook"] == before["notebook"]
    assert not state["done"] and state["can_undo"]
    assert game.request(path)["result"]["done"]
    restored = BrowserGame()
    restored.restore(json.loads(json.dumps(resumed["saved"])))
    assert restored.request(f"/api/sessions/{state['session_id']}")["result"] == state
    with pytest.raises(SessionError):
        restored.sessions[state["session_id"]].continue_attempt()
