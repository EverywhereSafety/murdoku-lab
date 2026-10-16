"""Write the brand assets the web pages use: favicon, app icons and the mascot's poses.

    python scripts/build_brand_assets.py

Everything is drawn by murdoku_lab/visual/art/brand.py, so the icons always match the mascot
in the app and on the share cards. PNGs use the bundled fonts profile for repeatable output.
"""

from pathlib import Path

from murdoku_lab.visual.art import brand
from murdoku_lab.visual.raster import bundled_profile, png_from_svg

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "web" / "public"


def main():
    out = PUBLIC / "brand"
    out.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "favicon.svg").write_text(brand.icon_svg() + "\n")
    for size, name in ((180, "apple-touch-icon.png"), (512, "icon-512.png")):
        (out / name).write_bytes(
            png_from_svg(brand.icon_svg(size), profile=bundled_profile(fit_width=size))
        )
    for pose in brand.POSES:
        (out / f"mascot-{pose}.svg").write_text(brand.mascot_svg(pose, size=256) + "\n")
    (out / "mascot-mono.svg").write_text(
        brand.mascot_svg("idle", size=256, mono=True) + "\n"
    )
    print(f"wrote favicon.svg and {len(list(out.iterdir()))} files to {out}")


if __name__ == "__main__":
    main()
