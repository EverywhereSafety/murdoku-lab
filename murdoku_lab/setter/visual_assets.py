"""Configurable LLM retrieval over a licensed local artwork catalog."""

import json
from pathlib import Path
from dataclasses import replace
from murdoku_lab.visual.asset_catalog import search_assets, validate_selection

from murdoku_lab.paths import DEFAULTS

DEFAULT_CONFIG = DEFAULTS / "visual_assets.json"


def select_assets(case, theme, *, client, config=None):
    cfg = json.loads(DEFAULT_CONFIG.read_text()) if config is None else dict(config)
    if not cfg.get("enabled"):
        return theme
    if cfg.get("pack") != "fluent-color" or cfg.get("compatibility") not in (
        "explicit_formal_roles",
        "prop_classes",
    ):
        raise ValueError("unsupported artwork pack or compatibility policy")
    if cfg.get("online_search"):
        raise ValueError("online downloads are separate from setter selection")
    choices = {
        p.pid: search_assets(
            formal_role=(
                ("standable" if p.standable else "blocking")
                if cfg.get("compatibility") == "prop_classes"
                else p.pid
            ),
            limit=cfg.get("search_limit", 8),
        )
        for p in case.scene.props
    }
    missing = [kind for kind, rows in choices.items() if not rows]
    if missing and not cfg.get("allow_missing", True):
        raise ValueError("missing compatible assets: " + ", ".join(missing))
    available = {kind: rows for kind, rows in choices.items() if rows}
    if not available:
        return theme
    if cfg.get("selection") == "deterministic":
        selected = {kind: rows[0]["kind"] for kind, rows in available.items()}
    elif cfg.get("selection") == "llm":
        from murdoku_lab.setter.llm_setter import _extract_json

        prompt = {
            "title": theme.title,
            "rooms": list(theme.areas),
            "objects": theme.objects,
            "candidates": {
                kind: [
                    {
                        "asset_id": e["kind"],
                        "concept": e["concept"],
                        "category": e["category"],
                    }
                    for e in rows
                ]
                for kind, rows in available.items()
            },
        }
        reply = client.chat(
            [
                {
                    "role": "system",
                    "content": 'Select artwork from the provided library candidates. Return JSON {"assets": {"prop_id": "asset_id"}}. Select one listed candidate for every supplied prop. All selected asset IDs must be distinct across prop IDs. Never invent IDs, change locations or use outside assets. This is presentation only.',
                },
                {"role": "user", "content": json.dumps(prompt)},
            ],
            temperature=0.3,
        )
        selected = _extract_json(reply).get("assets")
        if not isinstance(selected, dict) or set(selected) != set(available):
            raise ValueError("asset selection must cover exactly the searchable props")
        for kind, asset in selected.items():
            if asset not in {e["kind"] for e in available[kind]}:
                raise ValueError("asset was not offered to the setter")
    else:
        raise ValueError("selection must be llm or deterministic")
    # Preserve the model's preferences while filling conflicts from its offered candidates.
    used = set()
    for kind in sorted(available, key=lambda key: len(available[key])):
        candidates = [selected[kind]] + [
            e["kind"] for e in available[kind] if e["kind"] != selected[kind]
        ]
        choice = next((asset for asset in candidates if asset not in used), None)
        if choice is None:
            raise ValueError("insufficient distinct compatible assets")
        selected[kind] = choice
        used.add(choice)
    if cfg.get("compatibility") == "explicit_formal_roles":
        from murdoku_lab.visual.asset_catalog import catalog

        if any(
            kind not in catalog()[asset]["formal_roles"]
            for kind, asset in selected.items()
        ):
            raise ValueError("selection does not preserve explicit formal role")
    validate_selection(case, selected)
    objects = dict(theme.objects)
    from murdoku_lab.visual.asset_catalog import catalog

    for kind, asset in selected.items():
        objects[kind] = catalog()[asset]["concept"]
    return replace(theme, assets=selected, objects=objects)
