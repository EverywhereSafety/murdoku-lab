"""Author themes concurrently with a local model; never read official evaluation."""

import argparse, concurrent.futures, json, os, sys
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.render import render_case
from murdoku_lab.setter.llm_setter import llm_theme
from murdoku_lab.setter.llm_client import LLMClient
from murdoku_lab.setter.theme_quality import neutralize_setup, quality_issues


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--endpoint", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--api-key-var", default="MURDOKU_LOCAL_API_KEY")
    p.add_argument(
        "--styles-file",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "murdoku_lab/resources/theme_styles.txt",
    )
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--workers", type=int, default=1)
    a = p.parse_args()
    if a.workers < 1:
        raise ValueError("positive worker count required")
    styles = [
        s.strip()
        for s in a.styles_file.read_text().splitlines()
        if s.strip() and not s.startswith("#")
    ]
    assert styles, "empty theme style catalog"
    a.out.mkdir(parents=True, exist_ok=True)
    cfg = {
        "base_url": a.endpoint,
        "api_key_var": a.api_key_var,
        "models": {"default": a.model, "setter": a.model},
        "timeout_s": 120,
        "max_retries": 2,
    }
    os.environ.setdefault(a.api_key_var, "local-placeholder")
    records = [json.loads(l) for l in a.input.read_text().splitlines()]
    assert len({r["prompt_uid"] for r in records}) == len(
        records
    ), "duplicate structural inputs"
    good = {}
    failed = []
    usage = {}

    def generate(index, record):
        case = Case.from_json(record["murdoku_case"])
        style = styles[index % len(styles)]
        client = LLMClient(role="setter", cfg=cfg)
        errors = []
        try:
            for round_no in range(3):
                prompt_style = (
                    style
                    + ". Use clear short English display labels and exact prop IDs as keys. "
                    + ("Fix: " + errors[-1] if errors else "")
                )
                try:
                    result = llm_theme(
                        case,
                        style=prompt_style,
                        client=client,
                        attempts=3,
                        require_complete_props=True,
                    )
                    theme = neutralize_setup(result.theme)
                    issues = quality_issues(case, theme)
                    if issues:
                        raise ValueError("; ".join(issues))
                    record["murdoku_theme"] = theme.to_json()
                    record["messages"][1]["content"] = render_case(
                        case, theme, scene_format="compact"
                    )
                    record["augmentation"] = {
                        "source": "local_llm",
                        "model": a.model,
                        "style": style,
                        "attempts": result.attempts,
                        "generation_rounds": round_no + 1,
                        "structural_hash": case.content_hash(),
                    }
                    return record, None, client.usage.to_json()
                except Exception as exc:
                    errors.append(f"{type(exc).__name__}: {exc}")
            return (
                None,
                {"case_id": case.content_hash(), "errors": errors},
                client.usage.to_json(),
            )
        except Exception as exc:
            return (
                None,
                {
                    "case_id": case.content_hash(),
                    "errors": errors + [f"{type(exc).__name__}: {exc}"],
                },
                client.usage.to_json(),
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = {pool.submit(generate, i, r): i for i, r in enumerate(records)}
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            record, error, record_usage = future.result()
            for k, v in record_usage.items():
                usage[k] = usage.get(k, 0) + v
            if record is not None:
                good[i] = record
            else:
                failed.append(error)
            dest = a.out / "train.themed.rl.jsonl"
            tmp = dest.with_suffix(".tmp")
            tmp.write_text(
                "".join(
                    json.dumps(good[k], ensure_ascii=False) + "\n" for k in sorted(good)
                )
            )
            tmp.replace(dest)
            manifest = {
                "expected": len(records),
                "accepted": len(good),
                "failed": failed,
                "usage": usage,
                "workers": a.workers,
                "model": a.model,
                "styles": len(styles),
                "input": str(a.input),
                "official_data_access": False,
                "qualification": "generated and programmatically gated; independent review still required",
                "semantic_scope": "original formal clues rendered with schema-validated themes; no free clue paraphrase",
            }
            (a.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
            print(
                json.dumps(
                    {
                        "case_id": records[i]["prompt_uid"],
                        "status": "THEME_ACCEPTED" if record else "GENERATION_FAILED",
                        "accepted": len(good),
                        "failed": len(failed),
                    }
                ),
                flush=True,
            )
    assert good, "no LLM-authored themes accepted"
    print("THEME_GENERATION_FINISHED", flush=True)


if __name__ == "__main__":
    main()
