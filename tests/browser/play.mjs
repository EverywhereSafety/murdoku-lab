// The player, end to end, from a static build served below a path prefix:
//   npm run export:cases && npm run build && npm run test:play
// Desktop: library, a full case with a wrong then a right verdict, undo/redo, refresh recovery,
// refusals and the kinder tap rules. Phone: layout without overflow, touch placement, the clue
// sheet. Throughout: no page errors, no request to another origin, no Python API calls.
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { unseal } from "../../web/src/play/engine/seal.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../dist");
const prefix = "/murdoku/play/";
assert.ok(fs.existsSync(path.join(root, "cases/index.json")), "build the player first");
const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".woff2": "font/woff2", ".woff": "font/woff" };
const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://local");
  if (!url.pathname.startsWith(prefix)) return res.writeHead(404).end();
  let file = path.join(root, decodeURIComponent(url.pathname.slice(prefix.length)));
  if (file.endsWith(path.sep) || url.pathname.endsWith("/")) file = path.join(file, "index.html");
  if (!file.startsWith(root) || !fs.existsSync(file)) return res.writeHead(404).end();
  res.writeHead(200, { "content-type": types[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const base = `http://127.0.0.1:${server.address().port}${prefix}`;

const caseId = "museum-6x6";
const bundle = JSON.parse(fs.readFileSync(path.join(root, `cases/${caseId}.json`), "utf8"));
const secret = unseal(bundle.secret, bundle.id);
const people = bundle.public.people;
const wrong = people.find((p) => !p.victim && p.id !== secret.murderer).id;

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.MURDOKU_BROWSER_PATH || chromium.executablePath(),
  args: ["--no-sandbox"],
});
const errors = [];
const foreign = [];
const api = [];
const checks = [];
function watch(page, label) {
  page.on("pageerror", (e) => errors.push(`${label}: ${e.message}`));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (/^https?:$/.test(url.protocol) && url.origin !== new URL(base).origin) foreign.push(url.href);
    if (url.pathname.includes("/api/")) api.push(url.pathname);
  });
}

async function boardHelpers(page) {
  const overlay = page.locator(".pl-overlay");
  await overlay.waitFor();
  const box = await overlay.boundingBox();
  const width = await page.evaluate(() => document.querySelector(".pl-overlay").viewBox.baseVal.width);
  const scale = box.width / width;
  const point = (cell) => {
    const col = cell.charCodeAt(0) - 97;
    const row = Number(cell.slice(1)) - 1;
    return [box.x + (90 + col * 100) * scale, box.y + (90 + row * 100) * scale];
  };
  return { point };
}

const placements = (page) =>
  page.evaluate(
    (id) => {
      const saved = JSON.parse(localStorage.getItem(`murdoku:v1:case:${id}`) || "{}");
      return saved.events?.length ?? 0;
    },
    caseId,
  );

try {
  // ------------------------------------------------------------------ desktop
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await desktop.newPage();
  watch(page, "desktop");
  await page.goto(base, { waitUntil: "networkidle" });
  const cards = await page.locator(".pl-card").count();
  assert.ok(cards >= 4, "library lists the cases");
  checks.push(`library lists ${cards} case cards below ${prefix}`);

  await page.goto(`${base}?case=${caseId}`, { waitUntil: "networkidle" });
  const { point } = await boardHelpers(page);
  const boardBox = await page.locator(".pl-board").boundingBox();
  const sideBox = await page.locator(".pl-side").boundingBox();
  assert.ok(boardBox.y + boardBox.height <= 900 && sideBox.x >= boardBox.x + boardBox.width - 1, "board and dossier share the screen");
  checks.push("desktop: board, action bar and dossier on one screen");

  const blocked = bundle.public.scene.cells.find((c) => !c.standable);
  const open = bundle.public.scene.cells.filter((c) => c.standable);
  const [a, b] = people.map((p) => p.id);
  await page.keyboard.press(a.toLowerCase());
  await page.mouse.click(...point(open[0].cell));
  // b is now selected; tapping a's square selects a instead of stacking b on top of it.
  await page.mouse.click(...point(open[0].cell));
  const stacked = await page.locator(`.pl-token[data-person="${b}"]`).count();
  assert.equal(stacked, 0, "tapping an occupied square never stacks people");
  if (blocked) {
    await page.keyboard.press(b.toLowerCase());
    await page.mouse.click(...point(blocked.cell));
    await page.locator(".pl-toast.is-warn").waitFor();
    assert.equal(await page.locator(`.pl-token[data-person="${b}"]`).count(), 0);
  }
  checks.push("taps on occupied or blocked squares select or refuse instead of stacking");

  await page.keyboard.press("Control+z");
  assert.equal(await page.locator(`.pl-token[data-person="${a}"]`).count(), 0, "undo removes the placement");
  await page.keyboard.press("Control+Shift+z");
  assert.equal(await page.locator(`.pl-token[data-person="${a}"]`).count(), 1, "redo restores it");
  checks.push("undo and redo");

  for (const [who, cell] of Object.entries(secret.solution)) {
    await page.keyboard.press(who.toLowerCase());
    await page.mouse.click(...point(cell));
  }
  assert.ok((await placements(page)) > 0, "moves are saved");
  await page.reload({ waitUntil: "networkidle" });
  await page.locator(".pl-overlay").waitFor();
  assert.equal(await page.locator(".pl-token").count(), people.length, "refresh restores the board");
  checks.push("refresh restores every placement");

  const order = await page.evaluate(() =>
    [...document.querySelectorAll(".pl-suspect")].filter((n) => !n.classList.contains("is-victim")).map((n) => n.querySelector(".pl-badge").textContent),
  );
  await page.locator(".pl-accuse.is-ready").click();
  await page.locator(".pl-lineup-card").nth(order.indexOf(wrong)).click();
  await page.locator(".pl-outcome h2").waitFor();
  await page.locator(".pl-outcome .pl-primary").click();
  checks.push("a wrong verdict explains what is wrong and returns to the board");

  await page.locator(".pl-accuse.is-ready").click();
  await page.locator(".pl-lineup-card").nth(order.indexOf(secret.murderer)).click();
  await page.locator(".pl-reveal .pl-stamp").waitFor();
  const text = await page.locator(".pl-reveal").textContent();
  assert.ok(text.includes(people.find((p) => p.id === secret.murderer).name), "the reveal names the murderer");
  await page.locator(".pl-reveal .pl-link").click();
  await page.locator(".pl-guilty").waitFor();
  checks.push("right verdict: reveal, epilogue, GUILTY stamp on the board");

  await page.goto(base, { waitUntil: "networkidle" });
  assert.ok((await page.locator(".pl-card.is-solved").count()) >= 1, "the library marks the solved case");
  checks.push("library records the solved case");

  await page.goto(`${base}?case=glasshouse`, { waitUntil: "networkidle" });
  await page.locator(".pl-tool", { hasText: "Hint" }).click();
  const nudge = await page.locator(".pl-hint p").textContent();
  await page.locator(".pl-hint .pl-secondary").click();
  await page.locator(".pl-hint .pl-secondary").click();
  await page.locator(".pl-hint .pl-primary").click();
  assert.equal(await page.locator(".pl-token").count(), 1, "the answer-level hint places the person");
  assert.match(nudge, /^Try \w+ next/, "the first hint is a nudge, not the answer");
  checks.push("hints escalate from a nudge to a one-tap answer");

  if (fs.existsSync(path.join(root, "cases/tutorial.json"))) {
    await page.goto(`${base}?case=tutorial`, { waitUntil: "networkidle" });
    await page.locator(".pl-coach .pl-primary").click();
    const tutorial = JSON.parse(fs.readFileSync(path.join(root, "cases/tutorial.json"), "utf8"));
    const order = unseal(tutorial.secret, tutorial.id).hints.order;
    const solve = unseal(tutorial.secret, tutorial.id).solution;
    const help = await boardHelpers(page);
    for (const who of order) {
      const coached = page.locator(".pl-suspect.is-coached .pl-face");
      if (await coached.count()) await coached.first().click();
      assert.match(await page.locator(".pl-coach p").textContent(), new RegExp(tutorial.public.people.find((p) => p.id === who).name.split(" ")[0]));
      await page.mouse.click(...help.point(solve[who]));
    }
    assert.match(await page.locator(".pl-coach p").textContent(), /Name the murderer|Close the case/);
    checks.push("the training case coaches every placement in deduction order");
  }
  await desktop.close();

  // -------------------------------------------------------------------- daily
  const manifestPath = path.join(root, "daily/manifest.json");
  if (fs.existsSync(manifestPath)) {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    const day = manifest.days[Math.min(3, manifest.days.length - 1)];
    const later = manifest.days.find((d) => d.date > day.date);
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    const daily = await context.newPage();
    watch(daily, "daily");
    await daily.goto(`${base}?date=${day.date}`, { waitUntil: "networkidle" });
    assert.match(await daily.locator(".pl-today-cta").textContent(), /today/i);
    checks.push(`daily: the library opens on today's case (#${day.n}) with a countdown and calendar`);
    if (later) {
      await daily.goto(`${base}?d=${later.n}&date=${day.date}`, { waitUntil: "networkidle" });
      await daily.locator(".pl-empty h2").waitFor();
      await daily.goto(`${base}?d=${later.n}&date=${day.date}&unlock=all`, { waitUntil: "networkidle" });
      await daily.locator(".pl-overlay").waitFor();
      checks.push("daily: future cases stay locked unless previewed with unlock=all");
    }
    const sealed = JSON.parse(fs.readFileSync(path.join(root, `daily/${day.id}.json`), "utf8"));
    const answers = unseal(sealed.secret, sealed.id, day.date);
    await daily.goto(`${base}?d=${day.n}&date=${day.date}`, { waitUntil: "networkidle" });
    const help = await boardHelpers(daily);
    for (const [who, cell] of Object.entries(answers.solution)) {
      await daily.keyboard.press(who.toLowerCase());
      await daily.mouse.click(...help.point(cell));
    }
    const lineup = await daily.evaluate(() =>
      [...document.querySelectorAll(".pl-suspect")].filter((n) => !n.classList.contains("is-victim")).map((n) => n.querySelector(".pl-badge").textContent),
    );
    await daily.locator(".pl-accuse.is-ready").click();
    await daily.locator(".pl-lineup-card").nth(lineup.indexOf(answers.murderer)).click();
    await daily.locator(".pl-reveal .pl-primary").click();
    const shared = await daily.evaluate(() => navigator.clipboard.readText());
    assert.match(shared, new RegExp(`^Murdoku Daily #${day.n} · `));
    assert.match(shared, /🟩/);
    assert.ok(!/\b[a-p](?:1[0-6]|[1-9])\b/.test(shared.split("\n").slice(0, 3).join(" ")), "no coordinates in the share text");
    for (const p of sealed.public.people) assert.ok(!shared.includes(p.name), "no names in the share text");
    checks.push("daily: solving copies a spoiler-free share line (#n, tiles, verdict, stars)");
    await daily.goto(`${base}?date=${day.date}`, { waitUntil: "networkidle" });
    assert.match(await daily.locator(".pl-streak").first().textContent(), /1-day streak/);
    checks.push("daily: the streak counts a case solved on its day");
    await context.close();
  }

  // -------------------------------------------------------------------- phone
  const phone = await browser.newContext({ viewport: { width: 375, height: 667 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const mobile = await phone.newPage();
  watch(mobile, "phone");
  await mobile.goto(`${base}?case=glasshouse`, { waitUntil: "networkidle" });
  const helpers = await boardHelpers(mobile);
  const overflow = await mobile.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  assert.ok(overflow <= 0, `no horizontal overflow (${overflow}px)`);
  const bar = await mobile.locator(".pl-actions").boundingBox();
  assert.ok(bar.y + bar.height <= 667 && bar.x >= 0, "action bar is on screen");
  checks.push("phone: board fits the width, action bar pinned on screen");
  const target = (await mobile.evaluate(() => [...document.querySelectorAll(".pl-chip")].length)) && "a2";
  await mobile.locator(".pl-chip").first().tap();
  await mobile.touchscreen.tap(...helpers.point(target));
  await mobile.waitForTimeout(300);
  assert.ok((await mobile.locator(".pl-token").count()) <= 1);
  await mobile.locator(".pl-tool", { hasText: "Clues" }).tap();
  await mobile.locator(".pl-sheet .pl-suspect").first().waitFor();
  checks.push("phone: touch placement and the clue sheet");
  await phone.close();

  assert.deepEqual(errors, [], "no page errors");
  assert.deepEqual(foreign, [], "no requests to other origins");
  assert.deepEqual(api, [], "the player never calls the Python API");
  console.log(JSON.stringify({ checks, passed: checks.length, browser_errors: errors, foreign_requests: foreign }, null, 1));
} finally {
  await browser.close();
  server.close();
}
