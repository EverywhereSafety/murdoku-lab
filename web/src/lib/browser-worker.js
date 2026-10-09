// The Python engine runs off the UI thread; no gameplay requests leave the browser.
// GitHub Pages does not compress WASM automatically. Stream a precompressed
// copy through the browser decompressor while keeping Pyodide itself unchanged.
const fetchAsset = globalThis.fetch.bind(globalThis);
if (typeof DecompressionStream !== "undefined") {
  globalThis.fetch = async (input, options) => {
    const url = new URL(
      input instanceof Request ? input.url : input,
      import.meta.url,
    );
    if (!url.pathname.endsWith("/python/pyodide.asm.wasm"))
      return fetchAsset(input, options);
    const response = await fetchAsset(url.href + ".gz", options);
    if (!response.ok)
      throw new Error("Could not load the casebook. Please reload to retry.");
    return new Response(
      response.body.pipeThrough(new DecompressionStream("gzip")),
      {
        headers: { "Content-Type": "application/wasm" },
      },
    );
  };
}
const ready = (async () => {
  const runtimeURL = new URL(/* @vite-ignore */ "../python/", import.meta.url)
    .href;
  const { loadPyodide } = await import(
    /* @vite-ignore */ runtimeURL + "pyodide.mjs"
  );
  let timer;
  const python = await Promise.race([
    loadPyodide({ indexURL: runtimeURL }),
    new Promise((_, reject) => {
      timer = setTimeout(
        () =>
          reject(
            new Error(
              "The casebook took too long to load. Please reload to retry.",
            ),
          ),
        120000,
      );
    }),
  ]).finally(() => clearTimeout(timer));
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
