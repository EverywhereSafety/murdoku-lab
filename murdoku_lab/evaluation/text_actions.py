"""Direct-answer and text-action benchmark runners.

Uses the shared task state, grader and text submission parser.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Protocol

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme, canonical_theme
from murdoku_lab.environment.state import Scratchpad, apply_action
from murdoku_lab.environment.scoring import (
    score_episode,
    classify_outcome,
)
from murdoku_lab.evaluation.legacy_python import run_python
from murdoku_lab.core.render import render_case, render_scene
from murdoku_lab.environment.answer_text import (
    extract_actions,
    absorb_placement,
    extract_verdict,
)

MAX_TURNS = 40


# =============================================================================================
# Action protocol — plain text, so any model can drive it without tool-calling support
# =============================================================================================


PROTOCOL = """HOW TO ACT
Work concisely and use Python when search is useful. EVERY reply must contain at least one ACTION
line; on your first reply, either solve directly or emit ACTION: python with a fenced program.
Actions have the form:

  ACTION: mark <person> <cell> [<cell> ...]   -- record the squares still possible for a person
  ACTION: unmark <person> <cell> [...]        -- remove candidate squares
  ACTION: place <person> <cell>               -- commit a person to a square
  ACTION: unplace <person>                    -- take a placement back
  ACTION: board                               -- show your current grid and placements
  ACTION: check                               -- list any row/column/blocked-square rule breaches
  ACTION: python                              -- run Python; put the code in a ``` block after it
  ACTION: solve                               -- submit your final answer; this ends the case

Cells are named column-letter + row-number, e.g. c4. You may issue several ACTION lines per turn.

RUNNING CODE
Write `ACTION: python` and then a fenced code block. Print what you want to see; only stdout comes
back, truncated if long. Pure computation only — no files, no network, no imports beyond the standard
computational modules (itertools, math, collections, re, json, heapq, functools, ...). Nothing is
carried over between runs, so each block must stand alone.

  ACTION: python
  ```python
  import itertools
  for p in itertools.permutations(range(6)):
      ...
  ```

WHAT COUNTS AS AN ANSWER
The answer is the WHOLE arrangement — every person and the square they stood on — not just a name.
End with `ACTION: solve` followed by one line per person:

  ACTION: solve
  <Name> <square>
  ... every person, including the victim ...
  MURDERER: <name>

You may also build the grid up with `place` as you go; whatever is placed when you `solve` counts,
and lines after `solve` add to it. A named murderer with no arrangement behind it scores nothing:
there are only a handful of suspects, so naming one is not evidence of having solved anything.
"""

DIRECT_PROTOCOL = """Answer in one reply. Reason as much as you like, then finish with the WHOLE
arrangement — every person and the square they stood on — and only then the verdict:

  PLACEMENT:
  <Name> <square>
  ... one line per person, including the victim ...
  MURDERER: <name>

The arrangement is what is scored. There are only a handful of suspects, so naming one without the
grid behind it is indistinguishable from a guess and scores nothing."""


@dataclass
class Turn:
    role: str
    text: str
    actions: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)


class Agent(Protocol):
    name: str

    def act(self, prompt: str, history: list[Turn]) -> str: ...


# =============================================================================================
# Environment step
# =============================================================================================
# =============================================================================================
# Episode runners
# =============================================================================================
@dataclass
class EpisodeResult:
    case_id: str
    band: str | None
    variant: str
    mode: str
    agent: str
    theme_id: str
    turns: int
    invalid_actions: int
    assists_used: int
    wall_s: float
    score: dict
    python_calls: int = 0
    python_refusals: int = 0
    usage: dict = field(default_factory=dict)
    transcript: list[dict] = field(default_factory=list)
    error: str | None = None
    scene_format: str = "compact"
    outcome: str = "unknown"

    def to_json(self) -> dict:
        d = self.__dict__.copy()
        return d


def run_agentic(
    case: Case,
    agent: Agent,
    theme: Theme | None = None,
    *,
    max_turns: int = MAX_TURNS,
    allow_check: bool = True,
    allow_python: bool = True,
    python_timeout_s: float = 20.0,
    keep_transcript: bool = True,
    scene_format: str = "compact",
) -> EpisodeResult:
    theme = theme or canonical_theme(case)
    pad = Scratchpad(case, theme)
    history: list[Turn] = []
    prompt = render_case(case, theme, scene_format=scene_format) + "\n" + PROTOCOL
    t0 = time.time()
    answer: str | None = None
    invalid = assists = python_calls = python_refusals = 0
    err = None

    for turn in range(max_turns):
        try:
            text = agent.act(prompt if turn == 0 else "", history)
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
            break
        parsed_actions = extract_actions(text)
        acts = [action.raw for action in parsed_actions]
        obs: list[str] = []
        for action in parsed_actions:
            raw = action.raw
            verb = raw.split()[0].lower() if raw.split() else ""
            if verb == "check":
                assists += 1
                if not allow_check:
                    obs.append("`check` is disabled in this run.")
                    continue
            if verb == "python":
                if not allow_python:
                    obs.append("`python` is disabled in this run.")
                    continue
                code = action.code
                if code is None:
                    invalid += 1
                    obs.append(
                        "No fenced code block found after `ACTION: python`. "
                        "Put the code in a ```python ... ``` block."
                    )
                    continue
                r = run_python(code, timeout_s=python_timeout_s)
                python_calls += 1
                if r.refused:
                    python_refusals += 1
                obs.append(r.observation())
                continue
            o, sub = apply_action(pad, raw)
            if o.startswith(
                ("Unknown action", "Could not read", "No such person", "Empty action")
            ):
                invalid += 1
            obs.append(o)
            if sub is not None:
                # The arrangement is the answer, so sweep any "<Name> <square>" lines out of the
                # same message. A model that lists the grid under `solve` has answered in full.
                absorb_placement(pad, text)
                # The protocol asks for the verdict on its own `MURDERER:` line, which is where
                # models actually put it — so read it from the message rather than expecting it as
                # an argument to `solve`.
                answer = extract_verdict(text) or sub
                break
        if not acts:
            invalid += 1
            obs.append(
                "No ACTION line found. Emit at least one `ACTION: ...` line, and "
                "`ACTION: solve` with the full arrangement when you are done."
            )
        history.append(Turn("assistant", text, acts, obs))
        if answer is not None:
            break

    score = score_episode(case, theme, pad, answer)
    return EpisodeResult(
        case_id=case.content_hash(),
        band=case.target_band,
        variant=case.variant,
        mode="agentic",
        agent=agent.name,
        theme_id=theme.theme_id,
        turns=len(history),
        invalid_actions=invalid,
        assists_used=assists,
        python_calls=python_calls,
        python_refusals=python_refusals,
        wall_s=round(time.time() - t0, 2),
        score=score,
        usage=getattr(agent, "usage_json", lambda: {})(),
        transcript=(
            [
                {"text": t.text, "actions": t.actions, "observations": t.observations}
                for t in history
            ]
            if keep_transcript
            else []
        ),
        error=err,
        scene_format=scene_format,
        outcome=classify_outcome(score, err),
    )


def run_direct(
    case: Case,
    agent: Agent,
    theme: Theme | None = None,
    *,
    keep_transcript: bool = True,
    scene_format: str = "compact",
) -> EpisodeResult:
    theme = theme or canonical_theme(case)
    pad = Scratchpad(case, theme)
    prompt = (
        render_case(case, theme, scene_format=scene_format) + "\n" + DIRECT_PROTOCOL
    )
    t0 = time.time()
    err, answer, text = None, None, ""
    try:
        text = agent.act(prompt, [])
        answer = extract_verdict(text) or (text.strip().splitlines() or [""])[-1]
        absorb_placement(pad, text)
    except Exception as e:  # noqa: BLE001
        err = f"{type(e).__name__}: {e}"
    score = score_episode(case, theme, pad, answer)
    return EpisodeResult(
        case_id=case.content_hash(),
        band=case.target_band,
        variant=case.variant,
        mode="direct",
        agent=agent.name,
        theme_id=theme.theme_id,
        turns=1,
        invalid_actions=0 if answer else 1,
        assists_used=0,
        wall_s=round(time.time() - t0, 2),
        score=score,
        usage=getattr(agent, "usage_json", lambda: {})(),
        scene_format=scene_format,
        transcript=[{"text": text}] if keep_transcript else [],
        error=err,
        outcome=classify_outcome(score, err),
    )


RUNNERS: dict[str, Callable[..., EpisodeResult]] = {
    "direct": run_direct,
    "agentic": run_agentic,
}
