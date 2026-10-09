import json
from pathlib import Path
from murdoku_lab.core.instance import Case
import pytest
from murdoku_lab.core.theme import canonical_theme, Theme
from murdoku_lab.visual.asset_catalog import search_assets, validate_selection, catalog
from murdoku_lab.setter.visual_assets import select_assets


@pytest.fixture
def case():
    return Case.from_json(
        json.loads(
            (Path(__file__).parent / "fixtures/quality_base_case.json").read_text()
        )
    )


def test_catalog_search_filters_role_and_concept():
    rows = search_assets("chair", formal_role="chair")
    assert rows and all("chair" in r["formal_roles"] for r in rows)
    assert search_assets("chair", formal_role="bear") == []


def test_setter_rejects_invented_asset(case):
    class Client:
        def chat(self, *args, **kwargs):
            return '{"assets":{"unknown":"made-up"}}'

    with pytest.raises(ValueError):
        select_assets(
            case,
            canonical_theme(case),
            client=Client(),
            config={
                "enabled": True,
                "pack": "fluent-color",
                "compatibility": "explicit_formal_roles",
                "allow_missing": True,
                "selection": "llm",
            },
        )


def test_asset_selection_roundtrips_without_changing_case(case):
    before = case.to_json()
    theme = select_assets(
        case,
        canonical_theme(case),
        client=None,
        config={
            "enabled": True,
            "pack": "fluent-color",
            "compatibility": "explicit_formal_roles",
            "allow_missing": True,
            "selection": "deterministic",
        },
    )
    assert theme.assets
    validate_selection(case, theme.assets)
    assert Theme.from_json(theme.to_json()).assets == theme.assets
    assert case.to_json() == before
    with pytest.raises(ValueError):
        validate_selection(case, {"not-a-prop": "chair"})


def test_llm_selects_only_retrieved_candidates(case):
    class Client:
        def chat(self, messages, **kwargs):
            prompt = json.loads(messages[-1]["content"])
            assert "solution" not in prompt
            return json.dumps(
                {
                    "assets": {
                        kind: rows[-1]["asset_id"]
                        for kind, rows in prompt["candidates"].items()
                    }
                }
            )

    theme = select_assets(
        case,
        canonical_theme(case),
        client=Client(),
        config={
            "enabled": True,
            "pack": "fluent-color",
            "compatibility": "explicit_formal_roles",
            "allow_missing": True,
            "selection": "llm",
        },
    )
    validate_selection(case, theme.assets)
    for kind, asset in theme.assets.items():
        assert theme.objects[kind] == catalog()[asset]["concept"]


def test_class_selection_has_distinct_labels_and_compatible_geometry(case):
    class Client:
        def chat(self, messages, **kwargs):
            prompt = json.loads(messages[-1]["content"])
            return json.dumps(
                {
                    "assets": {
                        kind: rows[0]["asset_id"]
                        for kind, rows in prompt["candidates"].items()
                    }
                }
            )

    theme = select_assets(
        case,
        canonical_theme(case),
        client=Client(),
        config={
            "enabled": True,
            "pack": "fluent-color",
            "compatibility": "prop_classes",
            "allow_missing": False,
            "selection": "llm",
            "search_limit": 48,
        },
    )
    assert len(set(theme.assets.values())) == len(theme.assets)
    assert len(set(theme.objects[k] for k in theme.assets)) == len(theme.assets)
    validate_selection(case, theme.assets)
    assert Theme.from_json(theme.to_json()).assets == theme.assets
