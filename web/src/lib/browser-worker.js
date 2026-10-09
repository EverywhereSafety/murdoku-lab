// The Python engine runs off the UI thread; no gameplay requests leave the browser.
const ready = (async () => {
  const { loadPyodide } = await import(
    /* @vite-ignore */ "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs"
  );
  const python = await loadPyodide();
  const response = await fetch(
    new URL(/* @vite-ignore */ "../browser-engine.zip", import.meta.url),
  );
  if (!response.ok) throw new Error("Could not load the puzzle engine.");
  python.unpackArchive(await response.arrayBuffer(), "zip");
  python.runPython(
    "from murdoku_lab.visual.browser import BrowserGame, dispatch\ngame = BrowserGame()",
  );
  return python;
})();
let queue = Promise.resolve();
self.onmessage = ({ data }) => {
  queue = queue.then(async () => {
    try {
      const python = await ready;
      python.globals.set("request_json", JSON.stringify(data.request));
      const result = JSON.parse(
        python.runPython("dispatch(game, request_json)"),
      );
      self.postMessage({ id: data.id, ...result });
    } catch (error) {
      self.postMessage({ id: data.id, error: error.message });
    }
  });
};
