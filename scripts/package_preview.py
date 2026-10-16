"""Package the player for testers: a zip they unpack and start with a double click.

    python scripts/package_preview.py               # → outputs/preview/murdoku-preview-<date>.zip
    python scripts/package_preview.py --no-build    # package the last build

The zip holds the static player (no Lab, no Python packages needed), launchers for macOS and
Windows that serve it on http://127.0.0.1:4173/ with the Python that ships with most computers
and open the browser, and a short guide for testers (scripts/preview/). Nothing is uploaded
anywhere: the zip is a local file to hand round.
"""

import argparse
import datetime as dt
import importlib.util
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
KIT = Path(__file__).resolve().parent / "preview"
PORT = 4173
# The research Lab and the art preview need the Python server; testers get the game only.
LEFT_OUT = ("lab", "art-preview", "review")


def build():
    spec = importlib.util.spec_from_file_location(
        "release_local", ROOT / "scripts" / "release_local.py"
    )
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    release.build(f"http://127.0.0.1:{PORT}/")


def stage(folder):
    site = folder / "site"
    shutil.copytree(
        DIST,
        site,
        ignore=lambda directory, names: [
            n
            for n in names
            if (Path(directory) == DIST and n in LEFT_OUT)
            or (Path(directory).name == "assets" and n.startswith("lab-"))
        ],
    )
    (site / "lab").mkdir()
    shutil.copy(KIT / "lab.html", site / "lab" / "index.html")
    for name in (
        "Start Murdoku (Mac).command",
        "Start Murdoku (Windows).bat",
        "试玩说明.txt",
    ):
        shutil.copy(KIT / name, folder / name)
    (folder / "Start Murdoku (Mac).command").chmod(0o755)


def pack(folder, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(folder.rglob("*")):
            info = zipfile.ZipInfo.from_file(
                path, Path(folder.name) / path.relative_to(folder)
            )
            if path.is_dir():
                archive.writestr(info, "")
                continue
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--out", default=str(ROOT / "outputs" / "preview"))
    args = parser.parse_args()
    if not args.no_build:
        build()
    out = Path(args.out)
    name = f"murdoku-preview-{dt.date.today():%Y%m%d}"
    folder = out / "Murdoku Preview"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    stage(folder)
    target = out / f"{name}.zip"
    pack(folder, target)
    files = sum(1 for p in folder.rglob("*") if p.is_file())
    print(f"\n{target}  ({target.stat().st_size / 1e6:.1f} MB, {files} files)")


if __name__ == "__main__":
    main()
