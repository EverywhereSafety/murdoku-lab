// Versioned local saves: one profile, and one record per case. Nothing leaves the browser.
// A case record keeps the moves (replayed on load) and is dropped if the case content changed.
const PREFIX = "murdoku:v1:";

function storage() {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null;
  }
}

export function read(key, fallback) {
  try {
    const raw = storage()?.getItem(PREFIX + key);
    return raw == null ? fallback : JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function write(key, value) {
  try {
    storage()?.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    // Private browsing or a full quota: play on without saving.
  }
}

export const caseKey = (id) => `case:${id}`;

export function freshProgress(game) {
  return {
    content_hash: game.bundle.content_hash,
    events: [],
    elapsed_ms: 0,
    wrong_verdicts: 0,
    hints: [],
    finished: null,
  };
}

export function loadProgress(game) {
  const saved = read(caseKey(game.id), null);
  if (!saved || saved.content_hash !== game.bundle.content_hash) return freshProgress(game);
  return { ...freshProgress(game), ...saved };
}

export function saveProgress(game, progress) {
  write(caseKey(game.id), progress);
}

export const DEFAULT_SETTINGS = {
  sound: false,
  haptics: false,
  night: false,
  timer: false,
  notesFirst: false,
};

export function loadProfile() {
  const profile = read("profile", {});
  return {
    settings: { ...DEFAULT_SETTINGS, ...(profile.settings || {}) },
    daily: profile.daily || {},
  };
}

export function saveProfile(profile) {
  write("profile", profile);
}

// Library badges read case records without loading the cases.
export function caseStatus(entry) {
  const saved = read(caseKey(entry.id), null);
  if (!saved || saved.content_hash !== entry.content_hash) return null;
  if (saved.finished) return { solved: true, stars: saved.finished.stars };
  return saved.events?.length ? { solved: false } : null;
}

// A current entry can come from outside the library, such as the daily manifest.
export function nextCase(cases, currentOrId = null) {
  const currentId = typeof currentOrId === "string" ? currentOrId : currentOrId?.id ?? null;
  const currentIndex = cases.findIndex((entry) => entry.id === currentId);
  const current = currentOrId && typeof currentOrId === "object" ? currentOrId : cases[currentIndex];
  const statuses = new Map(cases.map((entry) => [entry.id, caseStatus(entry)]));
  const solvedHashes = new Set(
    cases.filter((entry) => statuses.get(entry.id)?.solved && entry.content_hash).map((entry) => entry.content_hash),
  );
  const ordered = currentIndex < 0 ? cases : [...cases.slice(currentIndex + 1), ...cases.slice(0, currentIndex)];
  const remaining = ordered.filter(
    (entry) => entry.id !== currentId && !statuses.get(entry.id)?.solved &&
      (!entry.content_hash || (entry.content_hash !== current?.content_hash && !solvedHashes.has(entry.content_hash))),
  );
  const generated = remaining.filter((entry) => entry.kind === "themed" || entry.kind === "generated");
  const candidates = generated.length ? generated : remaining.filter((entry) => entry.kind === "classic");
  if (currentId === null) {
    return candidates.find((entry) => statuses.get(entry.id)?.solved === false) || candidates[0] || null;
  }
  return candidates.find((entry) => !statuses.get(entry.id) && entry.setting?.id !== current?.setting?.id) || candidates[0] || null;
}
