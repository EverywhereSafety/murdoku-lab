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


def profile_for(style):
    """Casebook art renders with the bundled fonts; the frozen legacy styles keep the system
    fonts they were published with."""
    from murdoku_lab.visual.art.styles import CASEBOOK

    return bundled_profile() if style == CASEBOOK else None


def png_for_style(svg, style):
    return png_from_svg(svg, profile=profile_for(style))


def renderer_info(style):
    """Provenance for dataset manifests: what drew the images and with which fonts."""
    from murdoku_lab.visual.art.styles import CASEBOOK, CASEBOOK_VERSION, check_style

    check_style(style)
    info = {
        "style": style,
        "renderer_version": CASEBOOK_VERSION if style == CASEBOOK else "legacy/1",
    }
    package = ROOT / "node_modules" / "@resvg" / "resvg-js" / "package.json"
    if package.exists():
        info["resvg_version"] = json.loads(package.read_text()).get("version")
    if style == CASEBOOK:
        import hashlib

        digest = hashlib.sha256()
        for path in sorted(FONT_DIR.glob("*.ttf")):
            digest.update(path.name.encode() + b"\0" + path.read_bytes())
        info["font_sha256"] = digest.hexdigest()
    else:
        info["fonts"] = "system"
    return info


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
