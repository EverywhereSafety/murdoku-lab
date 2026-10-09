"""Check portable runtime selection without executing model code or bubblewrap."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
from murdoku_lab.environment.python import run_python


def test_runtime_and_mounts_are_explicit(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "bin").mkdir(parents=True)
    (runtime / "bin/python").touch()
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    process = AsyncMock()
    process.returncode = 0
    process.communicate.return_value = (b'{"output":"ok","done":false}', b"")
    env = {
        "LONG_HORIZON_TOOL_RUNTIME": str(runtime),
        "LONG_HORIZON_SANDBOX_BINDS": json.dumps([str(dependency)]),
    }
    with (
        patch.dict("os.environ", env, clear=True),
        patch("asyncio.create_subprocess_exec", return_value=process) as launch,
    ):
        result = asyncio.run(run_python(code="print(1)"))
    command = launch.call_args.args
    assert str(runtime) in command
    assert str(dependency) in command
    assert "/storage/pace-apps" not in command
    assert result["output"] == "ok"
    request = json.loads(process.communicate.call_args.args[0])
    assert request["memory_bytes"] == 2 * 1024**3
    assert any(Path(arg).name == "python_worker.py" for arg in command)


def test_standalone_runtime_setting_takes_precedence(tmp_path):
    runtime = tmp_path / "standalone"
    (runtime / "bin").mkdir(parents=True)
    (runtime / "bin/python").touch()
    process = AsyncMock()
    process.returncode = 0
    process.communicate.return_value = (b'{"output":"ok","done":false}', b"")
    with (
        patch.dict(
            "os.environ",
            {
                "MURDOKU_TOOL_RUNTIME": str(runtime),
                "LONG_HORIZON_TOOL_RUNTIME": str(tmp_path / "other"),
            },
            clear=True,
        ),
        patch("asyncio.create_subprocess_exec", return_value=process) as launch,
    ):
        asyncio.run(run_python(code="print(1)"))
    assert str(runtime) in launch.call_args.args
    assert str(tmp_path / "other") not in launch.call_args.args
