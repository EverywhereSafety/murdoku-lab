import { sessionStorageKey } from "../urls.js";

let worker;
let nextId = 0;
const pending = new Map();
const progressKey = `${sessionStorageKey}:progress`;
let restore;
try {
  restore = JSON.parse(localStorage.getItem(progressKey));
} catch {}

export function browserRequest(path, body) {
  if (!worker) {
    worker = new Worker(new URL("./browser-worker.js", import.meta.url), {
      type: "module",
    });
    worker.onmessage = ({ data }) => {
      if (data.loading) {
        window.dispatchEvent(
          new CustomEvent("murdoku-loading", { detail: data.loading }),
        );
        return;
      }
      const task = pending.get(data.id);
      if (!task) return;
      pending.delete(data.id);
      if (data.error) return task.reject(new Error(data.error));
      if (data.saved) {
        try {
          localStorage.setItem(progressKey, JSON.stringify(data.saved));
        } catch {}
      }
      task.resolve(data.result);
    };
    worker.onerror = () => {
      for (const task of pending.values())
        task.reject(
          new Error("Puzzle engine failed to load. Please reload to retry."),
        );
      pending.clear();
    };
  }
  const request = { path, body, restore };
  restore = null;
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, request });
  });
}
