"""Minimal OpenAI-compatible chat client. Self-contained by design (no sibling-repo imports).

Secrets: the API key is read from the env file named in `config/llm.json` (or the process env) and
is never logged, never written into a record, and never echoed in an error message. Only the
variable *name* appears in diagnostics.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from murdoku_lab.paths import PROJECT_ROOT

CONFIG = PROJECT_ROOT / "config" / "llm.json"


def _load_cfg() -> dict:
    return json.loads(CONFIG.read_text())


def _read_env_file(path: str) -> dict[str, str]:
    p = Path(os.path.expanduser(path))
    if not p.is_file():
        return {}
    out: dict[str, str] = {}
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = line[7:].lstrip() if line.startswith("export ") else line
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


_OPTIONAL_FIELDS = ("temperature", "top_p", "stop", "max_tokens")


def _retry_after(e) -> float | None:
    """Seconds the server asked us to wait, if it said so. Only the integer form is accepted; the
    HTTP-date variant is not worth parsing here."""
    try:
        v = (e.headers or {}).get("Retry-After")
    except Exception:  # noqa: BLE001
        return None
    try:
        return max(1.0, float(str(v).strip())) if v else None
    except (TypeError, ValueError):
        return None


def _unsupported_field(detail: str, body: dict) -> str | None:
    """Which optional request field did the server just refuse? Matches phrasings like
    "`temperature` is deprecated for this model" / "unsupported parameter: top_p"."""
    low = detail.lower()
    for f in _OPTIONAL_FIELDS:
        if (
            f in body
            and f in low
            and any(
                w in low
                for w in (
                    "deprecat",
                    "unsupport",
                    "not supported",
                    "unrecognized",
                    "unknown",
                    "invalid",
                    "not allowed",
                )
            )
        ):
            return f
    return None


def _SECRET_VARS(cfg: dict) -> set[str]:
    """The only variable names we will pick up from the process environment."""
    return {
        v
        for v in (
            cfg.get("api_key_var"),
            cfg.get("api_key_var_alt"),
            cfg.get("base_url_var"),
        )
        if v
    }


class LLMUnavailable(RuntimeError):
    """Raised when no API key is configured. Callers should degrade, not crash the run."""


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 0
    request_attempts: int = 0
    retries: int = 0
    rate_limit_retries: int = 0
    transient_retries: int = 0
    wait_s: float = 0.0

    def add(self, d: dict) -> None:
        self.prompt_tokens += int(d.get("prompt_tokens", 0) or 0)
        self.completion_tokens += int(d.get("completion_tokens", 0) or 0)
        self.calls += 1

    def to_json(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "calls": self.calls,
            "request_attempts": self.request_attempts,
            "retries": self.retries,
            "rate_limit_retries": self.rate_limit_retries,
            "transient_retries": self.transient_retries,
            "wait_s": round(self.wait_s, 3),
        }


_RATE_LOCK = threading.Lock()
_LAST_REQUEST: dict[str, float] = {}


@dataclass
class LLMClient:
    model: str | None = None
    role: str = "default"
    cfg: dict = field(default_factory=_load_cfg)
    usage: Usage = field(default_factory=Usage)
    last_reasoning: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        self.model = self.model or self.cfg["models"].get(
            self.role, self.cfg["models"]["default"]
        )

    # ------------------------------------------------------------------------------------ auth
    def _env(self) -> dict[str, str]:
        """Process environment overlaid on the key file. Read fresh, never cached onto the object,
        so a key never lingers in a repr, a pickle or a traceback frame."""
        d = _read_env_file(self.cfg.get("env_file", ""))
        d.update({k: v for k, v in os.environ.items() if k in _SECRET_VARS(self.cfg)})
        return d

    @property
    def _key(self) -> str:
        env = self._env()
        vars_ = [
            v
            for v in (self.cfg.get("api_key_var"), self.cfg.get("api_key_var_alt"))
            if v
        ]
        for var in vars_:
            key = env.get(var)
            if key:
                return key
        raise LLMUnavailable(
            f"no API key: set one of {vars_} in the environment, or put it in "
            f"{self.cfg.get('env_file')!r} (referenced by config/llm.json). "
            f"The key itself is never logged."
        )

    @property
    def endpoint(self) -> str:
        """The key file may carry its own base URL; it wins, so moving endpoint is not a code edit."""
        var = self.cfg.get("base_url_var")
        url = (self._env().get(var) if var else None) or self.cfg["base_url"]
        return url.rstrip("/") + "/chat/completions"

    def available(self) -> bool:
        try:
            _ = self._key
            return True
        except LLMUnavailable:
            return False

    def _wait_for_rate_slot(self) -> None:
        """Apply an optional per-model minimum request interval across clients in this process."""
        configured = self.cfg.get("model_min_interval_s", {})
        interval = float(configured.get(self.model, 0.0) or 0.0)
        if interval <= 0:
            return
        with _RATE_LOCK:
            now = time.monotonic()
            delay = max(0.0, _LAST_REQUEST.get(str(self.model), 0.0) + interval - now)
            if delay:
                time.sleep(delay)
                self.usage.wait_s += delay
            _LAST_REQUEST[str(self.model)] = time.monotonic()

    # ------------------------------------------------------------------------------------ call
    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float | None = None,
        max_tokens: int = 4096,
        stop: list[str] | None = None,
        timeout_s: float | None = None,
    ) -> str:
        """`temperature=None` omits the field. Some deployed models reject it outright, so it is
        opt-in rather than defaulted, and a 400 naming an unsupported field strips that field and
        retries once — sampling knobs are not worth failing a run over. Diversity in this project
        comes from the prompt (the `style` string), not from temperature."""
        body: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if stop:
            body["stop"] = stop
        url = self.endpoint
        last: Exception | None = None
        transient_retries = rate_retries = 0
        max_transient = int(self.cfg.get("max_retries", 3))
        max_rate = int(self.cfg.get("max_rate_retries", 6))
        while True:
            self._wait_for_rate_slot()
            self.usage.request_attempts += 1
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._key}",
                },
            )
            try:
                with urllib.request.urlopen(
                    req, timeout=timeout_s or self.cfg.get("timeout_s", 120)
                ) as r:
                    d = json.loads(r.read())
                self.usage.add(d.get("usage", {}))
                message = d["choices"][0]["message"]
                self.last_reasoning = message.get("reasoning_content") or ""
                return message.get("content") or ""
            except urllib.error.HTTPError as e:
                # The body carries the actual reason (bad model name, bad field). Surfacing it is
                # the difference between a debuggable error and "400". It cannot contain the key:
                # the key only ever travels in the request header.
                try:
                    detail = e.read().decode(errors="replace")[:600]
                except Exception:  # noqa: BLE001
                    detail = ""
                last = RuntimeError(f"HTTP {e.code}: {detail or e.reason}")
                dropped = _unsupported_field(detail, body)
                if dropped:
                    body.pop(dropped)
                    self.usage.retries += 1
                    continue  # retry without the field
                if e.code == 429:
                    # Rate limits are per-model on this gateway and can be as low as one request
                    # per MINUTE, so exponential backoff from a one-second base gives up long
                    # before the window reopens. Honour Retry-After, else wait out a full minute,
                    # and keep a separate budget so a slow queue is not mistaken for a failure.
                    rate_retries += 1
                    if rate_retries > max_rate:
                        break
                    delay = _retry_after(e) or 60.0
                    self.usage.retries += 1
                    self.usage.rate_limit_retries += 1
                    time.sleep(delay)
                    self.usage.wait_s += delay
                    continue
                if 400 <= e.code < 500 and e.code not in (408, 409, 425):
                    break  # our fault; a retry cannot fix it
                transient_retries += 1
                if transient_retries > max_transient:
                    break
                delay = min(2 ** (transient_retries - 1), 20)
                self.usage.retries += 1
                self.usage.transient_retries += 1
                time.sleep(delay)
                self.usage.wait_s += delay
            except (urllib.error.URLError, KeyError, TimeoutError) as e:
                last = e
                transient_retries += 1
                if transient_retries > max_transient:
                    break
                delay = min(2 ** (transient_retries - 1), 20)
                self.usage.retries += 1
                self.usage.transient_retries += 1
                time.sleep(delay)
                self.usage.wait_s += delay
        raise RuntimeError(f"LLM call failed: {type(last).__name__}: {last}")
