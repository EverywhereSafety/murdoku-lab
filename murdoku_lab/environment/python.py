"""Murdoku runtime configuration for the shared isolated Python tool."""

import os
from pathlib import Path
from murdoku_lab.paths import PROJECT_ROOT
from long_horizon_rl.python_tool import PythonTool


class MurdokuPythonTool(PythonTool):
    memory_bytes = 2 * 1024**3

    def runtime_path(self):
        return Path(
            os.environ.get(
                "MURDOKU_TOOL_RUNTIME",
                os.environ.get(
                    "LONG_HORIZON_TOOL_RUNTIME",
                    str(PROJECT_ROOT / ".tool-env"),
                ),
            )
        )


async def run_python(code=None, timeout=30, workspace=None, path=None):
    return await MurdokuPythonTool().run(code, timeout, workspace, path)
