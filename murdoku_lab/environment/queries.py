"""Paired text/vision queries using the existing private RL-record schema.

The model receives only model_inputs(...), never the complete environment record.
The visual view names public entities but supplies no textual tile/door map.
"""

from copy import deepcopy
import base64
import hashlib
from pathlib import Path

from murdoku_lab.core.theme import canonical_theme
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.core.render import TERMS, render_case
from murdoku_lab.environment.protocol import PROTOCOL, SCHEMAS, simplify_record


def vision_statement(case, theme):
    from murdoku_lab.visual.projection import public_observation

    public = public_observation(Scratchpad(case, theme))
    lines = [
        public["title"],
        f"BOARD: {case.scene.W} columns × {case.scene.H} rows. See the image.",
        public["goal"],
        "",
        "RULES",
        *public["rules"],
        "",
        "PEOPLE",
    ]
    for person in public["people"]:
        label = f"{person['id']}: {person['name']}"
        if person["victim"]:
            label += " — victim"
        if person["tags"]:
            label += "; " + ", ".join(person["tags"])
        lines.append(label)
    lines += ["", "AREA NAMES"]
    lines += [f"{a['number']}: {a['name']}" for a in public["scene"]["areas"]]
    lines += ["", "CLUES"]
    lines += [f"{c['id']}: {c['text']}" for c in public["clues"]]
    lines += ["", "TERMS", TERMS]
    return "\n".join(lines)


def make_record(case, theme=None, *, view="text", image_path=None, image_bytes=None):
    """Format a validated case; generation/export admission owns the full gate."""
    theme = theme or canonical_theme(case)
    case.self_check()
    theme.validate(case)
    if view not in ("text", "vision"):
        raise ValueError("view must be text or vision")
    record = {
        "prompt_uid": case.content_hash(),
        "data_source": "murdoku",
        "environment_type": "murdoku",
        "messages": [
            {"role": "system", "content": PROTOCOL},
            {
                "role": "user",
                "content": render_case(case, theme, scene_format="compact"),
            },
        ],
        "murdoku_case": case.to_json(),
        "murdoku_theme": theme.to_json(),
        "tool_schemas": deepcopy(SCHEMAS),
        "allow_check": True,
        "agent_info": {"max_turn": 1000, "apply_context_update_friction": False},
        "paired_case_id": case.content_hash(),
        "murdoku_observation": view,
        "visual_case_id": "cpu-" + case.content_hash(),
    }
    if view == "vision":
        if not image_path or not image_bytes:
            raise ValueError("vision view requires a PNG path and bytes")
        if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("vision assets must be PNG images")
        record["prompt_uid"] += "-vision"
        record["messages"][1]["content"] = [
            {"type": "text", "text": vision_statement(case, theme)},
            {"type": "image_url", "image_url": {"url": image_path}},
        ]
        record["image_assets"] = [
            {
                "path": image_path,
                "mime_type": "image/png",
                "sha256": hashlib.sha256(image_bytes).hexdigest(),
            }
        ]
    return simplify_record(record)


def public_record(record):
    allowed = (
        "prompt_uid",
        "paired_case_id",
        "data_source",
        "environment_type",
        "messages",
        "tool_schemas",
        "allow_check",
        "python_workspace",
        "python_timeout_seconds",
        "assistant_turn_limit",
        "agent_info",
        "murdoku_observation",
        "image_assets",
        "split",
        "visual_case_id",
    )
    return deepcopy({key: record[key] for key in allowed if key in record})


def model_inputs(record, *, asset_root=None):
    """Return only model-facing fields and optionally inline portable image refs.

    No provider call is performed. Existing text records need no asset root.
    """
    messages = deepcopy(record["messages"])
    expected = {a["path"]: a["sha256"] for a in record.get("image_assets", [])}
    for message in messages:
        if not isinstance(message.get("content"), list):
            continue
        for part in message["content"]:
            if part.get("type") != "image_url":
                continue
            url = part["image_url"]["url"]
            if url.startswith("data:image/"):
                continue
            if asset_root is None:
                raise ValueError(
                    "asset_root is required to inline a local image reference"
                )
            root = Path(asset_root).resolve()
            image = (root / url).resolve()
            if not image.is_relative_to(root):
                raise ValueError("image reference is outside the query bundle")
            data = image.read_bytes()
            if url in expected and hashlib.sha256(data).hexdigest() != expected[url]:
                raise ValueError("image checksum does not match this query")
            part["image_url"]["url"] = "data:image/png;base64," + base64.b64encode(
                data
            ).decode("ascii")
    return {
        "messages": messages,
        "tools": [
            {"type": "function", "function": deepcopy(s)}
            for s in record.get("tool_schemas", SCHEMAS)
        ],
    }


def public_tool_result(result):
    return deepcopy(
        {
            k: v
            for k, v in result.items()
            if k not in ("score", "reward", "final_state_variable")
        }
    )


def frame_message(environment, image_request):
    """Materialize an on-demand frame; caller appends it after its tool replies."""
    data = environment.render_png(scope=image_request.get("scope", "board"))
    return {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"Current board, revision {image_request.get('revision', 0)}.",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64,"
                    + base64.b64encode(data).decode("ascii")
                },
            },
        ],
    }
