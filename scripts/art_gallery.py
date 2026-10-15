"""Render a local before/after gallery of the casebook art.

    python scripts/art_gallery.py --records outputs/showcase/*.jsonl --setting manor
    open outputs/gallery/index.html

Every image is a PNG rendered with the bundled fonts, so what you see is what exports produce.
Boards show a few people placed on arbitrary squares (never the solution) to show the tokens.
"""

import argparse
import html
import json
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.setter import settings
from murdoku_lab.visual import art, demos
from murdoku_lab.visual.art import brand, portraits, props
from murdoku_lab.visual.projection import public_observation
from murdoku_lab.visual.raster import bundled_profile, png_from_svg

ROOT = Path(__file__).resolve().parents[1]


def _demo_observations():
    for entry in demos.catalogue().values():
        yield entry.slug, entry.case, entry.theme, entry.setting


def _record_observations(paths, setting):
    for path in paths:
        rows = [
            json.loads(line)
            for line in Path(path).read_text().splitlines()
            if line.strip()
        ]
        for i, row in enumerate(rows):
            case = Case.from_json(row.get("murdoku_case", row.get("case", row)))
            theme = settings.dress(case, setting)
            slug = f"{Path(path).stem}-{i + 1}"
            yield slug, case, theme, settings.load(setting)["name"]


def _with_tokens(case, theme):
    """A board state with up to three people on arbitrary, non-solution squares."""
    pad = Scratchpad(case, theme)
    obs = public_observation(pad)
    solution = {p: case.scene.rc(k) for p, k in case.solution.items()}
    used_rows, used_cols = set(), set()
    placed = 0
    for person in obs["people"]:
        if placed == 3:
            break
        for cell in obs["scene"]["cells"]:
            rc = (cell["row"], cell["col"])
            if (
                cell["standable"]
                and cell["row"] not in used_rows
                and cell["col"] not in used_cols
                and rc != solution.get(person["id"])
            ):
                obs["placements"][person["id"]] = cell["cell"]
                used_rows.add(cell["row"])
                used_cols.add(cell["col"])
                placed += 1
                break
    return obs


def _png(svg, path, *, legacy=False, fit=None):
    profile = None if legacy else bundled_profile(fit)
    path.write_bytes(png_from_svg(svg, profile=profile))
    return path.name


def _sheet(cells, cols, size, gap, body):
    rows = (len(cells) + cols - 1) // cols
    w, h = cols * (size + gap) + gap, rows * (size + gap) + gap
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="#fbf7ee"/>'
    ]
    out.append(
        '<defs><clipPath id="g-clip"><circle cx="50" cy="50" r="48"/></clipPath></defs>'
    )
    for i, cell in enumerate(cells):
        x, y = gap + (i % cols) * (size + gap), gap + (i // cols) * (size + gap)
        out.append(body(cell, x, y))
    out.append("</svg>")
    return "".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="*", default=[])
    parser.add_argument("--setting", default="manor")
    parser.add_argument("--out", default=str(ROOT / "outputs" / "gallery"))
    args = parser.parse_args()
    out = Path(args.out)
    img = out / "img"
    img.mkdir(parents=True, exist_ok=True)

    sections = []

    # Mascot
    poses = brand.POSES
    mascot = _sheet(
        list(poses),
        len(poses),
        220,
        20,
        lambda p, x, y: f'<g transform="translate({x} {y}) scale({220 / 128})">{brand.donut_detective(p)}</g>',
    )
    sections.append(
        (
            "吉祥物：甜甜圈侦探（ES 原标识 + 猎鹿帽）",
            [
                (
                    _png(mascot, img / "mascot.png"),
                    "idle · thinking · pointing · celebrating",
                )
            ],
        )
    )

    # Portraits
    looks = portraits.roster()
    faces = _sheet(
        list(range(len(looks))),
        16,
        78,
        8,
        lambda i, x, y: f'<g transform="translate({x} {y}) scale(.78)"><g clip-path="url(#g-clip)">{portraits.look_inner(looks[i])}</g></g>',
    )
    victims = _sheet(
        list(range(0, 64, 8)),
        8,
        110,
        12,
        lambda i, x, y: f'<g transform="translate({x} {y}) scale(1.1)"><g clip-path="url(#g-clip)">{portraits.look_inner(looks[i], "victim")}</g></g>',
    )
    sections.append(
        (
            "头像名册（128 个固定造型，同名同脸）",
            [
                (_png(faces, img / "portraits.png"), "中性 64 · 女性 32 · 男性 32"),
                (_png(victims, img / "victims.png"), "受害者造型：去饱和 + 闭眼"),
            ],
        )
    )

    # Prop zoo
    kinds = [(k, None) for k in props.BASE] + [(None, s) for s in props.SKINS]

    def zoo_cell(item, x, y):
        kind, skin = item
        label = skin or kind
        return (
            f'<rect x="{x}" y="{y + 30}" width="120" height="120" rx="10" fill="#e8d6b4"/>'
            f'<g transform="translate({x + 10} {y + 40})">{props.draw(kind or "generic", 100, 100, skin=skin)}</g>'
            f'<text x="{x + 60}" y="{y + 164}" font-size="12" text-anchor="middle" font-family="DM Mono" fill="#102725">{html.escape(label)}</text>'
        )

    zoo = _sheet(kinds, 8, 120, 50, zoo_cell).replace(
        "<rect width=", f"<defs>{props.defs()}</defs><rect width=", 1
    )
    sections.append(
        (
            "物件图鉴：26 种基础画法 + 庄园换皮",
            [(_png(zoo, img / "props.png"), "每种物件独立画法；换皮让画面与叫法一致")],
        )
    )

    # Boards
    boards = []
    cases = list(_demo_observations()) + list(
        _record_observations(args.records, args.setting)
    )
    for slug, case, theme, setting_name in cases:
        obs = _with_tokens(case, theme)
        before = _png(
            art.scene_svg(obs, style="art"), img / f"{slug}-before.png", legacy=True
        )
        day = _png(art.scene_svg(obs, style="casebook"), img / f"{slug}-day.png")
        night = _png(
            art.scene_svg(obs, style="casebook", theme="night"),
            img / f"{slug}-night.png",
        )
        exported = _png(
            art.board_svg(obs, style="casebook"), img / f"{slug}-export.png"
        )
        meta = f"{theme.title} · {setting_name} · {case.scene.W}×{case.scene.H} · {len(case.characters)} 人 · {case.scene.n_areas} 个房间"
        boards.append(
            (
                slug,
                meta,
                [
                    (before, "改版前（legacy art）"),
                    (day, "casebook 日间"),
                    (night, "casebook 夜间"),
                    (exported, "RL 视觉导出（带图例）"),
                ],
            )
        )

    # One full case file page
    slug, case, theme, _ = cases[0]
    page = _png(
        art.observation_svg(_with_tokens(case, theme), style="casebook"),
        img / "page.png",
    )

    parts = [
        "<!doctype html><meta charset='utf-8'><title>Murdoku Lab · casebook gallery</title>",
        "<style>body{font:15px/1.5 -apple-system,system-ui,sans-serif;background:#f4eedf;color:#102725;margin:0;padding:24px 28px}"
        "h1{font:600 28px Georgia,serif;margin:0 0 4px}h2{font:600 20px Georgia,serif;margin:36px 0 10px}"
        ".row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}figure{margin:0;background:#fbf7ee;border:1px solid #d9cfb9;border-radius:12px;padding:10px}"
        "figure img{display:block;max-width:100%;height:auto;border-radius:6px}figcaption{font-size:13px;color:#445c58;margin-top:6px}"
        ".boards figure{flex:1 1 300px;max-width:520px}.meta{color:#445c58;margin:0 0 8px}</style>",
        "<h1>Murdoku Lab · 新美术画廊（检查点 1a）</h1><p class='meta'>温馨悬疑案卷 casebook 画风 · 庄园主题 · 蜗牛侦探草案 · 所有图片由导出管线用打包字体渲染</p>",
    ]
    for title, images in sections:
        parts.append(f"<h2>{html.escape(title)}</h2><div class='row'>")
        for name, caption in images:
            parts.append(
                f"<figure><img src='img/{name}'><figcaption>{html.escape(caption)}</figcaption></figure>"
            )
        parts.append("</div>")
    parts.append("<h2>棋盘：改版前 → 改版后</h2>")
    for slug, meta, images in boards:
        parts.append(
            f"<h3 style='margin:22px 0 6px;font-size:16px'>{html.escape(slug)}</h3><p class='meta'>{html.escape(meta)}</p><div class='row boards'>"
        )
        for name, caption in images:
            parts.append(
                f"<figure><img src='img/{name}' loading='lazy'><figcaption>{html.escape(caption)}</figcaption></figure>"
            )
        parts.append("</div>")
    parts.append(
        f"<h2>完整案卷页（RL 视觉导出 full scope）</h2><div class='row'><figure><img src='img/{page}' loading='lazy'><figcaption>{html.escape(cases[0][0])}</figcaption></figure></div>"
    )
    (out / "index.html").write_text("".join(parts))
    print(f"wrote {out / 'index.html'} with {len(boards)} boards")


if __name__ == "__main__":
    main()
