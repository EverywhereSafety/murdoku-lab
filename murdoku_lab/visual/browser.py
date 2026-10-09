"""Browser adapter using the same sessions, actions, scoring and SVG renderer."""

import json
import re
from urllib.parse import parse_qs, urlsplit

from murdoku_lab.visual.demos import catalogue
from murdoku_lab.visual.session import VisualSession
from murdoku_lab.visual.art import scene_svg, observation_svg


class BrowserGame:
    def __init__(self):
        self.cases = catalogue()
        self.sessions = {}

    def restore(self, saved):
        session = VisualSession(self.cases[saved["case_id"]])
        if not isinstance(saved["id"], str) or not re.fullmatch(
            r"[a-f0-9]{32}", saved["id"]
        ):
            raise ValueError("Invalid saved session ID")
        session.id = saved["id"]
        session.frames = [session.observe()]
        for event in saved["events"]:
            session.act(event["action"], note=event.get("note"), source=event["source"])
        self.sessions[session.id] = session

    def request(self, path, body=None):
        url = urlsplit(path)
        query = parse_qs(url.query)
        session = None
        if url.path == "/api/cases":
            result = {
                "cases": [
                    dict(
                        id=e.slug,
                        title=e.theme.title,
                        eyebrow=e.eyebrow,
                        size=e.case.scene.W,
                        people=len(e.case.characters),
                        areas=e.case.scene.n_areas,
                        variant=e.case.variant,
                        description=e.description,
                    )
                    for e in self.cases.values()
                ]
            }
        elif url.path == "/api/sessions" and body is not None:
            session = VisualSession(self.cases[body["case_id"]])
            self.sessions[session.id] = session
            result = session.observe()
        else:
            match = re.fullmatch(
                r"/api/sessions/([a-f0-9]{32})(?:/(actions|retry|trace|frames|scene\.svg|observation\.svg))?",
                url.path,
            )
            if not match or match[1] not in self.sessions:
                raise ValueError("Session not found. Start a new case.")
            session = self.sessions[match[1]]
            route = match[2]
            if route == "retry" and body is not None:
                session = session.continue_attempt()
                self.sessions[session.id] = session
                result = session.observe()
            elif route == "actions" and body is not None:
                result = session.act(
                    body["action"],
                    note=body.get("note"),
                    expected_revision=body.get("expected_revision"),
                    source=body.get("source", "human"),
                )
            elif route == "trace":
                result = session.export_trace()
            elif route == "frames":
                index = int(query.get("index", [len(session.frames) - 1])[0])
                if not 0 <= index < len(session.frames):
                    raise ValueError("Frame outside trace")
                result = {
                    "observation": session.frames[index],
                    "count": len(session.frames),
                }
            elif route in ("scene.svg", "observation.svg"):
                state = session.observe()
                if "frame" in query:
                    index = int(query["frame"][0])
                    if not 0 <= index < len(session.frames):
                        raise ValueError("Frame outside trace")
                    state = session.frames[index]
                render = scene_svg if route == "scene.svg" else observation_svg
                result = render(
                    state,
                    style=query.get("style", ["art"])[0],
                    selected=query.get("selected", [None])[0],
                    focus_cells=query.get("focus", [""])[0].split(","),
                )
            elif route is None:
                result = session.observe()
            else:
                raise ValueError("Unknown request")
        saved = None
        if session and body is not None:
            saved = {
                "case_id": session.entry.slug,
                "id": session.id,
                "events": session.events,
            }
        return {"result": result, "saved": saved}


def dispatch(game, request_json):
    request = json.loads(request_json)
    if request.get("restore"):
        try:
            game.restore(request["restore"])
        except (ValueError, KeyError, TypeError):
            pass
    return json.dumps(game.request(request["path"], request.get("body")))
