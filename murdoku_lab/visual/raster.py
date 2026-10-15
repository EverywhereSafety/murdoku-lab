"""Optional deterministic PNG rendering; no browser or model request required."""

import json
from pathlib import Path
import subprocess

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
FONT_DIR = Path(__file__).with_name("fonts")


def bundled_profile(fit_width=None):
    """Render with the packaged casebook fonts only, so PNGs match on every machine."""
    files = sorted(str(p) for p in FONT_DIR.glob("*.ttf"))
    if not files:
        raise RuntimeError("Bundled fonts missing. Run scripts/build_fonts.py.")
    profile = {
        "fontFiles": files,
        "loadSystemFonts": False,
        "defaultFontFamily": "DM Sans",
    }
    if fit_width:
        profile["fitWidth"] = int(fit_width)
    return profile


def png_from_svg(svg, *, profile=None):
    """`profile=None` keeps the legacy system-font rendering; pass `bundled_profile()` for
    casebook art."""
    command = ["node", str(Path(__file__).with_name("rasterize_svg.mjs"))]
    if profile:
        command.append(json.dumps(profile))
    try:
        process = subprocess.run(
            command,
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
