"""Build the standalone casebook for GitHub Pages or any static host."""

import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from murdoku_lab.visual.browser import BrowserGame
from murdoku_lab.visual.art import portrait_svg, prop_svg
from murdoku_lab.visual.projection import ART_KINDS


def main():
    game = BrowserGame()
    for entry in game.cases.values():
        state = game.request("/api/sessions", {"case_id": entry.slug})["result"]
        game.request(f"/api/sessions/{state['session_id']}/scene.svg")
    subprocess.run(
        ["npm", "run", "build"],
        cwd=ROOT,
        env={**os.environ, "VITE_STATIC_PLAY": "true"},
        check=True,
    )
    output = ROOT / "dist"
    with ZipFile(output / "browser-engine.zip", "w", ZIP_DEFLATED) as archive:
        for name, module in list(sys.modules.items()):
            if name.startswith("murdoku_lab") and getattr(module, "__file__", None):
                path = Path(module.__file__)
                archive.write(path, path.relative_to(ROOT))
        for path in (ROOT / "murdoku_lab/visual/cases").glob("*.json"):
            archive.write(path, path.relative_to(ROOT))
        archive.write(ROOT / "LICENSE", "LICENSE")
        archive.write(ROOT / "NOTICE", "NOTICE")
    for kind, values, render in (
        (
            "portrait",
            range(max(len(e.case.characters) for e in game.cases.values())),
            portrait_svg,
        ),
        ("prop", sorted(ART_KINDS | {"generic"}), prop_svg),
    ):
        directory = output / "art" / kind
        directory.mkdir(parents=True, exist_ok=True)
        for value in values:
            (directory / f"{value}.svg").write_text(render(value))
    print(f"Static casebook: {output}")


if __name__ == "__main__":
    main()
