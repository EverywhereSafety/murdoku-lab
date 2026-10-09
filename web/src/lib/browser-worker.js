// The Python engine runs off the UI thread; no gameplay requests leave the browser.
// GitHub Pages does not compress WASM automatically. Stream a precompressed
// copy through the browser decompressor while keeping Pyodide itself unchanged.
const fetchAsset = globalThis.fetch.bind(globalThis);
const runtimeCache = "murdoku-python-314.0.7";
let downloaded = 0;
const report = (stage) => self.postMessage({ loading: stage });
async function cachedAsset(input, options) {
  const url = new URL(
    input instanceof Request ? input.url : input,
    import.meta.url,
  );
  let cache;
  try {
    cache = await caches.open(runtimeCache);
    const saved = await cache.match(url.href);
    if (saved) return saved;
  } catch {}
  const response = await fetchAsset(input, options);
  if (!response.ok)
    throw new Error(
      "Could not download the puzzle engine. Please reload to retry.",
    );
  // Only immutable runtime files belong in this cache; game code updates normally.
  if (cache && url.pathname.includes("/python/")) {
    cache.put(url.href, response.clone()).catch(() => {});
  }
  let lastReport = 0;
  const body = response.body.pipeThrough(
    new TransformStream({
      transform(chunk, controller) {
        downloaded += chunk.byteLength;
        if (performance.now() - lastReport > 150) {
          report(
            `Downloading puzzle engine · ${(downloaded / 1048576).toFixed(1)} MB`,
          );
          lastReport = performance.now();
        }
        controller.enqueue(chunk);
      },
    }),
  );
  return new Response(body, { headers: response.headers });
}
globalThis.fetch = async (input, options) => {
  const url = new URL(
    input instanceof Request ? input.url : input,
    import.meta.url,
  );
  if (!url.pathname.includes("/python/")) return fetchAsset(input, options);
  const compressed =
    typeof DecompressionStream !== "undefined" &&
    /\/pyodide\.asm\.(wasm|mjs)$/.test(url.pathname);
  const response = await cachedAsset(
    compressed ? url.href + ".gz" : input,
    options,
  );
  if (!compressed) return response;
  return new Response(
    response.body.pipeThrough(new DecompressionStream("gzip")),
    {
      headers: {
        "Content-Type": url.pathname.endsWith(".wasm")
          ? "application/wasm"
          : "text/javascript",
      },
    },
  );
};
const ready = (async () => {
  const runtimeURL = new URL(/* @vite-ignore */ "../python/", import.meta.url)
    .href;
  report("Loading puzzle engine…");
  const engine = fetch(
    new URL(/* @vite-ignore */ "../browser-engine.zip", import.meta.url),
  );
  const moduleReady = (async () => {
    const response = await fetch(runtimeURL + "pyodide.asm.mjs");
    const blob = new Blob([await response.text()], { type: "text/javascript" });
    const url = URL.createObjectURL(blob);
    try {
      return (await import(/* @vite-ignore */ url)).default;
    } finally {
      URL.revokeObjectURL(url);
    }
  })();
  const { loadPyodide } = await import(
    /* @vite-ignore */ runtimeURL + "pyodide.mjs"
  );
  let timer;
  const python = await Promise.race([
    moduleReady.then((createPyodideModule) =>
      loadPyodide({ indexURL: runtimeURL, createPyodideModule }),
    ),
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
  report("Preparing the board…");
  const response = await engine;
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
