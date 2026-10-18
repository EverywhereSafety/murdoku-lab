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

const root = process.env.MURDOKU_PLAY_ROOT ? path.resolve(process.env.MURDOKU_PLAY_ROOT) : path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../dist");
const prefix = process.env.MURDOKU_PLAY_PREFIX || "/murdoku/play/";
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
  page.setDefaultTimeout(15000);
  page.on("pageerror", (e) => errors.push(`${label}: ${e.message}`));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (/^https?:$/.test(url.protocol) && url.origin !== new URL(base).origin) foreign.push(url.href);
    if (url.pathname.includes("/api/")) api.push(url.pathname);
  });
}

// Two boxes overlap when they share any area; null boxes never do.
const overlap = (a, b) => Boolean(a && b && a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height);

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
  await page.getByLabel("Setting", { exact: true }).selectOption(bundle.meta.setting.id);
  assert.ok((await page.locator(".pl-card.is-solved").count()) >= 1, "the filtered library marks the solved case");
  checks.push("library records the solved case");

  await page.goto(`${base}?case=glasshouse`, { waitUntil: "networkidle" });
  await page.locator(".pl-tool", { hasText: "Hint" }).click();
  const nudge = await page.locator(".pl-hint p").textContent();
  assert.ok(!overlap(await page.locator(".pl-hint").boundingBox(), await page.locator(".pl-overlay").boundingBox()), "the hint card is not over the board");
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
    const board = await page.locator(".pl-overlay").boundingBox();
    for (const who of order) {
      const coached = page.locator(".pl-suspect.is-coached .pl-face");
      if (await coached.count()) await coached.first().click();
      assert.match(await page.locator(".pl-coach p").textContent(), new RegExp(tutorial.public.people.find((p) => p.id === who).name.split(" ")[0]));
      assert.ok(!overlap(await page.locator(".pl-coach").boundingBox(), board), "the coach card never covers the board");
      await page.mouse.click(...help.point(solve[who]));
      await page.locator(`.pl-token[data-person="${who}"]`).waitFor();
    }
    assert.match(await page.locator(".pl-coach p").textContent(), /Name the murderer|Close the case/);
    checks.push("the training case coaches every placement in deduction order, beside the board");
    await page.locator(".pl-accuse.is-ready").click();
    await page.locator(".pl-verdict .pl-lineup-card").first().waitFor();
    assert.ok(!overlap(await page.locator(".pl-verdict").boundingBox(), board), "the verdict panel leaves the board in view");
    checks.push("the verdict panel leaves the board in view");
    const suspects = tutorial.public.people.filter((p) => !p.victim).map((p) => p.id);
    await page.locator(".pl-lineup-card").nth(suspects.indexOf(unseal(tutorial.secret, tutorial.id).murderer)).click();
    await page.locator(".pl-reveal").waitFor();
    await page.locator(".pl-reveal button", { hasText: "Play again" }).click();
    await page.locator(".pl-coach .pl-primary", { hasText: "Let's start" }).waitFor();
    assert.equal(await page.locator(".pl-token").count(), 0, "playing again clears the board");
    await page.reload({ waitUntil: "networkidle" });
    assert.equal(await page.locator(".pl-token").count(), 0, "a fresh start survives a refresh");
    checks.push("a solved training case can be played again from the start");
  }
  // Regressions from the 24-person player review.
  await page.goto(`${base}?case=museum`, { waitUntil: "networkidle" });
  const museum = JSON.parse(fs.readFileSync(path.join(root, "cases/museum.json"), "utf8"));
  for (const person of museum.public.people.filter((p) => p.tags?.length)) {
    const card = page.locator(".pl-suspect").filter({ has: page.locator(".pl-badge", { hasText: new RegExp(`^${person.id}$`) }) });
    assert.equal(await card.locator(".pl-person-tags").textContent(), person.tags.join(" · "));
  }
  await page.keyboard.press("n");
  assert.equal(await page.locator(".pl-suspect.is-selected .pl-badge").textContent(), "N");
  assert.ok(!(await page.locator(".pl-overlay").getAttribute("class")).includes("is-notes"));
  await page.keyboard.press("Shift+n");
  await page.waitForFunction(() => document.querySelector(".pl-overlay.is-notes"));
  assert.equal(await page.locator(".pl-suspect.is-selected .pl-badge").textContent(), "N");
  checks.push("Museum: all public roles visible; N selects Nora and Shift+N toggles notes");

  await page.evaluate(() => {
    localStorage.removeItem("murdoku:v1:case:tutorial");
    localStorage.setItem("murdoku:v1:profile", JSON.stringify({ settings: { timer: true } }));
  });
  await page.goto(`${base}?case=tutorial`, { waitUntil: "networkidle" });
  const timerBefore = await page.locator(".pl-timer").textContent();
  await page.waitForFunction((before) => document.querySelector(".pl-timer")?.textContent !== before, timerBefore);
  await page.locator(".pl-tool", { hasText: /^Hint$/ }).click();
  await page.locator(".pl-hint:not(.pl-coach)").waitFor();
  assert.equal(await page.locator(".pl-coach").count(), 0);
  await page.locator(".pl-hint .pl-secondary").click();
  await page.locator(".pl-hint .pl-secondary").click();
  await page.locator(".pl-hint .pl-primary").click();
  await page.locator(".pl-coach").waitFor();
  assert.equal(await page.locator(".pl-token").count(), 1);
  const hints = await page.evaluate(() => JSON.parse(localStorage.getItem("murdoku:v1:case:tutorial")).hints);
  assert.deepEqual(hints.map((h) => h.level), [1, 2, 3]);
  checks.push("tutorial: hints display, escalate and place; coach returns; idle timer advances");
  await desktop.close();

  // -------------------------------------------------------------------- daily
  const manifestPath = path.join(root, "daily/manifest.json");
  if (fs.existsSync(manifestPath)) {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    const day = manifest.days[Math.min(3, manifest.days.length - 1)];
    const later = manifest.days.find((d) => d.date > day.date);
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    // Real local midnight updates both the library and an already-open locked route.
    const clockContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const rollover = await clockContext.newPage();
    watch(rollover, "midnight");
    const nextDay = manifest.days.find((d) => d.n === day.n + 1);
    if (nextDay) {
      await rollover.clock.install({ time: new Date(`${day.date}T23:59:59`) });
      await rollover.goto(base, { waitUntil: "networkidle" });
      await rollover.clock.pauseAt(new Date(`${day.date}T23:59:59.900`));
      await rollover.clock.runFor(2000);
      await rollover.waitForFunction((n) => document.querySelector(".pl-card.is-today .pl-card-setting")?.textContent.includes(`#${n} ·`), nextDay.n);
      assert.equal(await rollover.locator(`.pl-day[title^="#${nextDay.n} ·"]`).isEnabled(), true);
      await rollover.close();
      await clockContext.close();
      const lockedContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
      const lockedPage = await lockedContext.newPage();
      watch(lockedPage, "locked-midnight");
      await lockedPage.clock.install({ time: new Date(`${day.date}T23:59:58`) });
      await lockedPage.goto(`${base}?d=${nextDay.n}`, { waitUntil: "networkidle" });
      await lockedPage.locator(".pl-empty h2").waitFor();
      await lockedPage.clock.fastForward(4000);
      await lockedPage.locator(".pl-overlay").waitFor();
      await lockedContext.close();
      checks.push("midnight: today's card and calendar advance; an open future case unlocks without reload");
    } else await clockContext.close();
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    const daily = await context.newPage();
    watch(daily, "daily");
    await daily.goto(`${base}?date=${day.date}`, { waitUntil: "networkidle" });
    assert.match(await daily.locator(".pl-today-cta").textContent(), /today/i);
    checks.push(`daily: the library opens on today's case (#${day.n}) with a countdown and calendar`);

    const picker = daily.locator(".pl-daily-picker");
    const slider = picker.getByRole("slider", { name: "Choose a daily case" });
    const previousButton = picker.getByRole("button", { name: "Previous daily case" });
    const nextButton = picker.getByRole("button", { name: "Next daily case" });
    const todayButton = picker.getByRole("button", { name: "Today", exact: true });
    const selectedDaily = async (entry) => {
      await picker.locator(`time[datetime="${entry.date}"]`).waitFor();
      assert.equal(await picker.locator(".pl-card strong").textContent(), entry.title);
      assert.equal(await slider.inputValue(), String(manifest.days.indexOf(entry)));
      assert.ok((await slider.getAttribute("aria-valuetext")).includes(`#${entry.n} ·`));
    };
    await selectedDaily(day);
    assert.equal(await todayButton.isDisabled(), true);
    const previous = manifest.days[manifest.days.indexOf(day) - 1];
    if (previous) {
      await previousButton.click();
      await selectedDaily(previous);
      assert.equal(await picker.locator(".pl-card").isEnabled(), true);
      await nextButton.click();
      await selectedDaily(day);
      await previousButton.click();
      await selectedDaily(previous);
      await picker.locator(".pl-card").click();
      await daily.locator(".pl-overlay").waitFor();
      assert.equal(new URL(daily.url()).searchParams.get("d"), String(previous.n));
      assert.equal(new URL(daily.url()).searchParams.get("date"), day.date);
      await daily.goto(`${base}?date=${day.date}`, { waitUntil: "networkidle" });
      checks.push("daily picker: arrows switch the case and past dates open the selected puzzle");
    }

    if (manifest.days.length > 1) {
      await slider.press("Home");
      await selectedDaily(manifest.days[0]);
      assert.equal(await previousButton.isDisabled(), true);
      assert.equal(await picker.locator(".pl-card").isEnabled(), true);
      await slider.press("End");
      const last = manifest.days.at(-1);
      await selectedDaily(last);
      assert.equal(await nextButton.isDisabled(), true);
      assert.equal(await picker.locator(".pl-card").isDisabled(), last.date > day.date);
      if (last.date > day.date) assert.match(await slider.getAttribute("aria-valuetext"), /Locked/);
      assert.equal(new URL(daily.url()).searchParams.get("date"), day.date, "browsing future dates never changes the unlock date");
      if (last.date !== day.date) await todayButton.click();
      await selectedDaily(day);
      assert.equal(await todayButton.isDisabled(), true);
      assert.equal(await picker.locator(".pl-card").isEnabled(), true);
      checks.push("daily picker: slider reaches both season boundaries, future cases stay locked and Today resets the selection");
    }

    const adjacentDate = (date, offset) => new Date(Date.parse(`${date}T12:00:00Z`) + offset * 86400000).toISOString().slice(0, 10);
    for (const [date, entry, locked] of [
      [adjacentDate(manifest.days[0].date, -1), manifest.days[0], true],
      [adjacentDate(manifest.days.at(-1).date, 1), manifest.days.at(-1), false],
    ]) {
      await daily.goto(`${base}?date=${date}`, { waitUntil: "networkidle" });
      await selectedDaily(entry);
      assert.equal(await todayButton.isDisabled(), true);
      assert.equal(await picker.locator(".pl-card").isDisabled(), locked);
    }
    checks.push("daily picker: dates outside the season select its nearest boundary without inventing a today's case");
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
    await daily.locator(".pl-reveal").getByRole("button", { name: "Share", exact: true }).click();
    const shared = await daily.evaluate(() => navigator.clipboard.readText());
    assert.match(shared, new RegExp(`^Murdoku Daily #${day.n} · `));
    assert.match(shared, /🟩/);
    assert.ok(!/\b[a-p](?:1[0-6]|[1-9])\b/.test(shared.split("\n").slice(0, 3).join(" ")), "no coordinates in the share text");
    for (const p of sealed.public.people) assert.ok(!shared.includes(p.name), "no names in the share text");
    checks.push("daily: solving copies a spoiler-free share line (#n, tiles, verdict, stars)");
    await daily.locator(".pl-reveal").getByRole("button", { name: "Play another case", exact: true }).click();
    const nextId = new URL(daily.url()).searchParams.get("case");
    const following = JSON.parse(fs.readFileSync(path.join(root, "cases/index.json"), "utf8")).cases.find((entry) => entry.id === nextId);
    assert.equal(following?.kind, "themed", "the next case comes from the generated library");
    assert.notEqual(following.setting.id, day.setting.id, "the next case changes the daily's setting");
    await daily.getByRole("region", { name: following.title, exact: true }).locator(".pl-overlay").waitFor();
    checks.push("daily: Play another case opens a generated puzzle in a different setting");
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
  await mobile.goto(`${base}?case=museum`, { waitUntil: "networkidle" });
  await mobile.locator(".pl-tool", { hasText: "Clues" }).tap();
  await mobile.locator(".pl-sheet .pl-person-tags").first().waitFor();
  assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await mobile.goto(`${base}?case=tutorial`, { waitUntil: "networkidle" });
  await mobile.locator(".pl-tool", { hasText: /^Hint$/ }).tap();
  await mobile.locator(".pl-tray .pl-hint:not(.pl-coach)").waitFor();
  await mobile.locator(".pl-tray .pl-hint .pl-link").tap();
  await mobile.locator(".pl-tray .pl-coach").waitFor();
  checks.push("phone: Museum roles visible in clues; tutorial hints close back to the coach");
  await phone.close();

  assert.deepEqual(errors, [], "no page errors");
  assert.deepEqual(foreign, [], "no requests to other origins");
  assert.deepEqual(api, [], "the player never calls the Python API");
  console.log(JSON.stringify({ checks, passed: checks.length, browser_errors: errors, foreign_requests: foreign }, null, 1));
} finally {
  await browser.close();
  server.close();
}
