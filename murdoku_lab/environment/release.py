"""Minimal portable query/rollout records for distribution."""

from copy import deepcopy
import json
import re
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme

QUERY_FIELDS = (
    "prompt_uid",
    "paired_case_id",
    "split",
    "environment_type",
    "messages",
    "tool_schemas",
    "allow_check",
    "python_workspace",
    "python_timeout_seconds",
    "assistant_turn_limit",
    "murdoku_observation",
    "murdoku_reward",
)
CASE_FIELDS = (
    "schema",
    "id",
    "variant",
    "scene",
    "characters",
    "victim",
    "tags",
    "clues",
    "solution",
    "answer",
    "answer_key",
    "target_band",
)
INTERNAL = re.compile(
    r"(?<![A-Za-z0-9_])(?:/Users/|/storage/|/home/[A-Za-z0-9_.-]+/)"
    r"|(?:login-ice|login-phoenix|dtai-login)"
    r"|hf_[A-Za-z0-9]{20,}|wandb_v1_[A-Za-z0-9_-]{25,}"
    r"|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"
)


def project(value, fields):
    return deepcopy({key: value[key] for key in fields if key in value})


def schema(value):
    allowed = (
        "type",
        "description",
        "enum",
        "const",
        "required",
        "additionalProperties",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minLength",
        "maxLength",
        "pattern",
        "format",
        "uniqueItems",
        "minItems",
        "maxItems",
        "default",
        "title",
        "properties",
        "items",
        "anyOf",
        "oneOf",
        "allOf",
        "$ref",
        "$defs",
    )
    result = project(value, allowed)
    for key in ("properties", "$defs"):
        if key in result:
            result[key] = {name: schema(item) for name, item in result[key].items()}
    for key in ("items", "additionalProperties"):
        if isinstance(result.get(key), dict):
            result[key] = schema(result[key])
    for key in ("anyOf", "oneOf", "allOf"):
        if key in result:
            result[key] = [schema(item) for item in result[key]]
    return result


def messages(source):
    result = []
    for message in source:
        clean = project(
            message, ("role", "content", "reasoning_content", "tool_call_id")
        )
        if isinstance(clean.get("content"), list):
            blocks = []
            for block in clean["content"]:
                if block["type"] == "text":
                    blocks.append(project(block, ("type", "text")))
                elif block["type"] == "image_url":
                    image = project(block["image_url"], ("url", "detail"))
                    url = image["url"]
                    if not url.startswith("data:image/"):
                        path = Path(url)
                        if path.is_absolute() or ".." in path.parts or ":" in url:
                            raise ValueError(
                                "Image references must be relative bundle paths"
                            )
                    blocks.append({"type": "image_url", "image_url": image})
                else:
                    raise ValueError("Unsupported release content block")
            clean["content"] = blocks
        if "tool_calls" in message:
            clean["tool_calls"] = [
                dict(
                    project(call, ("id", "type")),
                    function=project(call["function"], ("name", "arguments")),
                )
                for call in message["tool_calls"]
            ]
        result.append(clean)
    return result


def release_row(row):
    source = row.get("query", row)
    query = project(source, QUERY_FIELDS)
    query["split"] = source.get("split", row.get("split"))
    if query["split"] not in ("train", "validation", "test"):
        raise ValueError("A case-level train/validation/test split is required")
    query["messages"] = messages(source["messages"])
    query["tool_schemas"] = [
        project(s, ("name", "description", "parameters"))
        for s in source["tool_schemas"]
    ]
    for tool in query["tool_schemas"]:
        tool["parameters"] = schema(tool["parameters"])
    case = Case.from_json(source["murdoku_case"])
    case.self_check()
    formal_id = case.content_hash()
    if source.get("paired_case_id", formal_id) != formal_id:
        raise ValueError("paired_case_id differs from serialized formal case")
    query["paired_case_id"] = formal_id
    query["murdoku_case"] = project(case.to_json(), CASE_FIELDS)
    if source.get("murdoku_theme"):
        theme = Theme.from_json(source["murdoku_theme"])
        theme.validate(case)
        query["murdoku_theme"] = theme.to_json()
        query["murdoku_theme"]["theme_id"] = "murdoku-" + query["prompt_uid"]
    if "agent_info" in source:
        query["agent_info"] = project(
            source["agent_info"], ("max_turn", "apply_context_update_friction")
        )
    trace = row.get("rollout")
    rollout = None
    if trace is not None:
        if trace.get("replay_strict_success") is not True:
            raise ValueError("Release rollouts must be replay-qualified")
        if trace.get("prompt_uid") != query["prompt_uid"]:
            raise ValueError("Query/rollout identity mismatch")
        expected_tools = [
            {"type": "function", "function": s} for s in query["tool_schemas"]
        ]
        actual_tools = trace.get("tools")
        if actual_tools is None:
            raise ValueError("Original rollout tools are required for release")
        normalized_tools = []
        for tool in actual_tools:
            function = project(
                tool.get("function", tool), ("name", "description", "parameters")
            )
            function["parameters"] = schema(function["parameters"])
            normalized_tools.append({"type": "function", "function": function})
        if normalized_tools != expected_tools:
            raise ValueError("Rollout tool schema differs from query")
        rollout = {
            "prompt_uid": query["prompt_uid"],
            "messages": messages(trace["messages"]),
            "tools": [
                {"type": "function", "function": s} for s in query["tool_schemas"]
            ],
            "replay_strict_success": True,
        }
        if rollout["messages"][: len(query["messages"])] != query["messages"]:
            raise ValueError("Release rollout prompt differs from query")
    result = {"query": query, "rollout": rollout}
    if INTERNAL.search(json.dumps(result, ensure_ascii=False)):
        raise ValueError(
            "Internal path or credential pattern in release content; review before export"
        )
    return result


def main():
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.input.resolve() == a.output.resolve():
        p.error("Release output must be separate from the source archive")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = a.output.with_suffix(a.output.suffix + ".tmp")
    seen = set()
    case_splits = {}
    try:
        with a.input.open() as source, temporary.open("w") as target:
            for line in source:
                if not line.strip():
                    continue
                clean = release_row(json.loads(line))
                uid = clean["query"]["prompt_uid"]
                if uid in seen:
                    raise ValueError("Duplicate release query")
                case_id = clean["query"]["paired_case_id"]
                split = clean["query"]["split"]
                if case_id in case_splits and case_splits[case_id] != split:
                    raise ValueError("Same formal case occurs in multiple splits")
                case_splits[case_id] = split
                seen.add(uid)
                target.write(json.dumps(clean, ensure_ascii=False) + "\n")
        temporary.replace(a.output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Exported {len(seen)} query/rollout records")


if __name__ == "__main__":
    main()
