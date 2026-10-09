"""Local HTTP viewer. Only dist/ and allowlisted public API responses are served."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlsplit

from murdoku_lab.visual.art import scene_svg, observation_svg, portrait_svg, prop_svg
from murdoku_lab.visual.projection import ART_KINDS
from murdoku_lab.visual.demos import catalogue
from murdoku_lab.environment.vision import VISUAL_SCHEMAS
from murdoku_lab.visual.session import VisualSession, SessionError, StaleRevision

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT


class Handler(BaseHTTPRequestHandler):
    server_version = "MurdokuVisualLab/0.1"

    def log_message(self, format, *args):
        # No request bodies, tokens, query-string data or imported records in logs.
        pass

    def respond(self, body, status=200, mime="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0]
        if content_type != "application/json":
            raise SessionError("Use application/json")
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 2_000_000:
            raise SessionError("JSON body must be between 1 byte and 2 MB")
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise SessionError("JSON body must be an object")
        return data

    def do_GET(self):
        try:
            self.get()
        except (SessionError, ValueError, KeyError, IndexError, TypeError):
            self.respond({"error": "Invalid request or unknown resource."}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def get(self):
        url = urlsplit(self.path)
        path = unquote(url.path)
        q = parse_qs(url.query)
        if path == "/api/health":
            return self.respond({"ok": True, "service": "murdoku-visual-lab"})
        if path == "/api/cases":
            return self.respond(
                {
                    "cases": [
                        {
                            "id": e.slug,
                            "title": e.theme.title,
                            "eyebrow": e.eyebrow,
                            "size": e.case.scene.W,
                            "people": len(e.case.characters),
                            "areas": e.case.scene.n_areas,
                            "variant": e.case.variant,
                            "description": e.description,
                        }
                        for e in self.server.catalogue.values()
                    ]
                }
            )
        if path == "/api/tools":
            return self.respond(
                {
                    "schemas": [
                        s
                        for s in VISUAL_SCHEMAS
                        if s["name"] in ("murdoku", "case_note")
                    ],
                    "transport": "murdoku tool calls; no computer-use actions",
                }
            )
        portrait = re.fullmatch(r"/api/art/portrait/(\d+)\.svg", path)
        if portrait:
            return self.respond(
                portrait_svg(int(portrait[1])), mime="image/svg+xml; charset=utf-8"
            )
        prop = re.fullmatch(r"/api/art/prop/([a-z_]+)\.svg", path)
        if prop:
            if prop[1] not in ART_KINDS and prop[1] != "generic":
                raise SessionError("unknown illustration")
            return self.respond(prop_svg(prop[1]), mime="image/svg+xml; charset=utf-8")
        match = re.fullmatch(
            r"/api/sessions/([a-f0-9]{32})(?:/(scene\.(?:svg|png)|observation\.(?:svg|png)|trace|frames))?",
            path,
        )
        if match:
            session = self.server.sessions.get(match[1])
            if session is None:
                return self.respond(
                    {"error": "Session expired or unknown. Start a new session."}, 404
                )
            with session.lock:
                if match[2] == "trace":
                    return self.respond(session.export_trace())
                if match[2] == "frames":
                    i = int(q.get("index", [len(session.frames) - 1])[0])
                    if not 0 <= i < len(session.frames):
                        raise SessionError("frame index outside trace")
                    return self.respond(
                        {"observation": session.frames[i], "count": len(session.frames)}
                    )
                if "frame" in q:
                    frame = int(q["frame"][0])
                    if not 0 <= frame < len(session.frames):
                        raise SessionError("frame index outside trace")
                    state = session.frames[frame]
                else:
                    state = session.observe()
            if match[2] in (
                "scene.svg",
                "observation.svg",
                "scene.png",
                "observation.png",
            ):
                style = q.get("style", ["art"])[0]
                selected = q.get("selected", [None])[0]
                focus = q.get("focus", [""])[0].split(",") if q.get("focus") else []
                fn = scene_svg if match[2].startswith("scene.") else observation_svg
                vector = fn(state, style=style, selected=selected, focus_cells=focus)
                if match[2].endswith(".png"):
                    from murdoku_lab.visual.raster import png_from_svg

                    try:
                        return self.respond(png_from_svg(vector), mime="image/png")
                    except (RuntimeError, OSError):
                        return self.respond(
                            {
                                "error": "PNG renderer unavailable. Run npm ci in the project directory."
                            },
                            503,
                        )
                return self.respond(vector, mime="image/svg+xml; charset=utf-8")
            return self.respond(state)
        if path.startswith("/api/"):
            return self.respond({"error": "Unknown API route."}, 404)
        # A source directory / private answer key is never a static-file root.
        dist = (ROOT / "dist").resolve()
        file = (dist / ("index.html" if path == "/" else path.lstrip("/"))).resolve()
        if not file.is_relative_to(dist) or not file.is_file():
            return self.respond(
                {"error": "File not found. Build the UI with npm run build."}, 404
            )
        mime = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        return self.respond(file.read_bytes(), mime=mime)

    def do_POST(self):
        try:
            self.post()
        except StaleRevision as error:
            self.respond({"error": str(error)}, 409)
        except (SessionError, ValueError, KeyError, TypeError) as error:
            message = (
                str(error)
                if isinstance(error, SessionError)
                else "Invalid JSON request."
            )
            self.respond({"error": message}, 422)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def post(self):
        path = urlsplit(self.path).path
        data = self.read_json()
        if path == "/api/sessions":
            slug = data.get("case_id", "glasshouse")
            if slug not in self.server.catalogue:
                raise SessionError("unknown case_id")
            if len(self.server.sessions) >= 256:
                raise SessionError(
                    "This local viewer holds at most 256 sessions. Restart to clear them."
                )
            session = VisualSession(self.server.catalogue[slug])
            self.server.sessions[session.id] = session
            return self.respond(session.observe(), 201)
        match = re.fullmatch(r"/api/sessions/([a-f0-9]{32})/(actions|tools)", path)
        if match:
            session = self.server.sessions.get(match[1])
            if session is None:
                return self.respond({"error": "Session expired or unknown."}, 404)
            if match[2] == "tools":
                if data.get("tool") == "case_note":
                    return self.respond(
                        session.act({"action": "present"}, note=data.get("arguments"))
                    )
                if data.get("tool") != "murdoku":
                    raise SessionError(
                        "HTTP tools are murdoku and case_note. Scientific Python and memory remain in the original in-process harness."
                    )
                return self.respond(session.act(data.get("arguments")))
            args = data.get("action")
            if isinstance(args, str):
                # Direct arguments ({action:'place',person:'A',cell:'b1'}) are convenient for
                # existing tool-call clients. Envelopes allow notes and revision guards.
                args = data
                return self.respond(session.act(args))
            return self.respond(
                session.act(
                    args,
                    note=data.get("note"),
                    expected_revision=data.get("expected_revision"),
                    source=data.get("source", "tool"),
                )
            )
        return self.respond({"error": "Unknown API route."}, 404)


def make_server(host="127.0.0.1", port=8765, records=None):
    server = ThreadingHTTPServer((host, port), Handler)
    server.catalogue = catalogue(records)
    server.sessions = {}
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument(
        "--records",
        help="Optional trusted local Case/RL record JSON or JSONL; kept server-side",
    )
    args = parser.parse_args()
    server = make_server(args.host, args.port, args.records)
    print(
        f"Murdoku visual lab: http://{args.host}:{server.server_address[1]}", flush=True
    )
    print("Local in-memory sessions. Ctrl-C stops the viewer.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
