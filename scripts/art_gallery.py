"""Render a local before/after gallery of the casebook art.

    python scripts/art_gallery.py --records outputs/showcase/*.jsonl --setting manor
    python scripts/art_gallery.py --showcase outputs/showcase/cases.jsonl
    open outputs/gallery/index.html

`--showcase` reads dressed records (scripts/build_showcase.py) and lays the gallery out by
setting: each setting's boards, its themed objects and its wallpapers.

Every image is a PNG rendered with the bundled fonts, so what you see is what exports produce.
Boards show a few people placed on arbitrary squares (never the solution) to show the tokens.
"""

import argparse
import html
import json
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.setter import settings
from murdoku_lab.visual import art, demos
from murdoku_lab.visual.art import brand, materials, portraits, props
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


def _showcase_observations(path):
    for line in Path(path).read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            case = Case.from_json(row["murdoku_case"])
            theme = Theme.from_json(row["murdoku_theme"])
            yield row["visual_case_id"], case, theme, theme.setting_id


def _theme_sheet(pack, img):
    """The setting's object key: every classic kind drawn as this setting draws it."""
    skins = pack["visual"].get("skins", {})
    items = list(settings.CLASSIC_KINDS)
    size, gap, cols = 104, 18, 10
    rows = (len(items) + cols - 1) // cols
    w, h = cols * (size + gap) + gap, rows * (size + 44) + gap
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><defs>{props.defs()}</defs>'
        f'<rect width="{w}" height="{h}" fill="#fbf7ee"/>'
    ]
    for i, kind in enumerate(items):
        x, y = gap + (i % cols) * (size + gap), gap + (i // cols) * (size + 44)
        noun = pack["objects"][kind]
        themed = kind in skins
        out.append(
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="10" fill="{"#e8d6b4" if themed else "#efe6d3"}"/>'
            f'<g transform="translate({x + 2} {y + 2})">{props.glyph(kind, 100, skin=skins.get(kind))}</g>'
            f'<text x="{x + size / 2}" y="{y + size + 16}" font-size="11.5" text-anchor="middle" font-family="DM Sans" '
            f'font-weight="{600 if themed else 400}" fill="#102725">{html.escape(noun)}</text>'
        )
    out.append("</svg>")
    return _png("".join(out), img / f"theme-{pack['id']}-objects.png")


def _wallpaper_strip(pack, img):
    papers = []
    for room in pack["rooms"]:
        if room.get("wallpaper") and room["wallpaper"] not in papers:
            papers.append(room["wallpaper"])
    w = 40 + 300 * len(papers) + 20
    defs = "".join(materials.wallpaper_pattern(p) for p in papers)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="80"><defs>{defs}</defs>'
        f'<rect width="{w}" height="80" fill="#fbf7ee"/>'
    ]
    for i, paper in enumerate(papers):
        x = 40 + 300 * i
        out.append(
            f'<rect x="{x}" y="40" width="280" height="26" fill="url(#{materials.wallpaper_id(paper)})"/>'
            f'<rect x="{x}" y="59" width="280" height="7" fill="#4a3022"/>'
            f'<path d="M{x} 40H{x + 280}" stroke="#2a221d" stroke-width="12"/><path d="M{x} 40H{x + 280}" stroke="#e7d6b6" stroke-width="6"/>'
            f'<text x="{x}" y="20" font-size="12" font-family="DM Mono" fill="#445c58">{html.escape(paper)}</text>'
        )
    out.append("</svg>")
    return _png("".join(out), img / f"theme-{pack['id']}-walls.png")


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
    parser.add_argument(
        "--showcase", help="dressed records from scripts/build_showcase.py"
    )
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

    def zoo_cell(item, x, y):
        kind, skin = item
        label = skin or kind
        return (
            f'<rect x="{x}" y="{y + 30}" width="120" height="120" rx="10" fill="#e8d6b4"/>'
            f'<g transform="translate({x + 10} {y + 40})">{props.draw(kind or "generic", 100, 100, skin=skin)}</g>'
            f'<text x="{x + 60}" y="{y + 164}" font-size="12" text-anchor="middle" font-family="DM Mono" fill="#102725">{html.escape(label)}</text>'
        )

    kinds = [(k, None) for k in props.BASE] + [(None, s) for s in props.all_skins()]
    zoo = _sheet(kinds, 10, 120, 50, zoo_cell).replace(
        "<rect width=", f"<defs>{props.defs()}</defs><rect width=", 1
    )
    sections.append(
        (
            f"物件图鉴：{len(props.BASE)} 种基础画法 + {len(props.all_skins())} 种主题换皮",
            [(_png(zoo, img / "props.png"), "每种物件独立画法；换皮让画面与叫法一致")],
        )
    )

    if args.showcase:
        _write_showcase(args.showcase, out, img, sections)
        return

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


STYLE = (
    "<style>body{font:15px/1.5 -apple-system,system-ui,sans-serif;background:#f4eedf;color:#102725;margin:0;padding:24px 28px}"
    "h1{font:600 28px Georgia,serif;margin:0 0 4px}h2{font:600 22px Georgia,serif;margin:40px 0 4px}"
    ".row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}figure{margin:0;background:#fbf7ee;border:1px solid #d9cfb9;border-radius:12px;padding:10px}"
    "figure img{display:block;max-width:100%;height:auto;border-radius:6px}figcaption{font-size:13px;color:#445c58;margin-top:6px}"
    ".boards figure{flex:1 1 300px;max-width:520px}.meta{color:#445c58;margin:0 0 10px}"
    "nav a{margin-right:14px;color:#0b7469}.theme{border-top:1px solid #d9cfb9;margin-top:28px}</style>"
)


def _write_showcase(path, out, img, sections):
    cases = list(_showcase_observations(path))
    order = []
    for _, _, theme, setting_id in cases:
        if setting_id not in order:
            order.append(setting_id)
    parts = [
        "<!doctype html><meta charset='utf-8'><title>Murdoku Lab · themes</title>",
        STYLE,
        "<h1>Murdoku Lab · 多场景主题（检查点 1b）</h1>",
        f"<p class='meta'>{len(order)} 套场景 × 3 个案件（6×6 易 / 7×7 中 / 8×8 中）· 每套场景有自己的房间名、物件叫法与画法、地板、墙纸和外框 · 题目数学不受主题影响</p>",
        "<nav>"
        + "".join(
            f"<a href='#{sid}'>{html.escape(settings.load(sid)['name'])}</a>"
            for sid in order
        )
        + "</nav>",
    ]
    for setting_id in order:
        pack = settings.load(setting_id)
        own = [c for c in cases if c[3] == setting_id]
        parts.append(
            f"<section class='theme' id='{setting_id}'><h2>{html.escape(pack['name'])}</h2>"
            f"<p class='meta'>{html.escape(pack.get('eyebrow', ''))}</p><div class='row boards'>"
        )
        for slug, case, theme, _ in own:
            obs = _with_tokens(case, theme)
            name = _png(art.scene_svg(obs, style="casebook"), img / f"{slug}-day.png")
            caption = f"{theme.title} · {case.scene.W}×{case.scene.H} · {case.scene.n_areas} 个房间"
            parts.append(
                f"<figure><img src='img/{name}' loading='lazy'><figcaption><b>{html.escape(caption)}</b><br>{html.escape(theme.blurb)}</figcaption></figure>"
            )
        slug, case, theme, _ = own[0]
        night = _png(
            art.scene_svg(_with_tokens(case, theme), style="casebook", theme="night"),
            img / f"{slug}-night.png",
        )
        parts.append(
            f"<figure><img src='img/{night}' loading='lazy'><figcaption>夜间模式 · {html.escape(theme.title)}</figcaption></figure></div>"
        )
        objects = _theme_sheet(pack, img)
        walls = _wallpaper_strip(pack, img)
        parts.append(
            "<div class='row' style='margin-top:14px'>"
            f"<figure><img src='img/{objects}' loading='lazy'><figcaption>本场景的 20 种物件叫法与画法（加粗 = 主题换皮）</figcaption></figure>"
            f"<figure><img src='img/{walls}' loading='lazy'><figcaption>墙纸</figcaption></figure></div></section>"
        )
    slug, case, theme, _ = cases[0]
    page = _png(
        art.observation_svg(_with_tokens(case, theme), style="casebook"),
        img / "showcase-page.png",
    )
    parts.append(
        f"<section class='theme'><h2>完整案卷页（RL 视觉导出 full scope）</h2><div class='row'><figure><img src='img/{page}' loading='lazy'><figcaption>{html.escape(slug)}</figcaption></figure></div></section>"
    )
    for title, images in sections:
        parts.append(
            f"<section class='theme'><h2>{html.escape(title)}</h2><div class='row'>"
        )
        for name, caption in images:
            parts.append(
                f"<figure><img src='img/{name}' loading='lazy'><figcaption>{html.escape(caption)}</figcaption></figure>"
            )
        parts.append("</div></section>")
    (out / "themes.html").write_text("".join(parts))
    print(
        f"wrote {out / 'themes.html'} with {len(cases)} boards in {len(order)} settings"
    )


if __name__ == "__main__":
    main()
