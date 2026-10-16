// Graded hints from the sealed hint data (murdoku_lab/visual/play_export.py hint_data).
// Order of business: someone misplaced, then the next person the clues pin down, then the
// verdict. Each target escalates on repeat: a nudge, a partial fact, then the answer.

const first = (game, who) => game.person.get(who).name.split(" ")[0];
const up = (cell) => cell.toUpperCase();

function levelFor(used, target, max) {
  const seen = used.filter((h) => h.target === target).map((h) => h.level);
  return Math.min(max, 1 + Math.max(0, ...seen));
}

export function nextHint(game, state, used = []) {
  const secret = game.secret();
  const { order, candidates, forbid } = secret.hints;
  const solution = secret.solution;

  const misplaced = order.filter((p) => state.placed[p] && state.placed[p] !== solution[p]);
  if (misplaced.length) {
    const who = misplaced[0];
    const at = state.placed[who];
    const target = `misplaced:${who}:${at}`;
    const level = levelFor(used, target, 4);
    const name = first(game, who);
    if (level === 1) return { target, level, reveal: false, key: "hint.misplaced.1", vars: {}, focus: {} };
    if (level === 2) return { target, level, reveal: false, key: "hint.misplaced.2", vars: { name }, focus: { person: who } };
    if (level === 3) {
      const n = forbid[who]?.[at];
      return n
        ? { target, level, reveal: false, key: "hint.misplaced.3a", vars: { name, cell: up(at), n }, focus: { person: who, cells: [at], clue: `clue-${n}` } }
        : { target, level, reveal: false, key: "hint.misplaced.3b", vars: { name, cell: up(at) }, focus: { person: who, cells: [at] } };
    }
    return {
      target,
      level,
      reveal: true,
      key: "hint.misplaced.4",
      vars: { name, cell: up(solution[who]) },
      focus: { person: who, cells: [solution[who]] },
      fix: { person: who, cell: solution[who] },
    };
  }

  const next = order.find((p) => !(p in state.placed));
  if (next) {
    const target = `next:${next}`;
    const level = levelFor(used, target, 3);
    const name = first(game, next);
    const own = game.clues.find((c) => c.person === next)?.id;
    if (level === 1) return { target, level, reveal: false, key: "hint.next.1", vars: { name }, focus: { person: next, clue: own } };
    if (level === 2) {
      const room = game.areaOf.get(solution[next]);
      const pinned = (candidates[next] || []).every((cell) => game.areaOf.get(cell) === room);
      if (pinned) {
        const row = Number(solution[next].slice(1));
        const cells = game.cells.filter((c) => c.row === row - 1).map((c) => c.cell);
        return { target, level, reveal: false, key: "hint.next.2row", vars: { name, row }, focus: { person: next, cells } };
      }
      const cells = game.cells.filter((c) => c.area === room).map((c) => c.cell);
      const roomName = game.areas.find((a) => a.id === room)?.name ?? "";
      return { target, level, reveal: false, key: "hint.next.2room", vars: { name, room: roomName }, focus: { person: next, cells } };
    }
    return {
      target,
      level,
      reveal: true,
      key: "hint.next.3",
      vars: { name, cell: up(solution[next]) },
      focus: { person: next, cells: [solution[next]] },
      fix: { person: next, cell: solution[next] },
    };
  }

  const target = "verdict";
  if (secret.goal_type !== "murderer")
    return { target, level: 1, reveal: false, key: "hint.verdict.cell", vars: {}, focus: {} };
  const level = levelFor(used, target, 3);
  const victim = first(game, game.victim);
  const area = secret.victim_area;
  const cells = game.cells.filter((c) => c.area === area).map((c) => c.cell);
  const room = game.areas.find((a) => a.id === area)?.name ?? "";
  if (level === 1) return { target, level, reveal: false, key: "hint.verdict.1", vars: { victim }, focus: { cells } };
  if (level === 2) return { target, level, reveal: false, key: "hint.verdict.2", vars: { room }, focus: { cells } };
  return { target, level, reveal: true, key: "hint.verdict.3", vars: { name: first(game, secret.murderer) }, focus: { person: secret.murderer, cells } };
}
