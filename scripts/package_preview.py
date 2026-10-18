"""Package the player for testers: a zip to hand round, or a folder for a static web host.

    python scripts/package_preview.py               # → outputs/preview/murdoku-preview-<date>.zip
    python scripts/package_preview.py --no-build    # package the last build
    python scripts/package_preview.py --site https://example.org/murdoku-preview/
                                                    # → outputs/site/murdoku-preview/

The zip holds the static player (no Lab, no Python packages needed), launchers for macOS and
Windows that serve it on http://127.0.0.1:4173/ with the Python that ships with most computers
and open the browser, and a short guide for testers (scripts/preview/).

`--site` builds for a public address instead: share links and preview images point there, every
page carries `noindex`, and `lab/` links to the live research Lab (`--lab`, by default
https://everywheresafety.github.io/murdoku/play/lab/). Copy the folder to that path of the host; adding it changes
no other page there. Nothing is uploaded by this script.
"""

import argparse
import datetime as dt
import html
import importlib.util
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
KIT = Path(__file__).resolve().parent / "preview"
PORT = 4173
# The research Lab and the art preview need the Python server; testers get the game only.
LEFT_OUT = ("lab", "art-preview", "review")


def build(site_url=f"http://127.0.0.1:{PORT}/"):
    spec = importlib.util.spec_from_file_location(
        "release_local", ROOT / "scripts" / "release_local.py"
    )
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    release.build(site_url)


def copy_player(site):
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


NOINDEX = '<meta name="robots" content="noindex">'


def site_folder(url, lab):
    """The player for a public address, ready to copy to that path of a static host."""
    folder = ROOT / "outputs" / "site" / urlparse(url).path.strip("/")
    if folder.exists():
        shutil.rmtree(folder)
    folder.parent.mkdir(parents=True, exist_ok=True)
    copy_player(folder)
    page = (KIT / "lab-live.html").read_text().replace("{LAB}", html.escape(lab))
    (folder / "lab" / "index.html").write_text(page)
    for path in folder.rglob("*.html"):
        text = path.read_text()
        if NOINDEX not in text:
            path.write_text(text.replace("<head>", "<head>" + NOINDEX, 1))
    return folder


def stage(folder):
    site = folder / "site"
    copy_player(site)
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
    parser.add_argument("--site", help="public address the folder will be served from")
    parser.add_argument(
        "--lab",
        default="https://everywheresafety.github.io/murdoku/play/lab/",
        help="where lab/ sends people",
    )
    args = parser.parse_args()
    if args.site:
        url = args.site if args.site.endswith("/") else args.site + "/"
        if not args.no_build:
            build(url)
        folder = site_folder(url, args.lab)
        files = sum(1 for p in folder.rglob("*") if p.is_file())
        print(f"\n{folder}  ({files} files) → serve it at {url}")
        return
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
