// Base rules the board shows as you play: one person per row and column, nobody on a blocked
// square. These never look at a clue or the answer.

function rowOf(cell) {
  return Number(cell.slice(1)) - 1;
}

function colOf(cell) {
  return cell.charCodeAt(0) - 97;
}

export { rowOf, colOf };

// People who break a base rule, and the squares, rows and columns involved.
export function conflicts(game, placed) {
  const people = new Set();
  const rows = new Map();
  const cols = new Map();
  const squares = new Map();
  const blocked = new Set();
  for (const [who, cell] of Object.entries(placed)) {
    const info = game.byLabel.get(cell);
    if (info && !info.standable) {
      blocked.add(who);
      people.add(who);
    }
    for (const [map, key] of [
      [rows, rowOf(cell)],
      [cols, colOf(cell)],
      [squares, cell],
    ]) {
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(who);
    }
  }
  const crowded = (map) => new Set([...map].filter(([, xs]) => xs.length > 1).map(([k]) => k));
  const badRows = crowded(rows);
  const badCols = crowded(cols);
  const stacked = crowded(squares);
  for (const [map, bad] of [
    [rows, badRows],
    [cols, badCols],
    [squares, stacked],
  ]) {
    for (const key of bad) for (const who of map.get(key)) people.add(who);
  }
  return { people, rows: badRows, cols: badCols, stacked, blocked };
}

// Squares a person cannot use given everyone else already placed: their rows and columns, plus
// blocked squares. This is the row/column crossing a player would pencil in by hand.
export function crossedFor(game, placed, who) {
  const out = new Set();
  const taken = Object.entries(placed).filter(([p]) => p !== who);
  for (const c of game.cells) {
    if (!c.standable) out.add(c.cell);
    else if (taken.some(([, cell]) => rowOf(cell) === c.row || colOf(cell) === c.col)) out.add(c.cell);
  }
  return out;
}

export function isComplete(game, placed) {
  return game.personIds.every((p) => p in placed);
}
