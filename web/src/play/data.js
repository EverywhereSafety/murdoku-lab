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

export async function loadCase(id) {
  const response = await fetch(assetUrl(`cases/${encodeURIComponent(id)}.json`));
  if (!response.ok) throw new Error(`Case ${id} unavailable (${response.status})`);
  return makeCase(await response.json());
}

const scenes = new Map();

export function loadScene(game, mode = "day") {
  const name = game.bundle.scene[mode];
  if (!scenes.has(name)) {
    scenes.set(
      name,
      fetch(assetUrl(`cases/${name}`)).then((response) => {
        if (!response.ok) throw new Error("Scene unavailable");
        return response.text();
      }),
    );
  }
  return scenes.get(name);
}
