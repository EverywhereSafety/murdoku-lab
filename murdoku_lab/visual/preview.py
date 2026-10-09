"""Build a public preview of paired queries without copying private case records."""

import argparse
from html import escape
import json
from pathlib import Path
import shutil

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "web/public/review")
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    text_rows = [
        json.loads(line)
        for line in (bundle / "public/text.jsonl").read_text().splitlines()
        if line
    ]
    vision_rows = [
        json.loads(line)
        for line in (bundle / "public/vision.jsonl").read_text().splitlines()
        if line
    ]
    manifest = json.loads((bundle / "manifest.json").read_text())
    if (bundle / "index.json").exists():
        index = json.loads((bundle / "index.json").read_text())
    else:
        private = [
            json.loads(line)
            for line in (bundle / "text.rl.jsonl").read_text().splitlines()
            if line
        ]
        index = []
        for i, (record, vision_row) in enumerate(zip(private, vision_rows), 1):
            case = record["murdoku_case"]
            scene = case["scene"]
            index.append(
                {
                    "index": i,
                    "case_id": record["paired_case_id"],
                    "visual_case_id": record["visual_case_id"],
                    "size": scene["W"],
                    "areas": len(set(scene["area_of"])),
                    "band": record["query_validation"]["band"],
                    "title": record["murdoku_theme"]["title"],
                    "image": vision_row["image_assets"][0]["path"],
                }
            )
    assert len(index) == len(text_rows) == len(vision_rows)
    cards = []
    for info, text_row, vision_row in zip(index, text_rows, vision_rows):
        assert (
            text_row["paired_case_id"]
            == vision_row["paired_case_id"]
            == info["case_id"]
        )
        image = vision_row["image_assets"][0]["path"]
        shutil.copy2(bundle / image, out / image)
        vision_text = vision_row["messages"][1]["content"][0]["text"]
        clues = vision_text.split("\nCLUES\n", 1)[1].split("\nTERMS\n", 1)[0].strip()
        case_id = info["visual_case_id"]
        cards.append(
            f"""<details class="case" data-size="{info['size']}" {'open' if info['index']==1 else ''}>
        <summary><span class="number">{info['index']:02d}</span> {info['size']}×{info['size']} · {escape(info['band'])} · {info['areas']} areas</summary>
        <div class="case-layout"><div><a href="{image}" target="_blank" rel="noreferrer"><img src="{image}" alt="Case {info['index']} board and visual legend" loading="lazy"></a><p class="muted">Open the full-resolution board and legends.</p></div>
        <div><h3>{escape(info['title'])}</h3><p><a class="play" href="../?case={case_id}">Play →</a></p><pre class="clues">{escape(clues)}</pre>
        <details><summary>Visual query text</summary><pre>{escape(vision_text)}</pre></details></div></div>
        <details class="text-query"><summary>Text query</summary><pre>{escape(text_row['messages'][1]['content'])}</pre></details></details>"""
        )
    if not index:
        raise ValueError("query bundle has no accepted cases")
    size_counts = {
        size: sum(row["size"] == size for row in index)
        for size in sorted({r["size"] for r in index})
    }
    buttons = '<button data-size-filter="all">All</button>' + "".join(
        f'<button data-size-filter="{n}">{n}×{n} · {k}</button>'
        for n, k in size_counts.items()
    )
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="../favicon.svg"><title>Murdoku · Paired query review</title>
    <style>*{{box-sizing:border-box}}body{{margin:0;background:#f6f5ed;color:#304b3c;font:15px/1.8 system-ui,sans-serif}}main{{max-width:1300px;margin:auto;padding:28px 32px 60px}}nav{{display:flex;gap:24px;flex-wrap:wrap}}a{{color:#476e49;text-underline-offset:4px}}h1{{font:clamp(34px,5vw,51px)/1.15 Georgia,serif;margin:36px 0 18px}}h2{{font-size:22px}}h3{{font-size:19px;margin:0 0 14px}}.intro{{max-width:980px}}.eyebrow{{font-size:11px;letter-spacing:2px;color:#738166}}.muted{{font-size:12px;color:#73816d}}.case{{background:#fffef8;border:1px solid #d9e1d0;border-radius:13px;margin:17px 0;padding:20px}}summary{{font-weight:650;cursor:pointer}}.number{{display:inline-block;padding:0 12px 0 0;color:#9a7750}}.case-layout{{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(280px,1fr);gap:28px;margin-top:24px;align-items:start}}img{{width:100%;display:block;border:1px solid #e0e5d7;border-radius:8px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.75 ui-monospace,SFMono-Regular,Consolas,monospace;background:#eef3e5;padding:18px;border-radius:8px}}pre.clues{{font:14px/1.9 system-ui,sans-serif;background:transparent;padding:0;white-space:pre-wrap}}.text-query pre{{white-space:pre;overflow-x:auto;overflow-wrap:normal}}.play,button{{display:inline-block;padding:8px 13px;border:1px solid #bacdaf;border-radius:8px;background:#edf2e5;color:#3f623e;text-decoration:none}}button{{margin:0 8px 8px 0;cursor:pointer;font:inherit;font-size:13px}}button.active{{background:#4d7048;color:white}}.facts{{display:flex;gap:24px;flex-wrap:wrap;padding:16px 20px;border:1px solid #d9e1ce;background:#edf2e5;border-radius:10px;margin:22px 0}}.facts b{{font-size:24px}}[hidden]{{display:none}}details details{{margin-top:16px}}@media(max-width:800px){{main{{padding:22px 16px}}.case-layout{{grid-template-columns:1fr}}.case{{padding:16px}}}}
    </style></head><body><main><nav><a href="../">← Casebook</a></nav>
    <p class="eyebrow">ONE GENERATOR · TWO QUERY VIEWS</p><h1>The same puzzle. Two ways in.</h1>
    <div class="intro"><p>Each puzzle has a text query and a <strong>board image + clues</strong> query. Both views share the same case, tools and gold grader.</p>
    <p>Use <code>murdoku(action="board")</code> to request the current image, and coordinate-based tools to place or mark characters.</p></div>
    <div class="facts"><span><b>{len(index)}</b> puzzles</span><span><b>{len(index)*2}</b> paired queries</span><span><b>{min(size_counts)}–{max(size_counts)}</b> board sizes</span><span>Difficulty from deduction certificates</span></div>
    <p>{buttons}</p>{''.join(cards)}
    <p class="muted">Paired views share a case identity. Split datasets by paired_case_id.</p>
    </main><script>document.querySelectorAll('[data-size-filter]').forEach(b=>b.addEventListener('click',()=>{{document.querySelectorAll('.case').forEach(c=>c.hidden=b.dataset.sizeFilter!=='all'&&c.dataset.size!==b.dataset.sizeFilter);document.querySelectorAll('[data-size-filter]').forEach(x=>x.classList.toggle('active',x===b));const first=[...document.querySelectorAll('.case')].find(c=>!c.hidden);if(first)first.open=true;}}));</script></body></html>"""
    (out / "index.html").write_text(html)
    (out / "paired-review.json").write_text(
        json.dumps(
            {"cases": len(index), "sizes": size_counts, "public_only": True}, indent=2
        )
        + "\n"
    )
    print(json.dumps({"cases": len(index), "directory": str(out)}))


if __name__ == "__main__":
    main()
