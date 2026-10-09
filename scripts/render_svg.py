"""Write a public SVG without a browser or a model call."""

import argparse
from pathlib import Path
import sys

from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.visual.art import scene_svg, observation_svg
from murdoku_lab.visual.demos import catalogue
from murdoku_lab.visual.projection import public_observation


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", default="glasshouse")
    p.add_argument("--records")
    p.add_argument("--scope", choices=("full", "scene"), default="full")
    p.add_argument("--style", choices=("art", "diagram"), default="art")
    p.add_argument("--out", default="artifacts/observation.svg")
    a = p.parse_args()
    e = catalogue(a.records)[a.case]
    state = public_observation(
        Scratchpad(e.case, e.theme),
        case_id=e.slug,
        setting=e.setting,
        eyebrow=e.eyebrow,
    )
    svg = (scene_svg if a.scope == "scene" else observation_svg)(state, style=a.style)
    output = Path(a.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg)
    print(output.resolve())


if __name__ == "__main__":
    main()
