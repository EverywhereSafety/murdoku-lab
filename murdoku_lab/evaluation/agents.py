"""Agents for the harness: two reference baselines plus the LLM under test.

`oracle` and `chance` exist to calibrate the *harness*, not the models. Oracle must score 1.0 — if
it does not, the harness or the scorer is broken, not the model. Chance is the floor: it fixes what
"1/(n-1) by guessing" looks like on this metric, so a model's score can be read against something.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme, canonical_theme
from murdoku_lab.evaluation.text_actions import Turn
from murdoku_lab.core.render import cell_label
from murdoku_lab.setter.llm_client import LLMClient, LLMUnavailable
from murdoku_lab.solver.logic import certify


@dataclass
class OracleAgent:
    """Solves with our own deduction engine and plays the answer. A harness self-test."""

    case: Case
    theme: Theme | None = None
    name: str = "oracle"

    def act(self, prompt: str, history: list[Turn]) -> str:
        th = self.theme or canonical_theme(self.case)
        cert = certify(self.case)
        placed = cert.placed if cert.solved else dict(self.case.solution)
        lines = [
            f"ACTION: place {x} {cell_label(self.case, k)}" for x, k in placed.items()
        ]
        if self.case.vdef.answer == "murderer":
            ans = th.name(self.case.murderer)
        else:
            ans = cell_label(self.case, self.case.solution[self.case.victim])
        return (
            "Solved by constraint propagation.\n"
            + "\n".join(lines)
            + f"\nACTION: answer {ans}\nANSWER: {ans}"
        )


@dataclass
class ChanceAgent:
    """Names a uniformly random suspect (or a random open cell). The floor."""

    case: Case
    theme: Theme | None = None
    seed: int = 0
    name: str = "chance"

    def act(self, prompt: str, history: list[Turn]) -> str:
        th = self.theme or canonical_theme(self.case)
        rng = random.Random(self.seed + len(history))
        if self.case.vdef.answer == "murderer":
            ans = th.name(rng.choice(list(self.case.suspects)))
        else:
            ans = cell_label(self.case, rng.choice(sorted(self.case.scene.open_cells)))
        return f"Guessing.\nACTION: answer {ans}\nANSWER: {ans}"


SYSTEM = (
    "You are solving a logic-deduction murder puzzle. Be rigorous: every conclusion must "
    "follow from the clues and the rules. Never guess when a deduction is available, and "
    "never assert a placement you have not justified. If you find you have contradicted "
    "yourself, say so and revise."
)


@dataclass
class LLMAgent:
    """The model under test. Keeps a running message history across turns."""

    model: str | None = None
    temperature: float | None = None  # omitted from the request when None; some
    # deployed models reject the field outright
    max_tokens: int = 24576
    max_total_completion_tokens: int = 49152
    name: str = "llm"
    # A 30-turn episode resends the whole transcript every turn, which is what pushed replies past
    # the HTTP timeout. Keep the system prompt, the opening puzzle, and the most recent exchanges.
    max_history_turns: int = 24
    client: LLMClient = field(default=None)  # type: ignore[assignment]
    messages: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.client = self.client or LLMClient(model=self.model, role="solver")
        self.name = self.model or self.client.model

    def usage_json(self) -> dict:
        return self.client.usage.to_json()

    def act(self, prompt: str, history: list[Turn]) -> str:
        if not self.messages:
            self.messages = [{"role": "system", "content": SYSTEM}]
        if len(self.messages) > 1 + 2 * self.max_history_turns:
            head, tail = self.messages[:2], self.messages[-2 * self.max_history_turns :]
            self.messages = head + tail
        if prompt:
            self.messages.append({"role": "user", "content": prompt})
        elif history:
            last = history[-1]
            obs = "\n".join(f"[{i+1}] {o}" for i, o in enumerate(last.observations))
            self.messages.append(
                {
                    "role": "user",
                    "content": f"RESULT OF YOUR ACTIONS\n{obs}\n\n"
                    f"Continue. Emit ACTION lines.",
                }
            )
        spent = self.client.usage.completion_tokens
        remaining = self.max_total_completion_tokens - spent
        if remaining <= 0:
            raise RuntimeError(
                f"episode completion-token budget exhausted ({self.max_total_completion_tokens})"
            )
        text = self.client.chat(
            self.messages,
            temperature=self.temperature,
            max_tokens=min(self.max_tokens, remaining),
        )
        # An empty reply must not go into the history: some providers reject a conversation
        # containing an empty assistant turn outright ("the message at position 2 with role
        # 'assistant' must not be empty"), so one blank turn killed the whole episode on the NEXT
        # call rather than where it happened.
        assistant = {
            "role": "assistant",
            "content": text if (text or "").strip() else "(no final answer yet)",
        }
        reasoning = getattr(self.client, "last_reasoning", "")
        if reasoning:
            # Reasoning models need their prior reasoning state on the next turn. Dropping this made
            # Kimi restart after a max-token turn and spend the same tokens again.
            assistant["reasoning_content"] = reasoning
        self.messages.append(assistant)
        return text


def build_agent(
    kind: str,
    case: Case,
    theme: Theme | None = None,
    *,
    seed: int = 0,
    model: str | None = None,
    max_tokens: int = 24576,
    max_total_completion_tokens: int = 49152,
):
    if kind == "oracle":
        return OracleAgent(case, theme)
    if kind == "chance":
        return ChanceAgent(case, theme, seed=seed)
    if kind in ("llm", "model"):
        return LLMAgent(
            model=model,
            max_tokens=max_tokens,
            max_total_completion_tokens=max_total_completion_tokens,
        )
    raise ValueError(f"unknown agent {kind!r}")
