// Daily cases by the player's local calendar day. Dates are plain YYYY-MM-DD strings and all
// day arithmetic goes through Date.UTC, so daylight-saving changes never skip or repeat a day.

const ISO = /^\d{4}-\d{2}-\d{2}$/;

export function localDay(now = new Date()) {
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

// ?date=YYYY-MM-DD previews another day locally.
export function today(params = new URLSearchParams(), now = new Date()) {
  const forced = params.get("date");
  return forced && ISO.test(forced) ? forced : localDay(now);
}

function utc(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return Date.UTC(y, m - 1, d);
}

export function daysBetween(a, b) {
  return Math.round((utc(b) - utc(a)) / 86400000);
}

export function addDays(iso, n) {
  const t = new Date(utc(iso) + n * 86400000);
  return `${t.getUTCFullYear()}-${String(t.getUTCMonth() + 1).padStart(2, "0")}-${String(t.getUTCDate()).padStart(2, "0")}`;
}

export function caseNumber(epoch, iso) {
  return daysBetween(epoch, iso) + 1;
}

// The cases a player may open: everything up to today, or the whole season with ?unlock=all.
export function openDays(manifest, day, unlockAll = false) {
  return manifest.days.filter((d) => unlockAll || d.date <= day);
}

export function todaysCase(manifest, day) {
  return manifest.days.find((d) => d.date === day) || null;
}

export function msToMidnight(now = new Date()) {
  const next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  return next - now;
}

// A streak counts days whose case was solved on that very day. Replaying an older case earns
// its stars but not a streak day. Today still unsolved does not break a streak that ran
// through yesterday.
export function streaks(record, day) {
  const onTime = new Set(
    Object.values(record)
      .filter((r) => r.solved_on && r.solved_on === r.date)
      .map((r) => r.date),
  );
  let current = 0;
  let cursor = onTime.has(day) ? day : addDays(day, -1);
  while (onTime.has(cursor)) {
    current += 1;
    cursor = addDays(cursor, -1);
  }
  let best = 0;
  let run = 0;
  let previous = null;
  for (const date of [...onTime].sort()) {
    run = previous && daysBetween(previous, date) === 1 ? run + 1 : 1;
    best = Math.max(best, run);
    previous = date;
  }
  return { current, best };
}

export function stats(record) {
  const rows = Object.values(record);
  const solved = rows.filter((r) => r.stars);
  return {
    played: rows.length,
    solved: solved.length,
    perfect: solved.filter((r) => r.stars === 3).length,
    hints: solved.length ? solved.reduce((sum, r) => sum + (r.hints || 0), 0) / solved.length : 0,
  };
}

// The spoiler-free share line: one square per person (green unaided, yellow nudge, orange
// partial, red answer), the verdict, stars and hints. Never a square or a name.
export function shareSquares(game, hints) {
  const worst = new Map();
  for (const h of hints) {
    const who = h.target.startsWith("next:") || h.target.startsWith("misplaced:") ? h.target.split(":")[1] : null;
    if (!who) continue;
    const level = h.reveal ? 3 : Math.min(2, h.level);
    worst.set(who, Math.max(worst.get(who) || 0, level));
  }
  const tiles = ["🟩", "🟨", "🟧", "🟥"];
  return game.personIds.map((p) => tiles[worst.get(p) || 0]).join("");
}
