"""Retry accounting must distinguish infrastructure recovery from model attempts."""

import io
import json
import urllib.error

from murdoku_lab.setter.llm_client import LLMClient


class _Response:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def _client(monkeypatch):
    monkeypatch.setenv("TEST_LLM_KEY", "not-a-real-secret")
    return LLMClient(
        model="test-model",
        cfg={
            "base_url": "https://example.invalid/v1",
            "api_key_var": "TEST_LLM_KEY",
            "api_key_var_alt": None,
            "base_url_var": None,
            "env_file": "",
            "models": {"default": "test-model"},
            "timeout_s": 1,
            "max_retries": 2,
            "max_rate_retries": 2,
            "model_min_interval_s": {},
        },
    )


def test_rate_limit_retry_is_recorded_but_not_counted_as_a_model_call(monkeypatch):
    client = _client(monkeypatch)
    replies = [
        urllib.error.HTTPError(
            client.endpoint,
            429,
            "limited",
            {"Retry-After": "2"},
            io.BytesIO(b'{"error":"limited"}'),
        ),
        _Response(
            {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 1},
            }
        ),
    ]

    def fake_open(*args, **kwargs):
        item = replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    waits = []
    monkeypatch.setattr(
        "murdoku_lab.setter.llm_client.urllib.request.urlopen", fake_open
    )
    monkeypatch.setattr("murdoku_lab.setter.llm_client.time.sleep", waits.append)
    assert client.chat([{"role": "user", "content": "x"}]) == "ok"
    assert client.usage.calls == 1
    assert client.usage.request_attempts == 2
    assert client.usage.retries == client.usage.rate_limit_retries == 1
    assert client.usage.transient_retries == 0
    assert client.usage.wait_s == 2


def test_reasoning_content_is_preserved_for_multiturn_models(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(
        "murdoku_lab.setter.llm_client.urllib.request.urlopen",
        lambda *a, **k: _Response(
            {
                "choices": [
                    {"message": {"content": "", "reasoning_content": "partial proof"}}
                ],
                "usage": {"completion_tokens": 7},
            }
        ),
    )
    assert client.chat([{"role": "user", "content": "x"}]) == ""
    assert client.last_reasoning == "partial proof"


def test_transient_retry_has_a_finite_budget(monkeypatch):
    client = _client(monkeypatch)

    def unavailable(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(
        "murdoku_lab.setter.llm_client.urllib.request.urlopen", unavailable
    )
    monkeypatch.setattr("murdoku_lab.setter.llm_client.time.sleep", lambda _: None)
    try:
        client.chat([{"role": "user", "content": "x"}])
    except RuntimeError as e:
        assert "LLM call failed" in str(e)
    else:
        raise AssertionError("persistent transport failure must surface")
    assert client.usage.request_attempts == 3  # initial request + two retries
    assert client.usage.transient_retries == 2
