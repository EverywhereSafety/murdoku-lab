"""The daily case: plan a season, generate candidates, pick, lock and build.

    python -m murdoku_lab.setter.daily plan --days 14
    python -m murdoku_lab.setter.daily generate --days 14 --workers 8
    python -m murdoku_lab.setter.daily review 2026-10-15      # candidates side by side
    python -m murdoku_lab.setter.daily pick 2026-10-15 2      # optional: override the auto pick
    python -m murdoku_lab.setter.daily lock --days 14
    python -m murdoku_lab.setter.daily status
    python -m murdoku_lab.setter.daily build                  # → web/public/daily, og, d/<n>

A season (config/daily/season-<id>.json) fixes the weekly rhythm of board sizes and bands, the
epoch that numbers cases (#1 is the epoch's day), and the setting rotation: no setting repeats
within a week. Each day gets a few candidates from the constraint-first farm with seeds derived
from sha256("murdoku/daily/v1/<date>/<j>"), so a day can always be regenerated. Locking picks a
candidate (the reviewer's pick, or the first that keeps the variety rules: a new room layout and
not yesterday's murderer letter, farming a few more candidates when none does), dresses it in the
day's setting (preferring a title the setting has not used yet and a victim not seen in the last
five days) and records the candidate, seed, git revision and solver version. Locked cases are listed in
content/daily/published.json so dataset exports can leave them out.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme
from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def season(season_id="s01"):
    return json.loads(
        (ROOT / "config" / "daily" / f"season-{season_id}.json").read_text()
    )


def content_dir(spec):
    return ROOT / "content" / "daily" / spec["season"]


def number(spec, date):
    return (date - dt.date.fromisoformat(spec["epoch"])).days + 1


def seed_for(date, j):
    digest = hashlib.sha256(
        f"murdoku/daily/v1/{date.isoformat()}/{j}".encode()
    ).hexdigest()
    return int(digest[:8], 16)


def _rotation(spec, week):
    """The settings for one week: a seeded shuffle, so no setting repeats within the week and
    consecutive weeks differ."""
    order = list(spec["settings"])
    key = hashlib.sha256(
        f"murdoku/daily/v1/{spec['season']}/week/{week}".encode()
    ).digest()
    for i in range(len(order) - 1, 0, -1):
        j = key[i % len(key)] % (i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def plan(spec, days=None):
    start = dt.date.fromisoformat(spec["start"])
    total = days or spec["weeks"] * 7
    out = []
    for i in range(total):
        date = start + dt.timedelta(days=i)
        weekday = WEEKDAYS[date.weekday()]
        size, band = spec["rhythm"][weekday]
        week = i // 7
        rotation = _rotation(spec, week)
        if (
            week > 0
            and rotation[0] == _rotation(spec, week - 1)[(7 - 1) % len(rotation)]
        ):
            rotation = rotation[1:] + rotation[:1]
        out.append(
            {
                "date": date.isoformat(),
                "n": number(spec, date),
                "weekday": weekday,
                "size": size,
                "band": band,
                "setting": rotation[date.weekday() % len(rotation)],
                "special": spec.get("special", {}).get(weekday),
                "seeds": [seed_for(date, j) for j in range(spec["candidates"])],
            }
        )
    return out


def _candidates_path(spec, date):
    return content_dir(spec) / "candidates" / f"{date}.jsonl"


def _farm(day, seed, count, path, workers=6):
    """Farm `count` candidates for one day with `seed`, appending to `path`."""
    scratch = path.with_suffix(f".{seed}.part.jsonl")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "murdoku_lab.setter.farm",
            "--strategy",
            "constraint-first",
            "--variant",
            "classic",
            "--size",
            str(day["size"]),
            "--bands",
            day["band"],
            "--n",
            str(count),
            "--shots",
            "8",
            "--workers",
            str(workers),
            "--seed",
            str(seed),
            "--rhythm-policy",
            str(ROOT / "config" / "rhythm" / "player.json"),
            "--scene-spec",
            str(ROOT / "config" / "scene_specs" / "cozy.json"),
            "--out",
            str(scratch),
        ],
        check=False,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if scratch.exists():
        with path.open("a") as out:
            out.write(scratch.read_text())
        scratch.unlink()
    for stats in path.parent.glob(f"{scratch.stem}*.farm_stats.json"):
        stats.unlink()


def generate(spec, days=None, workers=6):
    """Farm candidates for every planned day that has none yet."""
    out = []
    for day in plan(spec, days):
        path = _candidates_path(spec, day["date"])
        if path.exists() and path.read_text().strip():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        started = time.time()
        _farm(day, day["seeds"][0], len(day["seeds"]), path, workers)
        took = round(time.time() - started, 1)
        count = len(path.read_text().splitlines())
        out.append({"date": day["date"], "candidates": count, "seconds": took})
        print(
            f"{day['date']} {day['size']}×{day['size']} {day['band']}: {count} candidate(s) in {took}s",
            flush=True,
        )
    return out


def candidates(spec, date):
    path = _candidates_path(spec, date)
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [Case.from_json(row.get("murdoku_case", row)) for row in rows]


def _picks_path(spec):
    return content_dir(spec) / "picks.json"


def pick(spec, date, j):
    picks = _read(_picks_path(spec), {})
    picks[date] = int(j)
    _write(_picks_path(spec), picks)


def _read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n")


def _layout(case):
    return hashlib.sha256(json.dumps(case.scene.area_of).encode()).hexdigest()[:16]


def lock(spec, days=None):
    """Pick, dress and lock every planned day with candidates; earlier locks stay as they are."""
    from murdoku_lab.setter import settings

    try:
        import ortools

        solver = ortools.__version__
    except Exception:  # noqa: BLE001
        solver = "unknown"
    git = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout.strip()
    picks = _read(_picks_path(spec), {})
    lock_path = content_dir(spec) / "lock.json"
    locks = _read(lock_path, {})
    published = _read(ROOT / "content" / "daily" / "published.json", {})
    days_dir = content_dir(spec) / "days"
    history = []
    for date in sorted(locks):
        record = json.loads((days_dir / f"{date}.json").read_text())
        history.append(
            (
                date,
                _layout(Case.from_json(record["murdoku_case"])),
                record["murderer"],
                record["victim"],
            )
        )
    for day in plan(spec, days):
        date = day["date"]
        if date in locks:
            continue
        pool = candidates(spec, date)
        if not pool:
            continue
        # Six Vanes take turns as victims, so "no repeat within five days" is always possible.
        recent = history[-5:]
        layouts = {h[1] for h in history}

        def fits(case):
            letter = case.murderer
            yesterday = history[-1][2] if history else None
            return _layout(case) not in layouts and letter != yesterday

        # Top a day up from further seeds when none of its candidates keeps the variety rules.
        for extra in range(1, 4):
            if any(fits(c) for c in pool) or date in picks:
                break
            _farm(
                day,
                seed_for(dt.date.fromisoformat(date), len(day["seeds"]) + extra),
                2,
                _candidates_path(spec, date),
            )
            pool = candidates(spec, date)
        order = list(range(len(pool)))
        if date in picks:
            order = [picks[date]] + [i for i in order if i != picks[date]]
        j = next((i for i in order if fits(pool[i])), order[0])
        case = pool[j]
        victims = {h[3] for h in recent}
        used_titles = set()
        for earlier in sorted(locks):
            previous = json.loads((days_dir / f"{earlier}.json").read_text())
            if previous["setting"] == day["setting"]:
                used_titles.add(Theme.from_json(previous["murdoku_theme"]).title)
        dressings = []
        for attempt in range(40):
            salt = date if attempt == 0 else f"{date}#{attempt}"
            dressings.append((salt, settings.dress(case, day["setting"], salt=salt)))
        fresh = [d for d in dressings if d[1].title not in used_titles]
        best = [d for d in fresh if d[1].name(case.victim) not in victims]
        salt, theme = (best or fresh or dressings)[0]
        record = {
            "schema": "murdoku.daily_case/1",
            "date": date,
            "n": day["n"],
            "weekday": day["weekday"],
            "size": day["size"],
            "band": day["band"],
            "special": day["special"],
            "setting": day["setting"],
            "murderer": case.murderer,
            "victim": theme.name(case.victim),
            "murdoku_case": case.to_json(),
            "murdoku_theme": theme.to_json(),
        }
        _write(days_dir / f"{date}.json", record)
        locks[date] = {
            "candidate": j,
            "seed": day["seeds"][0],
            "salt": salt,
            "content_hash": case.content_hash(),
            "git": git,
            "ortools": solver,
            "locked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }
        published[case.content_hash()] = f"{spec['season']}/{date}"
        history.append((date, _layout(case), case.murderer, theme.name(case.victim)))
        print(f"locked {date} #{day['n']} {day['setting']}: {theme.title}")
    _write(lock_path, locks)
    _write(ROOT / "content" / "daily" / "published.json", published)
    return locks


def status(spec, days=None):
    locks = _read(content_dir(spec) / "lock.json", {})
    rows = []
    for day in plan(spec, days):
        pool = candidates(spec, day["date"])
        title = ""
        if day["date"] in locks:
            record = json.loads(
                (content_dir(spec) / "days" / f"{day['date']}.json").read_text()
            )
            title = Theme.from_json(record["murdoku_theme"]).title
        rows.append(
            f"#{day['n']:<4} {day['date']} {day['weekday'][:3]} {day['size']}×{day['size']} "
            f"{day['band']:<6} {day['setting']:<10} candidates={len(pool)} "
            f"{'locked: ' + title if title else 'open'}"
        )
    return rows


def locked_days(spec):
    days_dir = content_dir(spec) / "days"
    return [json.loads(p.read_text()) for p in sorted(days_dir.glob("*.json"))]


def build(spec, out=None, site_url=""):
    """Write the locked days for the player: bundles sealed with their date, scenes, thumbs,
    share images and a link-preview page per day."""
    from murdoku_lab.environment.state import Scratchpad
    from murdoku_lab.setter import settings
    from murdoku_lab.visual.art import STATIC_LAYERS, casebook, thumbnail_svg
    from murdoku_lab.visual.art.cards import card_for, share_card_svg
    from murdoku_lab.visual.play_export import bundle
    from murdoku_lab.visual.projection import public_observation
    from murdoku_lab.visual.raster import bundled_profile, png_from_svg

    out = Path(out or ROOT / "web" / "public")
    daily_dir = out / "daily"
    for directory in (daily_dir, out / "og", out / "d"):
        if directory.exists():
            import shutil

            shutil.rmtree(directory)
    daily_dir.mkdir(parents=True)
    (out / "og").mkdir()
    manifest = []
    for record in locked_days(spec):
        case = Case.from_json(record["murdoku_case"])
        theme = Theme.from_json(record["murdoku_theme"])
        pack = settings.load(theme.setting_id)
        n = record["n"]
        case_id = f"daily-{n}"
        data = bundle(
            case,
            theme,
            case_id=case_id,
            kind="daily",
            setting=pack["name"],
            eyebrow=f"Daily case #{n}",
            salt=record["date"],
        )
        data["daily"] = {
            "n": n,
            "date": record["date"],
            "weekday": record["weekday"],
            "season": spec["season"],
            "special": record["special"],
        }
        data["share"] = {"url": f"{site_url}d/{n}/", "og_image": f"og/{n}.png"}
        data["scene"] = {"day": f"{case_id}.day.svg", "night": f"{case_id}.night.svg"}
        data["thumb"] = f"{case_id}.thumb.svg"
        (daily_dir / f"{case_id}.json").write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        )
        obs = public_observation(Scratchpad(case, theme))
        for mode in ("day", "night"):
            (daily_dir / f"{case_id}.{mode}.svg").write_text(
                casebook.scene_svg(
                    obs,
                    theme=mode,
                    layers=STATIC_LAYERS,
                    cell_labels="none",
                    backdrop=False,
                )
            )
        (daily_dir / f"{case_id}.thumb.svg").write_text(thumbnail_svg(obs, px=320))
        weekday = record["weekday"].title()
        date = dt.date.fromisoformat(record["date"])
        label = f"{weekday[:3]} {date.day} {date.strftime('%b')}"
        card = card_for(
            case,
            theme,
            state="unsolved",
            number=n,
            date=label,
            difficulty=record["band"].title(),
            url=data["share"]["url"].replace("https://", "").replace("http://", ""),
        )
        (out / "og" / f"{n}.png").write_bytes(
            png_from_svg(share_card_svg(card, "og"), profile=bundled_profile())
        )
        _og_page(out / "d" / str(n), n, theme, pack, record, site_url)
        manifest.append(
            {
                "n": n,
                "id": case_id,
                "date": record["date"],
                "weekday": record["weekday"],
                "special": record["special"],
                "title": theme.title,
                "blurb": theme.blurb,
                "setting": {"id": theme.setting_id, "name": pack["name"]},
                "size": f"{case.scene.W}×{case.scene.H}",
                "difficulty": data["meta"]["difficulty"],
                "accent": data["meta"]["accent"],
                "content_hash": data["content_hash"],
                "thumb": data["thumb"],
                "url": f"{case_id}.json",
            }
        )
    index = {
        "schema": "murdoku.daily_manifest/1",
        "season": spec["season"],
        "epoch": spec["epoch"],
        "days": manifest,
    }
    (daily_dir / "manifest.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1) + "\n"
    )
    return index


def _og_page(directory, n, theme, pack, record, site_url):
    """A tiny page per case for link previews; people who open it land on the case."""
    from html import escape

    directory.mkdir(parents=True, exist_ok=True)
    title = f"Murdoku Daily #{n} · {theme.title}"
    description = f"{pack['name']} · {record['size']}×{record['size']} {record['band']} · {theme.blurb}"
    image = f"{site_url}og/{n}.png" if site_url else f"../../og/{n}.png"
    (directory / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{escape(title)}</title>"
        f'<meta name="description" content="{escape(description)}">'
        f'<meta property="og:title" content="{escape(title)}">'
        f'<meta property="og:description" content="{escape(description)}">'
        f'<meta property="og:image" content="{escape(image)}">'
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta http-equiv="refresh" content="0; url=../../?d={n}">'
        f'</head><body><a href="../../?d={n}">{escape(title)}</a></body></html>\n'
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--season", default="s01")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "generate", "lock", "status"):
        p = sub.add_parser(name)
        p.add_argument("--days", type=int, default=None)
        if name == "generate":
            p.add_argument("--workers", type=int, default=6)
    p = sub.add_parser("pick")
    p.add_argument("date")
    p.add_argument("candidate", type=int)
    p = sub.add_parser("review")
    p.add_argument("date")
    p = sub.add_parser("build")
    p.add_argument("--out", default=None)
    p.add_argument("--site-url", default="")
    args = parser.parse_args(argv)
    spec = season(args.season)
    if args.command == "plan":
        for day in plan(spec, args.days):
            print(
                f"#{day['n']:<4} {day['date']} {day['weekday'][:3]} {day['size']}×{day['size']} {day['band']:<6} {day['setting']}"
            )
    elif args.command == "generate":
        generate(spec, args.days, args.workers)
    elif args.command == "pick":
        pick(spec, args.date, args.candidate)
        print(f"picked candidate {args.candidate} for {args.date}")
    elif args.command == "review":
        from murdoku_lab.solver.logic import certify

        for j, case in enumerate(candidates(spec, args.date)):
            cert = certify(case)
            print(
                f"[{j}] murderer {case.murderer} · {len(case.clues)} clues · cost {cert.cost} · depth {cert.depth}"
            )
            for clue_no, clue in enumerate(case.clues, start=1):
                print(f"     {clue_no}. {clue.holder}: {[a.kind for a in clue.atoms]}")
    elif args.command == "lock":
        lock(spec, args.days)
    elif args.command == "status":
        print("\n".join(status(spec, args.days)))
    elif args.command == "build":
        index = build(spec, args.out, args.site_url)
        print(f"built {len(index['days'])} daily cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
