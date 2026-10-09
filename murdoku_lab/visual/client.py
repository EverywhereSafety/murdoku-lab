"""Standard-library HTTP client. Wrap step() as the model's murdoku function tool."""

import json
from urllib.request import Request, urlopen


class MurdokuClient:
    def __init__(
        self, base_url="http://127.0.0.1:8765", case_id="glasshouse", session_id=None
    ):
        self.base_url = base_url.rstrip("/")
        if session_id:
            self.session_id = session_id
        else:
            self.session_id = self._json("/api/sessions", {"case_id": case_id})[
                "session_id"
            ]

    def _json(self, path, body=None):
        req = Request(
            self.base_url + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=30) as response:
            return json.load(response)

    @property
    def path(self):
        return "/api/sessions/" + self.session_id

    def observe(self):
        return self._json(self.path)

    def call(self, tool, arguments):
        return self._json(self.path + "/tools", {"tool": tool, "arguments": arguments})

    def step(self, arguments, *, note=None, expected_revision=None):
        return self._json(
            self.path + "/actions",
            {
                "action": arguments,
                "note": note,
                "expected_revision": expected_revision,
                "source": "tool",
            },
        )

    def image(self, *, scope="full", format="png", style="art"):
        if (
            scope not in ("full", "scene")
            or format not in ("png", "svg")
            or style not in ("art", "diagram")
        ):
            raise ValueError("invalid image options")
        resource = "observation" if scope == "full" else "scene"
        with urlopen(
            self.base_url + self.path + f"/{resource}.{format}?style={style}",
            timeout=45,
        ) as response:
            return response.read()

    def trace(self):
        return self._json(self.path + "/trace")
