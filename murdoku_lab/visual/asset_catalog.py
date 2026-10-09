"""Local color artwork, selected by formal prop kind, never by themed label."""

import base64
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).parent / "assets" / "fluent"


@lru_cache(maxsize=1)
def catalog():
    return {
        entry["kind"]: entry
        for entry in json.loads((ROOT / "catalog.json").read_text())
    }


@lru_cache(maxsize=64)
def asset_uri(kind):
    entry = catalog().get(kind)
    if entry is None:
        return None
    path = ROOT / entry["path"]
    if path.parent != ROOT or path.suffix != ".svg":
        raise ValueError("invalid catalog asset path")
    return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode(
        "ascii"
    )


def prop_image(kind, width, height):
    uri = asset_uri(kind)
    if uri is None:
        return None
    # Frame exposes the complete formal footprint; preserve artwork aspect ratio.
    return (
        f'<rect x="1" y="1" width="{max(1,width-2)}" height="{max(1,height-2)}" '
        'rx="8" fill="#ffffff55" stroke="#536e5755"/>'
        f'<image width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" href="{uri}"/>'
    )


def search_assets(query="", *, category=None, formal_role=None, limit=8):
    """Search approved local assets; role compatibility is explicit and curated."""
    words = set(query.casefold().split())
    rows = []
    for entry in catalog().values():
        if category and entry["category"] != category:
            continue
        if formal_role and formal_role not in entry["formal_roles"]:
            continue
        terms = set(
            (
                entry["concept"]
                + " "
                + entry["kind"]
                + " "
                + entry["category"]
                + " "
                + " ".join(entry.get("aliases", []))
            )
            .casefold()
            .split()
        )
        score = len(words & terms)
        if words and not score:
            continue
        rows.append((score, entry))
    return [
        dict(entry)
        for _, entry in sorted(rows, key=lambda row: (-row[0], row[1]["kind"]))[
            : max(0, limit)
        ]
    ]


def validate_selection(case, selected):
    props = {p.pid: p for p in case.scene.props}
    for prop, asset in selected.items():
        if prop not in props:
            raise ValueError("asset selection contains unknown prop")
        if asset not in catalog():
            raise ValueError("unknown catalog asset: " + str(asset))
        role = "standable" if props[prop].standable else "blocking"
        if (
            prop not in catalog()[asset]["formal_roles"]
            and role not in catalog()[asset]["formal_roles"]
        ):
            raise ValueError("asset is incompatible with formal prop role: " + prop)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search licensed local color assets")
    parser.add_argument("--query", default="")
    parser.add_argument("--category")
    parser.add_argument("--role")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    print(
        json.dumps(
            search_assets(
                args.query,
                category=args.category,
                formal_role=args.role,
                limit=args.limit,
            ),
            indent=2,
        )
    )
