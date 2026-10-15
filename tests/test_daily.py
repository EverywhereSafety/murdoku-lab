"""The daily schedule: rhythm, rotation, reproducible seeds, locked content and the build."""

import json

import pytest

from murdoku_lab.setter import daily, export_queries
from murdoku_lab.visual.seal import unseal


@pytest.fixture(scope="module")
def spec():
    return daily.season("s01")


def test_plan_follows_the_weekly_rhythm(spec):
    days = daily.plan(spec, 28)
    assert [d["n"] for d in days] == list(range(1, 29))
    for d in days:
        assert [d["size"], d["band"]] == spec["rhythm"][d["weekday"]]
        assert d["seeds"] == [
            daily.seed_for(daily.dt.date.fromisoformat(d["date"]), j)
            for j in range(spec["candidates"])
        ]
    sundays = [d for d in days if d["weekday"] == "sunday"]
    assert all(d["special"] == "Sunday Special" for d in sundays)


def test_no_setting_repeats_within_a_week(spec):
    days = daily.plan(spec, 56)
    for start in range(0, 56, 7):
        week = [d["setting"] for d in days[start : start + 7]]
        assert len(set(week)) == 7


def test_case_numbers_count_days_from_the_epoch(spec):
    epoch = daily.dt.date.fromisoformat(spec["epoch"])
    assert daily.number(spec, epoch) == 1
    assert daily.number(spec, epoch + daily.dt.timedelta(days=30)) == 31


def test_locked_days_keep_the_variety_rules(spec):
    days = daily.locked_days(spec)
    if not days:
        pytest.skip("no locked daily cases in this checkout")
    by_setting = {}
    for record in days:
        title = record["murdoku_theme"]["title"]
        by_setting.setdefault(record["setting"], []).append(title)
    for titles in by_setting.values():
        assert len(set(titles)) == len(titles)
    letters = [d["murderer"] for d in days]
    assert all(a != b for a, b in zip(letters, letters[1:]))
    published = export_queries.daily_published()
    from murdoku_lab.core.instance import Case

    assert all(
        Case.from_json(d["murdoku_case"]).content_hash() in published for d in days
    )


def test_build_writes_sealed_bundles_and_preview_pages(spec, tmp_path):
    days = daily.locked_days(spec)
    if not days:
        pytest.skip("no locked daily cases in this checkout")
    index = daily.build(spec, tmp_path, site_url="https://example.org/play/")
    first = index["days"][0]
    bundle = json.loads((tmp_path / "daily" / first["url"]).read_text())
    assert bundle["daily"]["n"] == first["n"]
    secret = unseal(bundle["secret"], bundle["id"], first["date"])
    assert set(secret["solution"]) == {p["id"] for p in bundle["public"]["people"]}
    with pytest.raises(Exception):
        unseal(bundle["secret"], bundle["id"], "1999-01-01")
    page = (tmp_path / "d" / str(first["n"]) / "index.html").read_text()
    assert f"https://example.org/play/og/{first['n']}.png" in page
    assert (tmp_path / "og" / f"{first['n']}.png").read_bytes().startswith(b"\x89PNG")
