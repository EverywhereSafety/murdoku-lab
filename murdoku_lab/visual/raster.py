"""Optional deterministic PNG rendering; no browser or model request required."""

from pathlib import Path
import subprocess

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT


def png_from_svg(svg):
    try:
        process = subprocess.run(
            ["node", str(Path(__file__).with_name("rasterize_svg.mjs"))],
            input=svg.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=ROOT,
            timeout=30,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("PNG renderer timed out") from error
    if process.returncode:
        raise RuntimeError(
            "PNG renderer unavailable. Install this project with npm ci."
        )
    if not process.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("PNG renderer returned an invalid image")
    return process.stdout
