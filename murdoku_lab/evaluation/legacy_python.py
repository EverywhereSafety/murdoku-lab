"""Restricted subprocess runner for the text-ACTION benchmark.

Uses an import allowlist and static screening. Native agent tools use the
Agent Horizon isolated Python runtime instead.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass

# Modules a solver legitimately wants: pure computation, no outside world.
ALLOWED_IMPORTS = {
    "itertools",
    "math",
    "collections",
    "functools",
    "operator",
    "re",
    "json",
    "heapq",
    "bisect",
    "random",
    "string",
    "copy",
    "fractions",
    "decimal",
    "statistics",
    "dataclasses",
    "typing",
    "enum",
    "abc",
    "numbers",
    "array",
    "types",
    "textwrap",
    "pprint",
    "unicodedata",
}

# Anything that reaches the filesystem, the network, or another process.
_BANNED = (
    r"\bopen\s*\(",
    r"\b__import__\b",
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"\bcompile\s*\(",
    r"\binput\s*\(",
    r"\bbreakpoint\s*\(",
    r"\bglobals\s*\(",
    r"\bvars\s*\(",
    r"\b__builtins__\b",
    r"\b__loader__\b",
    r"\b__spec__\b",
    r"\bobject\s*\.\s*__subclasses__",
)


@dataclass
class RunResult:
    ok: bool
    stdout: str
    stderr: str
    refused: str | None = None  # why the static screen rejected it, if it did
    timed_out: bool = False
    duration_s: float = 0.0

    def observation(self, *, max_chars: int = 4000) -> str:
        """What the model is shown. Truncated, because a solver that prints all 720 permutations
        should not be able to flood its own context — and the truncation is stated so it can adapt.
        """
        if self.refused:
            return f"REFUSED: {self.refused}\nNothing ran. Compute in memory; no files, no network."
        if self.timed_out:
            return f"TIMEOUT after {self.duration_s:.1f}s. Nothing returned. Try a cheaper search."
        body = self.stdout or "(no output — did you print anything?)"
        if self.stderr:
            body += "\nSTDERR:\n" + self.stderr
        if len(body) > max_chars:
            body = body[:max_chars] + f"\n... [truncated at {max_chars} chars]"
        return body


def screen(code: str) -> str | None:
    """Reason to refuse, or None. Runs before the subprocess exists."""
    for pat in _BANNED:
        m = re.search(pat, code)
        if m:
            return f"{m.group(0).strip()} is not available here"
    for m in re.finditer(
        r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", code, re.MULTILINE
    ):
        root = m.group(1).split(".")[0]
        if root not in ALLOWED_IMPORTS:
            return (
                f"module {root!r} is not available; allowed: "
                f"{', '.join(sorted(ALLOWED_IMPORTS))}"
            )
    return None


def run_python(
    code: str, *, timeout_s: float = 20.0, max_chars: int = 4000
) -> RunResult:
    """Execute `code` and capture its output. Never raises."""
    import time

    why = screen(code)
    if why:
        return RunResult(False, "", "", refused=why)

    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="murdoku_sbx_") as tmp:
        # -I: isolated mode — ignores PYTHONPATH and the user site directory, so the repository
        # (and therefore our solver and any emitted answer keys) is not importable.
        try:
            p = subprocess.run(
                [sys.executable, "-I", "-c", code],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env={"PATH": "/usr/bin:/bin", "HOME": tmp, "PYTHONIOENCODING": "utf-8"},
            )
        except subprocess.TimeoutExpired:
            return RunResult(False, "", "", timed_out=True, duration_s=time.time() - t0)
        except Exception as e:  # noqa: BLE001
            return RunResult(
                False, "", f"{type(e).__name__}: {e}", duration_s=time.time() - t0
            )

    return RunResult(
        p.returncode == 0,
        p.stdout[: max_chars * 2],
        p.stderr[-2000:],
        duration_s=round(time.time() - t0, 3),
    )
