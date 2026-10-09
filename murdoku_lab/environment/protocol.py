"""Canonical Murdoku task prompt and tool contract for text and vision."""

from copy import deepcopy

_PROMPT = """Solve the puzzle from its visible rules and clues. Submit the complete arrangement and the requested answer.
You may call multiple tools in one assistant turn. Tool responses do not count toward the assistant-turn limit.

murdoku: action="board" shows the board; place/unplace/mark/unmark update the scratchpad. action="check" checks basic placement rules only, not clues or the answer. Finish with action="submit", placements mapping EVERY actual character (including the victim) to a cell, and murderer containing the character's name. For victim-cell tasks use answer with the cell instead. Submission ends the episode. Printing or saving an answer does not submit it.

{python_instructions}

memory: write/read/list/delete notes using title and content. Notes and scratchpad persist when old conversation turns are cleared; retrieve notes when needed. Note bodies are not automatically inserted into the prompt. No puzzle-specific solver is supplied.
"""

STATELESS_PYTHON = """run_python: execute inline code in a fresh isolated process. Python variables do not persist. Use any Python approach you prefer."""
WORKSPACE_PYTHON = """run_python: execute inline code or a saved Python path; provide exactly one of code or path. Each execution uses a fresh isolated process in /workspace. Python variables do not persist; files do, including across context clears. The default wall-clock limit is {timeout:g} seconds; timeout can request up to 300 seconds. A timeout kills that execution, but files already written remain. Set any internal computation deadline below the tool limit. Use any Python approach you prefer.

workspace: write/read/list/delete files, or replace one unique old_text with content. Paths are relative to /workspace. Saved Python modules can be imported. Managed files and recovery snapshots support 128 files / 16 MiB; read output is capped at 32768 characters and stdout/stderr at 16384 characters."""

PROTOCOL = _PROMPT.format(python_instructions=STATELESS_PYTHON)

SCHEMAS = [
    {
        "name": "memory",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["write", "read", "list", "delete"],
                },
                "title": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "murdoku",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "board",
                        "place",
                        "unplace",
                        "mark",
                        "unmark",
                        "check",
                        "submit",
                    ],
                },
                "person": {"type": "string"},
                "cell": {"type": "string"},
                "placements": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "murderer": {"type": "string"},
                "answer": {"type": "string"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "run_python",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
    },
]


WORKSPACE_SCHEMA = {
    "name": "workspace",
    "description": "Manage persistent files in this episode's /workspace.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["write", "replace", "read", "list", "delete"],
            },
            "path": {"type": "string", "description": "Relative path, e.g. solver.py"},
            "content": {"type": "string"},
            "old_text": {"type": "string", "description": "Unique text to replace"},
        },
        "required": ["action"],
    },
}


def simplify_record(record, workspace=True, python_timeout=120, max_turns=None):
    """Prepare the current protocol. Replay never calls this or rewrites a query."""
    if (
        isinstance(python_timeout, bool)
        or not isinstance(python_timeout, (int, float))
        or not 0 < python_timeout <= 300
    ):
        raise ValueError("invalid Python timeout")
    if max_turns is None:
        max_turns = record.get("assistant_turn_limit")
    if max_turns is not None and (type(max_turns) is not int or max_turns < 1):
        raise ValueError("max_turns must be a positive integer")
    result = deepcopy(record)
    result.pop("murdoku_protocol_version", None)
    result["python_workspace"] = bool(workspace)
    result["python_timeout_seconds"] = python_timeout if workspace else 30
    instructions = (
        WORKSPACE_PYTHON.format(timeout=python_timeout)
        if workspace
        else STATELESS_PYTHON
    )
    prompt = _PROMPT.format(python_instructions=instructions)
    if max_turns is not None:
        result["assistant_turn_limit"] = max_turns
        result.setdefault("agent_info", {})["max_turn"] = max_turns
        prompt += f"\nYou have at most {max_turns} assistant turns.\n"
    schemas = deepcopy(SCHEMAS)
    if workspace:
        python_schema = next(x for x in schemas if x["name"] == "run_python")
        python_schema["parameters"] = {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "path": {"type": "string"},
                "timeout": {"type": "number", "exclusiveMinimum": 0, "maximum": 300},
            },
        }
        schemas.append(deepcopy(WORKSPACE_SCHEMA))
    result["tool_schemas"] = schemas
    observation = result.get("murdoku_observation", "text")
    if observation == "vision":
        from murdoku_lab.environment.vision import VISION_INSTRUCTIONS, visual_schemas

        prompt += "\n" + VISION_INSTRUCTIONS
        result["tool_schemas"] = visual_schemas(result)
    elif observation != "text":
        raise ValueError("murdoku_observation must be text or vision")
    result["messages"][0]["content"] = prompt
    return result


def parse_function_call(text, schemas=None):
    import json

    call = json.loads(text)
    name = call.get("name", call.get("tool"))
    arguments = call.get("arguments", {})
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    if not isinstance(arguments, dict):
        raise ValueError("function arguments must be an object")
    if schemas and name not in [schema["name"] for schema in schemas]:
        raise ValueError("unknown tool")
    return {"tool": name, "arguments": arguments}
