"""`murdoku.seal/1`: keep a case's answers out of plain sight in a static bundle.

The player app ships every case as a static file, so anyone determined can read its answers;
the seal only stops an accidental spoiler (a glance at the network panel, a search engine
snippet). JSON is XORed with a mulberry32 keystream seeded by FNV-1a over `"<id>|<salt>"`, then
base64-encoded. web/src/play/engine/seal.js implements the same steps, and both are pinned by
tests/fixtures/seal_vectors.json.
"""

import base64
import json

ALG = "murdoku.seal/1"
MASK = 0xFFFFFFFF


def fnv1a(text):
    h = 0x811C9DC5
    for byte in text.encode():
        h = ((h ^ byte) * 0x01000193) & MASK
    return h


def mulberry32(seed):
    a = seed & MASK
    while True:
        a = (a + 0x6D2B79F5) & MASK
        t = ((a ^ (a >> 15)) * (a | 1)) & MASK
        t = ((t + (((t ^ (t >> 7)) * (t | 61)) & MASK)) & MASK) ^ t
        yield (t ^ (t >> 14)) & MASK


def _xor(data, key):
    stream = mulberry32(fnv1a(key))
    return bytes(b ^ (next(stream) & 0xFF) for b in data)


def seal(value, case_id, salt=""):
    plain = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    data = _xor(plain.encode(), f"{case_id}|{salt}")
    return {"alg": ALG, "data": base64.b64encode(data).decode()}


def unseal(sealed, case_id, salt=""):
    if sealed.get("alg") != ALG:
        raise ValueError(f"unknown seal {sealed.get('alg')!r}")
    data = _xor(base64.b64decode(sealed["data"]), f"{case_id}|{salt}")
    return json.loads(data.decode())
