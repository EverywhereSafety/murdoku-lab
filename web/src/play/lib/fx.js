// Small feedback effects. Sound and vibration are off until the player turns them on, and
// motion respects prefers-reduced-motion (see play.css).
let audio = null;

function context() {
  if (!audio) {
    const Ctor = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!Ctor) return null;
    audio = new Ctor();
  }
  if (audio.state === "suspended") audio.resume();
  return audio;
}

function tone(ctx, { freq, to = freq, start = 0, length = 0.08, type = "sine", gain = 0.12 }) {
  const t0 = ctx.currentTime + start;
  const osc = ctx.createOscillator();
  const amp = ctx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t0);
  osc.frequency.exponentialRampToValueAtTime(Math.max(40, to), t0 + length);
  amp.gain.setValueAtTime(0.0001, t0);
  amp.gain.exponentialRampToValueAtTime(gain, t0 + 0.01);
  amp.gain.exponentialRampToValueAtTime(0.0001, t0 + length);
  osc.connect(amp).connect(ctx.destination);
  osc.start(t0);
  osc.stop(t0 + length + 0.02);
}

const SOUNDS = {
  place: [{ freq: 660, to: 420, length: 0.07, type: "triangle" }],
  pickup: [{ freq: 380, to: 520, length: 0.06, type: "triangle", gain: 0.08 }],
  note: [{ freq: 1180, to: 1000, length: 0.035, type: "sine", gain: 0.05 }],
  reject: [
    { freq: 200, length: 0.09, type: "square", gain: 0.05 },
    { freq: 160, start: 0.1, length: 0.11, type: "square", gain: 0.05 },
  ],
  wrong: [
    { freq: 330, to: 300, length: 0.16, type: "triangle" },
    { freq: 262, to: 240, start: 0.17, length: 0.24, type: "triangle" },
  ],
  solved: [
    { freq: 523, length: 0.12, type: "triangle" },
    { freq: 659, start: 0.11, length: 0.12, type: "triangle" },
    { freq: 784, start: 0.22, length: 0.14, type: "triangle" },
    { freq: 1047, start: 0.34, length: 0.32, type: "triangle", gain: 0.1 },
  ],
};

const VIBRATIONS = { place: 8, pickup: 6, note: 4, reject: [18, 40, 18], wrong: [30, 60, 30], solved: [20, 40, 20, 40, 60] };

export function feedback(kind, settings) {
  if (settings?.sound) {
    const ctx = context();
    if (ctx) for (const part of SOUNDS[kind] || []) tone(ctx, part);
  }
  if (settings?.haptics && navigator.vibrate) navigator.vibrate(VIBRATIONS[kind] || 0);
}

export function reducedMotion() {
  return globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}
