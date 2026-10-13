// Presentation only: derive exclusions from the player's own placements.
export function lineExclusions(state) {
  const cells = new Map(state.scene.cells.map((cell) => [cell.cell, cell]));
  const rows = new Set();
  const cols = new Set();
  const occupied = new Set(Object.values(state.placements));
  for (const label of occupied) {
    const cell = cells.get(label);
    if (!cell) continue;
    rows.add(cell.row);
    cols.add(cell.col);
  }
  return new Set(
    state.scene.cells
      .filter(
        (cell) =>
          cell.standable &&
          !occupied.has(cell.cell) &&
          (rows.has(cell.row) || cols.has(cell.col)),
      )
      .map((cell) => cell.cell),
  );
}

export function assistMarkup(markup, state, selected, enabled) {
  if (!markup) return markup;
  const document = new DOMParser().parseFromString(markup, "image/svg+xml");
  const svg = document.documentElement;
  const ns = "http://www.w3.org/2000/svg";
  const layer = document.createElementNS(ns, "g");
  layer.setAttribute("class", "line-exclusions");
  layer.setAttribute("pointer-events", "none");
  layer.setAttribute("aria-hidden", "true");
  const excluded = enabled ? lineExclusions(state) : new Set();
  const manual = new Set(state.exclusions?.[selected] || []);
  const occupied = new Set(Object.values(state.placements));
  for (const hit of svg.querySelectorAll("[data-cell]")) {
    const label = hit.getAttribute("data-cell");
    if (!excluded.has(label) && !manual.has(label)) continue;
    if (excluded.has(label)) hit.setAttribute("data-line-excluded", "true");
    if (manual.has(label)) hit.setAttribute("data-manual-excluded", "true");
    hit.setAttribute(
      "aria-label",
      `${hit.getAttribute("aria-label")}; ${manual.has(label) ? "your exclusion for " + selected : "row or column occupied by a placed person"}`,
    );
    if (occupied.has(label) || manual.has(label)) continue;
    const rect = hit.querySelector("rect");
    const x =
      Number(rect.getAttribute("x")) + Number(rect.getAttribute("width")) / 2;
    const y =
      Number(rect.getAttribute("y")) + Number(rect.getAttribute("height")) / 2;
    const path = document.createElementNS(ns, "path");
    path.setAttribute("d", `M${x - 12} ${y - 12}l24 24m0-24l-24 24`);
    path.setAttribute("stroke", manual.has(label) ? "#a44b89" : "#805b56");
    path.setAttribute("stroke-width", "4");
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("opacity", manual.has(label) ? ".95" : ".7");
    layer.append(path);
  }
  svg.append(layer);
  return new XMLSerializer().serializeToString(svg);
}
