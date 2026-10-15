// Static data: the case library, case bundles and scenes, all relative to the player page so
// the same build works at /, below a path prefix, or from a LAN address.
import { makeCase } from "./engine/case.js";

const root = new URL(".", window.location.href);

export const assetUrl = (path) => new URL(path, root).href;

let library = null;

export function loadLibrary() {
  library ??= fetch(assetUrl("cases/index.json")).then((response) => {
    if (!response.ok) throw new Error(`Case library unavailable (${response.status})`);
    return response.json();
  });
  return library;
}

let daily = null;

// The daily manifest, or null when this build has no daily cases.
export function loadDaily() {
  daily ??= fetch(assetUrl("daily/manifest.json"))
    .then((response) => (response.ok ? response.json() : null))
    .catch(() => null);
  return daily;
}

// Daily cases (daily-<n>) live in daily/ and are sealed with their date.
export async function loadCase(id) {
  const dir = id.startsWith("daily-") ? "daily/" : "cases/";
  const response = await fetch(assetUrl(`${dir}${encodeURIComponent(id)}.json`));
  if (!response.ok) throw new Error(`Case ${id} unavailable (${response.status})`);
  const bundle = await response.json();
  const game = makeCase(bundle, { salt: bundle.daily?.date ?? "" });
  game.dir = dir;
  return game;
}

const scenes = new Map();

export function loadScene(game, mode = "day") {
  const name = game.bundle.scene[mode];
  if (!scenes.has(name)) {
    scenes.set(
      name,
      fetch(assetUrl(`${game.dir || "cases/"}${name}`)).then((response) => {
        if (!response.ok) throw new Error("Scene unavailable");
        return response.text();
      }),
    );
  }
  return scenes.get(name);
}
