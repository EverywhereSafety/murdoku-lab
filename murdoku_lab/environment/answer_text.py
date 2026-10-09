"""Parse public placements, verdicts and legacy ACTION messages."""

from dataclasses import dataclass
import re
from murdoku_lab.core.render import parse_cell
from murdoku_lab.environment.state import Scratchpad

ACTION_RE = re.compile(r"^\s*ACTION:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)

CODE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class ParsedAction:
    raw: str
    code: str | None = None


def extract_code(text: str, after: int = 0, before: int | None = None) -> str | None:
    """The first fenced code block starting at or after `after`. Models put the block on the lines
    following `ACTION: python`, so the action line itself carries no payload."""
    m = CODE_RE.search(text, after, len(text) if before is None else before)
    return m.group(1) if m else None


def extract_actions(text: str) -> list[ParsedAction]:
    """Parse top-level ACTION lines and bind each Python action to its own following code block.

    Model-written programs sometimes contain literal ``ACTION: ...`` lines. Those are program data,
    not environment commands, so fenced spans are excluded. Likewise, when one reply contains two
    Python actions, each action must execute the block that follows it rather than replaying the
    first block twice.
    """
    code_spans = [(m.start(), m.end()) for m in CODE_RE.finditer(text)]

    def in_code(pos: int) -> bool:
        return any(start <= pos < end for start, end in code_spans)

    matches = [m for m in ACTION_RE.finditer(text) if not in_code(m.start())]
    parsed: list[ParsedAction] = []
    for i, match in enumerate(matches):
        raw = match.group(1).strip()
        verb = raw.split()[0].lower() if raw.split() else ""
        code = None
        if verb == "python":
            before = matches[i + 1].start() if i + 1 < len(matches) else None
            code = extract_code(text, after=match.end(), before=before)
        parsed.append(ParsedAction(raw=raw, code=code))
    return parsed


_VERDICT_LINE = re.compile(
    r"^\s*(?:MURDERER|ANSWER|VERDICT|KILLER|CULPRIT)\s*[:\-]\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def extract_verdict(text: str) -> str | None:
    """The `MURDERER: <name>` line, if the model wrote one. Last match wins: a model that revises
    itself mid-message means the final statement, and the protocol puts this line at the very end.
    """
    m = _VERDICT_LINE.findall(CODE_RE.sub("", text))
    return m[-1].strip() if m else None


def absorb_placement(pad: Scratchpad, text: str) -> int:
    """Pull "<Name> <square>" lines out of a one-shot reply into the scratchpad.

    Only a *bookkeeping* transfer, exactly like the `place` action: it records what the model
    claimed so `placed`/`exact` can be scored, and it never tells the model anything. Lines that
    do not resolve to a person and a square are ignored rather than counted as errors — prose
    around the block is expected.
    """
    n = 0
    for line in CODE_RE.sub("", text).splitlines():
        line = line.strip().lstrip("-*0123456789.) ").strip()
        if not line or line.lower().startswith(("answer:", "placement")):
            continue
        parts = line.replace(",", " ").replace(":", " ").split()
        if len(parts) < 2:
            continue
        k = parse_cell(pad.case, parts[-1])
        if k is None:
            continue
        who = pad.sym(" ".join(parts[:-1]))
        if who is None or who in pad.placed:
            continue
        pad.placed[who] = k
        n += 1
    return n
