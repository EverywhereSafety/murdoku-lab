"""Build the standalone casebook for GitHub Pages or any static host."""

import os
import gzip
from pathlib import Path
import subprocess
import sys
import shutil
import tarfile
from urllib.request import urlopen
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from murdoku_lab.visual.browser import BrowserGame
from murdoku_lab.visual.art import portrait_svg, prop_svg
from murdoku_lab.visual.projection import ART_KINDS

PYODIDE_VERSION = "314.0.7"


def bundle_runtime(output):
    cache = Path.home() / ".cache/murdoku-lab/pyodide" / PYODIDE_VERSION
    cache.mkdir(parents=True, exist_ok=True)
    runtime_files = (
        "pyodide.mjs",
        "pyodide.asm.mjs",
        "pyodide.asm.wasm",
        "python_stdlib.zip",
        "pyodide-lock.json",
    )
    if any(not (cache / name).exists() for name in runtime_files):
        print("Downloading Pyodide browser runtime", flush=True)
        archive_path = cache / "runtime.tgz"
        with (
            urlopen(
                f"https://registry.npmjs.org/pyodide/-/pyodide-{PYODIDE_VERSION}.tgz",
                timeout=60,
            ) as response,
            archive_path.open("wb") as stream,
        ):
            shutil.copyfileobj(response, stream)
        with tarfile.open(archive_path, "r:gz") as archive:
            for name in runtime_files:
                temporary = cache / (name + ".download")
                with (
                    archive.extractfile("package/" + name) as source,
                    temporary.open("wb") as stream,
                ):
                    shutil.copyfileobj(source, stream)
                temporary.replace(cache / name)
    sources = {}
    sources["LICENSE-Pyodide.txt"] = (
        f"https://raw.githubusercontent.com/pyodide/pyodide/{PYODIDE_VERSION}/LICENSE"
    )
    sources["LICENSE-Python.txt"] = (
        "https://raw.githubusercontent.com/python/cpython/v3.14.0/LICENSE"
    )
    target = output / "python"
    target.mkdir()
    for name in runtime_files:
        shutil.copy2(cache / name, target / name)
    for name in ("pyodide.asm.wasm", "pyodide.asm.mjs"):
        (target / (name + ".gz")).write_bytes(
            gzip.compress((cache / name).read_bytes(), compresslevel=9, mtime=0)
        )
    for name, url in sources.items():
        cached = cache / name
        if not cached.exists():
            print(f"Downloading browser runtime: {name}", flush=True)
            temporary = cache / (name + ".download")
            with urlopen(url, timeout=60) as response, temporary.open("wb") as stream:
                shutil.copyfileobj(response, stream)
            temporary.replace(cached)
        shutil.copy2(cached, target / name)
    (target / "NOTICE.txt").write_text(
        "Pyodide " + PYODIDE_VERSION + " (Mozilla Public License 2.0)\n"
        "Source: https://github.com/pyodide/pyodide/tree/" + PYODIDE_VERSION + "\n"
        "CPython 3.14: https://github.com/python/cpython/tree/v3.14.0\n"
        "Unmodified browser runtime distributed by the Pyodide project.\n"
    )


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
    bundle_runtime(output)
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
