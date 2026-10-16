// murdoku.seal/1 — the same steps as murdoku_lab/visual/seal.py, pinned by
// tests/fixtures/seal_vectors.json. It keeps answers out of plain sight; it is not security.

export const ALG = "murdoku.seal/1";

export function fnv1a(text) {
  let h = 0x811c9dc5;
  for (const byte of new TextEncoder().encode(text)) {
    h = Math.imul(h ^ byte, 0x01000193) >>> 0;
  }
  return h;
}

export function* mulberry32(seed) {
  let a = seed >>> 0;
  while (true) {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), a | 1) >>> 0;
    t = ((((t + (Math.imul(t ^ (t >>> 7), t | 61) >>> 0)) >>> 0) ^ t) >>> 0);
    yield (t ^ (t >>> 14)) >>> 0;
  }
}

function xor(bytes, key) {
  const stream = mulberry32(fnv1a(key));
  const out = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i += 1) {
    out[i] = bytes[i] ^ (stream.next().value & 0xff);
  }
  return out;
}

// JSON with sorted keys and no spaces, like Python's json.dumps(sort_keys=True, separators).
export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalJson(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export function seal(value, id, salt = "") {
  const data = xor(new TextEncoder().encode(canonicalJson(value)), `${id}|${salt}`);
  let binary = "";
  for (const byte of data) binary += String.fromCharCode(byte);
  return { alg: ALG, data: btoa(binary) };
}

export function unseal(sealed, id, salt = "") {
  if (!sealed || sealed.alg !== ALG) throw new Error("Unknown case seal.");
  const raw = Uint8Array.from(atob(sealed.data), (c) => c.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(xor(raw, `${id}|${salt}`)));
}
