"""Bundle the casebook fonts for deterministic SVG→PNG exports.

The web app self-hosts the same families through @fontsource packages. Exports render with
resvg, which needs TrueType files on disk: this converts the Latin WOFF subsets shipped in
those packages to TTF (a container change; glyphs are untouched) and records their source.

    npm ci && python scripts/build_fonts.py
"""

import hashlib
import json
import shutil
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "murdoku_lab" / "visual" / "fonts"
FONTS = {
    "dm-sans": ("DMSans", (400, 500, 600, 700), ("normal",)),
    "dm-mono": ("DMMono", (400, 500), ("normal",)),
    "newsreader": ("Newsreader", (400, 500, 600), ("normal", "italic")),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"source": "@fontsource packages (Latin subsets)", "files": {}}
    licences = []
    for package, (stem, weights, styles) in FONTS.items():
        base = ROOT / "node_modules" / "@fontsource" / package
        version = json.loads((base / "package.json").read_text())["version"]
        for weight in weights:
            for style in styles:
                src = base / "files" / f"{package}-latin-{weight}-{style}.woff"
                if not src.exists():
                    continue
                suffix = "Italic" if style == "italic" else ""
                name = f"{stem}-{weight}{suffix}.ttf"
                font = TTFont(src)
                font.flavor = None
                font.save(OUT / name)
                manifest["files"][name] = {
                    "package": f"@fontsource/{package}@{version}",
                    "source": src.name,
                    "sha256": hashlib.sha256((OUT / name).read_bytes()).hexdigest(),
                }
        licences.append(f"== {package} ==\n" + (base / "LICENSE").read_text())
    (OUT / "OFL.txt").write_text("\n\n".join(licences))
    (OUT / "FONTS.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    )
    print(f"wrote {len(manifest['files'])} fonts to {OUT}")


if __name__ == "__main__":
    shutil.os.umask(0o022)
    main()
