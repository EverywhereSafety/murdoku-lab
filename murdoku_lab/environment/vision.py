"""Optional drop-in adapter for the existing async tool environment.

Agent operations remain function calls. An image is an observation, never a click target.
The caller chooses when to attach an SVG/raster observation to its model request.
"""

from copy import deepcopy

from murdoku_lab.environment.tools import MurdokuToolEnvironment
from murdoku_lab.environment.protocol import SCHEMAS
from murdoku_lab.visual.art import scene_svg, observation_svg, board_svg
from murdoku_lab.visual.projection import public_observation
from murdoku_lab.environment.validation import validate_note, validate_tool_action

CASE_NOTE_SCHEMA = {
    "name": "case_note",
    "description": "Record a concise public explanation and visible references for a later demo. Does not test deductions or change puzzle state.",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "maxLength": 1200},
            "clue_ids": {"type": "array", "items": {"type": "string"}},
            "focus_person": {"type": "string"},
            "focus_cells": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["summary"],
        "additionalProperties": False,
    },
}


def visual_schemas(record=None):
    schemas = deepcopy((record or {}).get("tool_schemas", SCHEMAS))
    return [schema for schema in schemas if schema.get("name") != "case_note"] + [
        deepcopy(CASE_NOTE_SCHEMA)
    ]


VISUAL_SCHEMAS = visual_schemas()

VISION_INSTRUCTIONS = """The board is an image. The text contains the clues, public attributes and rules.
Use the same coordinate-based murdoku tools to place and mark people; no pixel clicking is needed.
murdoku(action="board") requests the current board image, including your placements and marks.
It does not return a textual tile map. The rollout caller attaches the requested PNG observation.
case_note may record a concise explanation with visible clue references for a later demo.
"""


def environment_for(record, memory_path=None):
    """Keep existing text episodes on their original environment and action protocol."""
    if record.get("murdoku_observation", "text") == "vision":
        return IllustratedMurdokuEnvironment(record, memory_path)
    return MurdokuToolEnvironment(record, memory_path)


class IllustratedMurdokuEnvironment(MurdokuToolEnvironment):
    def __init__(self, record, memory_path=None):
        super().__init__(record, memory_path)
        self.tool_schemas = visual_schemas(record)
        self.events = []
        self.pending_note = None
        self.visual_terminal = None
        self.observation_mode = record.get("murdoku_observation", "text")
        if self.observation_mode not in ("text", "vision"):
            raise ValueError("murdoku_observation must be text or vision")

    async def step(self, call):
        if self.done:
            raise ValueError("episode already ended")
        if call["tool"] == "case_note":
            self.pending_note = validate_note(call["arguments"], self.pad)
            self.events.append(
                {
                    "index": len(self.events) + 1,
                    "action": {"action": "present"},
                    "note": deepcopy(self.pending_note),
                    "source": "tool",
                }
            )
            return {
                "done": False,
                "observations": ["Public presentation note recorded."],
            }
        if call["tool"] == "murdoku":
            validate_tool_action(call["arguments"], self.pad)
            if (
                self.observation_mode == "vision"
                and call["arguments"]["action"] == "board"
            ):
                self.events.append(
                    {
                        "index": len(self.events) + 1,
                        "action": {"action": "board"},
                        "note": deepcopy(self.pending_note),
                        "source": "tool",
                    }
                )
                self.pending_note = None
                return {
                    "done": False,
                    "observations": ["Current board image requested."],
                    "image_request": {
                        "scope": "board",
                        "format": "png",
                        "revision": len(self.events),
                    },
                }
        result = await super().step(call)
        if call["tool"] == "murdoku":
            self.events.append(
                {
                    "index": len(self.events) + 1,
                    "action": deepcopy(call["arguments"]),
                    "note": deepcopy(self.pending_note),
                    "source": "tool",
                }
            )
            self.pending_note = None
            if result.get("done"):
                self.visual_terminal = deepcopy(result)
        return result

    def observe(self):
        return public_observation(
            self.pad,
            revision=len(self.events),
            done=self.done,
            terminal=self.visual_terminal,
            last_event=self.events[-1] if self.events else None,
        )

    def render_svg(self, *, scope="full", style="art"):
        renderers = {"full": observation_svg, "scene": scene_svg, "board": board_svg}
        if scope not in renderers:
            raise ValueError("scope must be full, scene or board")
        return renderers[scope](self.observe(), style=style)

    def export_trace(self, case_id="local"):
        return {
            "schema": "murdoku.trace/1",
            "case_id": case_id,
            "source": {
                "kind": "recorded_tool_calls",
                "label": "Tool harness; model provenance supplied by caller",
            },
            "steps": deepcopy(self.events),
        }

    def render_png(self, *, scope="full", style="art"):
        from murdoku_lab.visual.raster import png_from_svg

        return png_from_svg(self.render_svg(scope=scope, style=style))

    async def finalize(self, reason):
        result = await super().finalize(reason)
        self.visual_terminal = deepcopy(result)
        return result
