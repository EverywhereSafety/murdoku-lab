"""Additional gates for English training themes; not a proof of prose equivalence."""

import re
from dataclasses import replace
from murdoku_lab.core.theme import Theme


def neutralize_setup(theme):
    # Free narrative is not part of the formal case and can accidentally add facts.
    return replace(theme, blurb="", victim_note="was found dead")


def quality_issues(case, theme):
    theme.validate(case)
    issues = []
    missing = {p.pid for p in case.scene.props} - set(theme.objects)
    if missing:
        issues.append(
            "Every board prop needs an explicit themed label; missing: "
            + ", ".join(sorted(missing))
        )
    fields = [
        theme.title,
        *theme.names.values(),
        *theme.areas,
        *theme.objects.values(),
        *theme.tags.values(),
    ]
    if any(re.search(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", v) for v in fields):
        issues.append("All display labels must be English; non-English labels found")
    for label, values in [
        ("character", [theme.name(c) for c in case.characters]),
        ("area", list(theme.areas)),
        ("prop", [theme.obj(p.pid) for p in case.scene.props]),
    ]:
        normalized = [" ".join(v.casefold().split()) for v in values]
        if any(not v for v in normalized):
            issues.append(f"Empty {label} label")
        if len(set(normalized)) != len(normalized):
            issues.append(f"Ambiguous duplicate {label} labels")
    if theme.blurb or theme.victim_note != "was found dead":
        issues.append("Free setup text must be empty and victim note neutral")
    return issues


def parse_review(value):
    if not isinstance(value, dict) or type(value.get("accept")) is not bool:
        raise ValueError("review must contain a boolean accept")
    issues = value.get("issues")
    if not isinstance(issues, list) or any(not isinstance(x, str) for x in issues):
        raise ValueError("review must contain a list of issue strings")
    if value["accept"] and issues:
        raise ValueError("accept contradicts nonempty issues")
    if not value["accept"] and not issues:
        raise ValueError("rejection requires a reason")
    return value
