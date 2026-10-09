// Reproduce DSW: serve the app only under a workspace/port prefix and reject
// escaped /assets, /api or /favicon requests at the gateway root with HTTP 400.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import http from "node:http";
import { chromium } from "playwright";

const upstream = new URL(
  process.env.MURDOKU_TEST_URL || "http://127.0.0.1:8765/",
);
const mounts = [
  "/dsw-test/workspaces/example/proxy/8765/",
  "/dsw-test/workspaces/another/proxy/8765/",
];
const escaped = [];
const requests = [];
const errors = [];
const checks = [];
const proxy = http.createServer((req, res) => {
  const url = new URL(req.url, "http://proxy.test");
  const mount = mounts.find((prefix) => url.pathname.startsWith(prefix));
  if (!mount) {
    escaped.push(url.pathname);
    res.writeHead(400, { "Content-Type": "text/plain" });
    res.end("DSW-style gateway: request escaped the workspace port prefix");
    return;
  }
  requests.push({ method: req.method, path: url.pathname });
  const forwarded = http.request(
    {
      hostname: upstream.hostname,
      port: upstream.port,
      path: "/" + url.pathname.slice(mount.length) + url.search,
      method: req.method,
      headers: { ...req.headers, host: upstream.host },
    },
    (response) => {
      res.writeHead(response.statusCode, response.headers);
      response.pipe(res);
    },
  );
  forwarded.on("error", () => {
    if (!res.headersSent) res.writeHead(502);
    res.end("Test upstream unavailable");
  });
  req.pipe(forwarded);
});

await new Promise((resolve) => proxy.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${proxy.address().port}`;
let browser;
try {
  browser = await chromium.launch({
    executablePath:
      process.env.MURDOKU_BROWSER_PATH || chromium.executablePath(),
    headless: true,
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1120 },
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.url().startsWith(origin) && response.status() >= 400)
      errors.push(
        `HTTP ${response.status()} ${new URL(response.url()).pathname}`,
      );
  });
  await page.goto(origin + mounts[0], { waitUntil: "networkidle" });
  await page.locator('[data-cell="b1"]').waitFor();
  assert.equal(await page.locator("[data-cell]").count(), 36);
  const staticUrls = await page.evaluate(() => [
    ...[...document.querySelectorAll("script[src]")].map((el) => el.src),
    ...[
      ...document.querySelectorAll('link[rel="stylesheet"],link[rel="icon"]'),
    ].map((el) => el.href),
  ]);
  assert(
    staticUrls.length >= 3 &&
      staticUrls.every((url) => url.startsWith(origin + mounts[0])),
  );
  await page.waitForFunction(() => {
    const images = [...document.querySelectorAll(".portrait-wrap img")];
    return (
      images.length === 6 &&
      images.every((img) => img.complete && img.naturalWidth > 0)
    );
  });
  checks.push(
    "JS, CSS, favicon, board and portraits load below the DSW prefix",
  );

  const initial = await page.evaluate(() => window.murdokuAgent.observe());
  await page.getByRole("button", { name: "Select Ada", exact: true }).click();
  await page
    .getByRole("button", { name: "Place person (P)", exact: true })
    .click();
  await page.locator('[data-cell="b1"]').click();
  await page.waitForFunction(
    () => document.querySelector(".scene-svg")?.dataset.revision === "1",
  );
  assert.deepEqual(
    (await page.evaluate(() => window.murdokuAgent.observe())).placements,
    { A: "b1" },
  );
  await page.getByRole("button", { name: "Diagram", exact: true }).click();
  await page.waitForFunction(
    () => document.querySelector(".scene-svg")?.dataset.style === "diagram",
  );
  await page.getByRole("button", { name: "Illustrated", exact: true }).click();
  checks.push(
    "tool actions, JSON observations and both SVG views use the prefix",
  );

  await page
    .getByRole("button", { name: "Open object and terrain key", exact: true })
    .click();
  await page.waitForFunction(() => {
    const images = [...document.querySelectorAll(".object-key img")];
    return (
      images.length > 0 &&
      images.every((img) => img.complete && img.naturalWidth > 0)
    );
  });
  await page
    .getByRole("button", { name: "Close dialog", exact: true })
    .filter({ visible: true })
    .click();
  checks.push("object illustrations resolve below the prefix");

  await page
    .getByRole("button", { name: "For developers", exact: true })
    .click();
  const downloadReady = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Observation PNG", exact: true })
    .click();
  const download = await downloadReady;
  await download.saveAs("artifacts/dsw-proxy-observation.png");
  await page
    .getByRole("button", { name: "Close dialog", exact: true })
    .filter({ visible: true })
    .click();
  checks.push("PNG export fetches the full observation through the proxy");

  await page.reload({ waitUntil: "networkidle" });
  const resumed = await page.evaluate(() => window.murdokuAgent.observe());
  assert.equal(resumed.session_id, initial.session_id);
  assert.deepEqual(resumed.placements, { A: "b1" });
  await page.screenshot({
    path: "artifacts/dsw-proxy-preview.png",
    fullPage: true,
  });
  checks.push("refresh restores the session within its mount path");

  await page.goto(origin + mounts[1] + "index.html", {
    waitUntil: "networkidle",
  });
  await page.locator('[data-cell="b1"]').waitFor();
  const separate = await page.evaluate(() => window.murdokuAgent.observe());
  assert.notEqual(separate.session_id, initial.session_id);
  assert.deepEqual(separate.placements, {});
  checks.push(
    "index.html entry works; two gateway paths do not share a saved session",
  );

  // Query galleries are dataset outputs. Opt in when the server has a supplied bundle.
  const reviewCount = Number(process.env.MURDOKU_TEST_REVIEW_COUNT || 0);
  await page
    .getByRole("button", { name: "For developers", exact: true })
    .click();
  const reviewLink = page.getByRole("link", {
    name: "Review generated samples",
  });
  assert.equal(await reviewLink.count(), 1);
  if (reviewCount > 0) {
    await reviewLink.click();
    await page.locator("details.case").first().waitFor();
    assert.equal(await page.locator("details.case").count(), reviewCount);
    await page.waitForFunction(() => {
      const image = document.querySelector("details.case[open] img");
      return image?.complete && image.naturalWidth > 0;
    });
    const previewLink = page.locator("details.case").first().locator("a.play");
    const previewCase = new URL(
      await previewLink.getAttribute("href"),
      page.url(),
    ).searchParams.get("case");
    await previewLink.click();
    await page.locator('[data-cell="a1"]').waitFor();
    const generated = await page.evaluate(() => window.murdokuAgent.observe());
    assert.equal(generated.case_id, previewCase);
    assert(!("solution" in generated) && !("answer_key" in generated));
    checks.push(
      "supplied query gallery and interactive case links preserve the proxy prefix",
    );
  }

  assert.deepEqual(escaped, []);
  assert.deepEqual(errors, []);
  const receipt = {
    checks,
    passed: checks.length,
    requests: requests.length,
    escaped_root_requests: escaped,
    browser_errors: errors,
    verification:
      "Local DSW-style path-prefix proxy; no live gateway credentials used",
  };
  await fs.writeFile(
    "artifacts/dsw-proxy-verification.json",
    JSON.stringify(receipt, null, 2) + "\n",
  );
  console.log(JSON.stringify(receipt));
} finally {
  if (browser) await browser.close();
  proxy.closeAllConnections();
  await new Promise((resolve) => proxy.close(resolve));
}
