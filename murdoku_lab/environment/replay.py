"""Accept teacher traces only after fresh harness execution and strict success."""

import json
from copy import deepcopy
from murdoku_lab.environment.vision import environment_for
from murdoku_lab.environment.queries import frame_message
from murdoku_lab.environment.protocol import parse_function_call


async def replay_candidate(record, candidate, allow_recoverable_errors=False):
    env = await environment_for(record).start()
    messages = deepcopy(record["messages"])
    try:
        events = candidate.get("events", [])
        if not events:
            raise ValueError("empty trajectory")
        for i, event in enumerate(events):
            calls = event.get("tool_calls", [])
            if not calls:
                raise ValueError("each turn must contain at least one tool call")
            assistant = {
                "role": "assistant",
                "content": event.get("text") or "",
                "tool_calls": calls,
            }
            if event.get("reasoning"):
                assistant["reasoning_content"] = event["reasoning"]
            messages.append(assistant)
            frames = []
            for call_index, call in enumerate(calls):
                action = parse_function_call(
                    json.dumps(call["function"]), record["tool_schemas"]
                )
                try:
                    result = await env.step(action)
                except (ValueError, KeyError, TypeError) as exc:
                    if not allow_recoverable_errors:
                        raise
                    result = {"error": str(exc), "done": False}
                if result.get("error") and not allow_recoverable_errors:
                    raise ValueError("tool execution failed during replay")
                observed = event.get("observations")
                if observed is not None:
                    if len(observed) != len(calls):
                        raise ValueError("tool observation count mismatch")
                    original = observed[call_index]
                    if bool(original.get("error")) != bool(result.get("error")):
                        raise ValueError(
                            "tool success/error changed during fresh replay"
                        )
                # Grader statistics are private supervision metadata, never model input.
                public = {
                    k: v
                    for k, v in result.items()
                    if k not in ("score", "reward", "final_state_variable")
                }
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(public),
                    }
                )
                if result.get("image_request"):
                    frames.append(frame_message(env, result["image_request"]))
                if result.get("done"):
                    if i != len(events) - 1 or call_index != len(calls) - 1:
                        raise ValueError("trajectory continues after submit")
                    score = result.get("score", {})
                    if not score.get("solved"):
                        raise ValueError("submission is not strictly correct")
                    return {
                        "prompt_uid": record["prompt_uid"],
                        "messages": messages,
                        "tools": [
                            {"type": "function", "function": s}
                            for s in record["tool_schemas"]
                        ],
                        "replay_strict_success": True,
                        "turns": len(events),
                        "recovered_tool_errors": sum(
                            bool(o.get("error"))
                            for e in events
                            for o in e.get("observations", [e.get("observation", {})])
                        ),
                    }
            messages.extend(frames)
        raise ValueError("trajectory never submitted")
    finally:
        await env.close()
