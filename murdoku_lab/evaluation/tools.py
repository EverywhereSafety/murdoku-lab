"""Canonical native text/vision sampling and evaluation against a hosted model."""

import argparse, asyncio, json, time, urllib.request
from pathlib import Path
from murdoku_lab.paths import DEFAULTS, PROJECT_ROOT
from murdoku_lab.environment.vision import environment_for as make_environment
from murdoku_lab.environment.queries import model_inputs, frame_message
from murdoku_lab.environment.rewards import terminal_reward
from long_horizon_rl.context_feedback import warning_notice, clear_notice
from long_horizon_rl.queries import query_from_row
from murdoku_lab.environment.protocol import simplify_record
from murdoku_lab.environment.protocol import parse_function_call as parse_action


def tool_package_requirements(root):
    root = Path(root)
    path = root / "requirements" / "tools.txt"
    text = path.read_text() if path.is_file() else ""
    return (
        text
        if text and not text.lstrip().startswith("-r ")
        else (DEFAULTS / "tool-requirements.txt").read_text()
    )


async def main(args):
    if (
        args.context_clear
        and not 0 < args.clear_target < args.clear_trigger < args.context
    ):
        raise ValueError("require clear target < trigger < full context")
    if args.context_feedback and not args.context_clear:
        raise ValueError("context feedback requires managed clearing")
    if (
        args.warning_margin is not None
        and not 0 < args.warning_margin < args.clear_trigger
    ):
        raise ValueError("invalid warning margin")
    if args.memory_title_limit < 0:
        raise ValueError("invalid title limit")
    if args.parallel < 1:
        raise ValueError("parallel must be positive")
    if not 0 <= args.temperature <= 2 or not 0 < args.top_p <= 1:
        raise ValueError("invalid sampling parameters")
    endpoint = json.loads(Path(args.endpoint).read_text())
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=True)
    records = [
        query_from_row(json.loads(line))
        for line in Path(args.input).read_text().splitlines()
        if line.strip()
    ]
    if not args.keep_input_protocol:
        records = [
            simplify_record(
                r, workspace=args.workspace, python_timeout=args.python_timeout
            )
            for r in records
        ]
    uids = [record["prompt_uid"] for record in records]
    if len(set(uids)) != len(uids):
        raise ValueError("duplicate prompt in evaluation input")
    for uid in uids:
        if (
            not isinstance(uid, str)
            or not uid
            or Path(uid).name != uid
            or uid in (".", "..")
        ):
            raise ValueError("invalid prompt UID")
        for suffix in (".memory.json", ".workspace.json", ".json", ".partial.json"):
            if (root / (uid + suffix)).exists():
                raise ValueError(
                    "existing attempt artifacts; use a new output directory"
                )
    semaphore = asyncio.Semaphore(args.parallel)

    async def evaluate(record):
        async with semaphore:
            env = None
            phase = "input"
            events = []
            generated = 0
            errors = 0
            valid = 0
            reward = 0.0
            score = None
            reason = "turn_limit"
            start = time.monotonic()
            immutable = []
            groups = []
            memory = {}
            context_events = []
            feedback_events = []
            clears = 0
            notice_text = ""
            warning_sent = False

            def model_messages():
                visible = {
                    k: v for k, v in memory.items() if k not in ("archival", "notes")
                }
                prefix = [dict(m) for m in immutable]
                if visible:
                    prefix[0]["content"] += "\nOperational memory: " + json.dumps(
                        visible
                    )
                if notice_text:
                    prefix[0]["content"] += "\n" + notice_text
                return prefix + [m for group in groups for m in group]

            try:
                messages = model_inputs(
                    record,
                    asset_root=getattr(args, "asset_root", None)
                    or Path(args.input).parent,
                )["messages"]
                tools = [
                    {"type": "function", "function": schema}
                    for schema in record["tool_schemas"]
                ]
                immutable = list(messages)
                phase = "environment"
                env = make_environment(
                    record, memory_path=root / (record["prompt_uid"] + ".memory.json")
                )
                await env.start()
                env.workspace_export_path = root / (
                    record["prompt_uid"] + ".workspace.json"
                )
                memory = env.memory
                phase = "rollout"
                for turn in range(args.turns):

                    def count_tokens():
                        payload = {
                            "model": endpoint["model"],
                            "messages": model_messages(),
                            "tools": tools,
                            "add_generation_prompt": True,
                            "chat_template_kwargs": {
                                "enable_thinking": args.thinking,
                                "preserve_thinking": args.preserve_thinking,
                            },
                        }
                        req = urllib.request.Request(
                            endpoint["base_url"].removesuffix("/v1") + "/tokenize",
                            data=json.dumps(payload).encode(),
                            headers={"Content-Type": "application/json"},
                        )
                        with urllib.request.urlopen(req, timeout=30) as reply:
                            return json.load(reply)["count"]

                    prompt_tokens = await asyncio.to_thread(count_tokens)
                    if args.context_clear and prompt_tokens > args.clear_trigger:
                        before = prompt_tokens
                        removed = 0
                        removed_tokens = 0
                        while True:
                            while groups and prompt_tokens > args.clear_target:
                                prior = prompt_tokens
                                groups.pop(0)
                                removed += 1
                                prompt_tokens = await asyncio.to_thread(count_tokens)
                                removed_tokens += prior - prompt_tokens
                            if args.context_feedback:
                                notice_text = clear_notice(
                                    args.context,
                                    args.clear_trigger,
                                    removed,
                                    removed_tokens,
                                    memory,
                                    args.memory_title_limit,
                                )
                                prompt_tokens = await asyncio.to_thread(count_tokens)
                            if prompt_tokens <= args.clear_target or not groups:
                                break
                        clears += 1
                        warning_sent = False
                        context_events.append(
                            {
                                "turn": turn,
                                "before_tokens": before,
                                "after_tokens": prompt_tokens,
                                "removed_groups": removed,
                            }
                        )
                        if args.context_feedback:
                            feedback_events.append(
                                {
                                    "turn": turn,
                                    "type": "clear",
                                    "removed_groups": removed,
                                    "removed_tokens": removed_tokens,
                                }
                            )
                        if prompt_tokens > args.clear_target:
                            reason = "immutable_context_overflow"
                            break
                    margin = args.warning_margin or args.tokens
                    if (
                        args.context_feedback
                        and not warning_sent
                        and prompt_tokens >= args.clear_trigger - margin
                        and not (context_events and context_events[-1]["turn"] == turn)
                    ):
                        notice_text = warning_notice(args.context, args.clear_trigger)
                        warning_sent = True
                        prompt_tokens = await asyncio.to_thread(count_tokens)
                        feedback_events.append(
                            {
                                "turn": turn,
                                "type": "warning",
                                "input_tokens": prompt_tokens,
                            }
                        )
                    headroom = args.context - prompt_tokens - 512
                    if headroom < 512:
                        reason = "context_limit"
                        break
                    body = {
                        "model": endpoint["model"],
                        "messages": model_messages(),
                        "temperature": args.temperature,
                        "top_p": args.top_p,
                        "max_tokens": (
                            min(
                                args.tokens, headroom, args.generation_limit - generated
                            )
                            if args.generation_limit
                            else min(args.tokens, headroom)
                        ),
                        "top_k": args.top_k,
                        "min_p": args.min_p,
                        "presence_penalty": args.presence_penalty,
                        "repetition_penalty": args.repetition_penalty,
                        "tools": tools,
                        "tool_choice": "auto",
                        "chat_template_kwargs": {
                            "enable_thinking": args.thinking,
                            "preserve_thinking": args.preserve_thinking,
                        },
                        "seed": args.seed + turn,
                    }

                    def request():
                        req = urllib.request.Request(
                            endpoint["base_url"] + "/chat/completions",
                            data=json.dumps(body).encode(),
                            headers={"Content-Type": "application/json"},
                        )
                        with urllib.request.urlopen(
                            req, timeout=args.request_timeout
                        ) as reply:
                            return json.load(reply)

                    response = await asyncio.to_thread(request)
                    message = response["choices"][0]["message"]
                    text = message.get("content") or ""
                    generated += response["usage"]["completion_tokens"]
                    calls = message.get("tool_calls") or []
                    group = [message]
                    observations = []
                    frames = []
                    if not calls:
                        errors += 1
                        observations.append(
                            {
                                "error": "No native tool call provided",
                                "hint": "Use the provided function tools with their required arguments.",
                            }
                        )
                        group.append(
                            {
                                "role": "user",
                                "content": "Tool result: "
                                + json.dumps(observations[-1]),
                            }
                        )
                    for call in calls:
                        if env.done:
                            observation = {
                                "error": "Episode already ended; this call was not executed."
                            }
                        else:
                            try:
                                action = parse_action(
                                    json.dumps(call["function"]), record["tool_schemas"]
                                )
                                observation = await env.step(action)
                                valid += 1
                            except (ValueError, KeyError, TypeError) as exc:
                                observation = {
                                    "error": str(exc),
                                    "hint": "Use the provided function tools with their required arguments.",
                                }
                            if observation.get("error"):
                                errors += 1
                        observations.append(observation)
                        public = {
                            k: v
                            for k, v in observation.items()
                            if k not in ("score", "reward", "final_state_variable")
                        }
                        group.append(
                            {
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": json.dumps(public),
                            }
                        )
                        if observation.get("image_request"):
                            frames.append(
                                frame_message(env, observation["image_request"])
                            )
                    observation = next(
                        (o for o in observations if o.get("done")), observations[-1]
                    )
                    events.append(
                        {
                            "turn": turn,
                            "text": text,
                            "reasoning": message.get(
                                "reasoning", message.get("reasoning_content")
                            ),
                            "tool_calls": calls,
                            "observation": observation,
                            "observations": observations,
                            "usage": response["usage"],
                            "finish_reason": response["choices"][0]["finish_reason"],
                        }
                    )
                    group.extend(frames)
                    groups.append(group)
                    if observation.get("done"):
                        reward = observation.get("reward", 0.0)
                        score = observation.get("score")
                        reason = "terminal"
                        break
                    (root / (record["prompt_uid"] + ".partial.json")).write_text(
                        json.dumps(
                            {
                                "events": events,
                                "generated_tokens": generated,
                                "context_events": context_events,
                                "feedback_events": feedback_events,
                                "memory": memory,
                            }
                        )
                        + "\n"
                    )
                    if args.generation_limit and generated >= args.generation_limit:
                        reason = "generation_limit"
                        break
                if (
                    reason
                    in (
                        "turn_limit",
                        "generation_limit",
                        "context_limit",
                        "context_overflow",
                        "immutable_context_overflow",
                    )
                    and not env.done
                ):
                    final = await env.finalize(reason)
                    reward = final["reward"]
                    score = final["score"]
            except Exception as exc:
                reason = (
                    "invalid_input"
                    if phase == "input"
                    and isinstance(exc, (ValueError, OSError, KeyError, TypeError))
                    else "request_or_environment_failure"
                )
                reward = None
                score = None
                events.append({"error": str(exc), "phase": phase})
            finally:
                if env is not None:
                    try:
                        await env.close()
                    except Exception as exc:
                        reason = "request_or_environment_failure"
                        reward = None
                        score = None
                        events.append({"error": str(exc), "phase": "cleanup"})
            shaped_reward = (
                terminal_reward(
                    score,
                    len(env.pad.case.characters),
                    {"mode": "placement_shaped", "placement_weight": 0.2},
                )
                if score
                else None
            )
            execution_errors = sum(
                bool(o.get("error"))
                for e in events
                for o in e.get("observations", [e.get("observation", {})])
            )
            result = {
                "case_id": record["prompt_uid"],
                "reward": reward,
                "training_reward": shaped_reward,
                "execution_errors": execution_errors,
                "truncated_turns": sum(
                    e.get("finish_reason") == "length" for e in events
                ),
                "reasoning_only_turns": sum(
                    bool(e.get("reasoning"))
                    and not e.get("tool_calls")
                    and not e.get("text")
                    for e in events
                ),
                "context_clears": clears,
                "context_warnings": sum(
                    e["type"] == "warning" for e in feedback_events
                ),
                "submit_turn": len(events) if reason == "terminal" else None,
                "memory_calls": sum(
                    any(
                        c.get("function", {}).get("name") == "memory"
                        for c in e.get("tool_calls", [])
                    )
                    for e in events
                ),
                "score": score,
                "termination": reason,
                "turns": len(events),
                "valid_calls": valid,
                "errors": errors,
                "generated_tokens": generated,
                "seconds": time.monotonic() - start,
            }
            (root / (record["prompt_uid"] + ".json")).write_text(
                json.dumps(
                    {
                        "result": result,
                        "events": events,
                        "context_events": context_events,
                        "feedback_events": feedback_events,
                        "memory": memory,
                    },
                    indent=2,
                )
                + "\n"
            )
            print(json.dumps(result), flush=True)
            return result

    results = await asyncio.gather(*(evaluate(r) for r in records))
    summary = {
        "model": endpoint["model"],
        "cases": len(results),
        "solved": sum(bool((r["score"] or {}).get("solved")) for r in results),
        "positive_training_rewards": sum(
            (r["training_reward"] or 0) > 0 for r in results
        ),
        "submitted": sum(r["termination"] == "terminal" for r in results),
        "invalid_attempts": sum(
            r["termination"] in ("invalid_input", "request_or_environment_failure")
            for r in results
        ),
        "invalid_inputs": sum(r["termination"] == "invalid_input" for r in results),
        "infrastructure_failures": sum(
            r["termination"] == "request_or_environment_failure" for r in results
        ),
        "truncated_turns": sum(r["truncated_turns"] for r in results),
        "reasoning_only_turns": sum(r["reasoning_only_turns"] for r in results),
        "valid_calls": sum(r["valid_calls"] for r in results),
        "errors": sum(r["errors"] for r in results),
        "settings": vars(args),
        "protocol": (
            "persistent Python workspace" if args.workspace else "inline Python"
        )
        + " with native model function calling; no JSON constrained decoding",
        "scope": (
            "teacher collection on training-only queries"
            if args.purpose == "teacher"
            else "fixed local validation only; no official puzzles; no training; one stochastic attempt per case"
        ),
        "tool_packages": (DEFAULTS / "tool-requirements.txt").read_text(),
        "results": results,
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        "BENCHMARK_COMPLETE",
        json.dumps({k: v for k, v in summary.items() if k != "results"}),
        flush=True,
    )


p = argparse.ArgumentParser()
p.add_argument("--seed", type=int, default=42)
p.add_argument("--parallel", type=int, default=2)
p.add_argument("--temperature", type=float, default=0.7)
p.add_argument("--top-p", type=float, default=0.9)
p.add_argument("--endpoint", required=True)
p.add_argument("--input", required=True)
p.add_argument("--out", required=True)
p.add_argument("--turns", type=int, default=32)
p.add_argument("--tokens", type=int, default=10240)
p.add_argument("--request-timeout", type=int, default=600)
p.add_argument("--context", type=int, default=16384)
p.add_argument("--generation-limit", type=int, default=32768)
p.add_argument("--context-clear", action="store_true")
p.add_argument("--clear-trigger", type=int, default=49152)
p.add_argument("--clear-target", type=int, default=32768)
p.add_argument("--thinking", action="store_true")
p.add_argument("--preserve-thinking", action="store_true")
p.add_argument("--top-k", type=int, default=-1)
p.add_argument("--min-p", type=float, default=0.0)
p.add_argument("--presence-penalty", type=float, default=0.0)
p.add_argument("--repetition-penalty", type=float, default=1.0)
p.add_argument("--context-feedback", action="store_true")
p.add_argument("--warning-margin", type=int)
p.add_argument("--memory-title-limit", type=int, default=32)
p.add_argument("--workspace", action=argparse.BooleanOptionalAction, default=True)
p.add_argument("--python-timeout", type=float, default=120)
p.add_argument(
    "--keep-input-protocol", action=argparse.BooleanOptionalAction, default=True
)
p.add_argument("--purpose", choices=["evaluation", "teacher"], default="evaluation")
p.add_argument("--asset-root", help="Root directory of local screenshot assets")
if __name__ == "__main__":
    asyncio.run(main(p.parse_args()))
