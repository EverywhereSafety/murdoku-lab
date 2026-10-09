import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { chromium } from "playwright";

const base = process.env.MURDOKU_TEST_URL || "http://127.0.0.1:8765";
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.MURDOKU_BROWSER_PATH || chromium.executablePath(),
  args: ["--no-sandbox"],
});
const errors = [];
const externalRequests = [];
const trackExternalRequests = (context) =>
  context.on("request", (request) => {
    const url = new URL(request.url());
    if (/^https?:$/.test(url.protocol) && url.origin !== new URL(base).origin)
      externalRequests.push(url.href);
  });
const checks = [];
const context = await browser.newContext({
  viewport: { width: 1440, height: 1120 },
  deviceScaleFactor: 1,
});
trackExternalRequests(context);
const page = await context.newPage();
page.setDefaultNavigationTimeout(120000);
page.setDefaultTimeout(120000);
page.on("pageerror", (e) => errors.push(e.message));
page.on("response", (r) => {
  if (r.url().startsWith(base) && r.status() >= 400)
    errors.push(`HTTP ${r.status()} ${new URL(r.url()).pathname}`);
});
const state = () => page.evaluate(() => window.murdokuAgent.observe());
async function revision(n) {
  await page.waitForFunction(
    (n) => document.querySelector(".scene-svg")?.dataset.revision === String(n),
    n,
  );
}
async function action(args, note) {
  const result = await page.evaluate(
    ({ args, note }) => window.murdokuAgent.act(args, note),
    { args, note },
  );
  await revision(result.observation.revision);
  return result;
}
try {
  await page.goto(base, { waitUntil: "networkidle" });
  await page.locator('[data-cell="b1"]').waitFor();
  assert.equal(await page.locator("[data-cell]").count(), 36);
  await page.screenshot({ path: "artifacts/desktop.png", fullPage: true });
  checks.push("desktop initial render");

  await page.locator('[data-cell="b1"]').click();
  await revision(1);
  assert.deepEqual((await state()).marks.A, ["b1"]);
  assert.deepEqual((await state()).placements, {});
  await page.locator('[data-cell="b1"]').focus();
  await page.keyboard.press("Space");
  await revision(2);
  assert.equal((await state()).placements.A, "b1");
  await page.locator('[data-cell="c2"]').hover();
  await page.mouse.down();
  await page.waitForTimeout(550);
  await page.mouse.up();
  await revision(3);
  await page.waitForTimeout(200);
  assert.equal((await state()).revision, 3);
  assert.equal((await state()).placements.A, "c2");
  await page
    .getByRole("button", { name: "Focus on the board", exact: true })
    .click();
  assert(await page.locator(".workspace.play-focus").isVisible());
  await page
    .getByRole("button", { name: "Open object and terrain key", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Close dialog", exact: true })
    .filter({ visible: true })
    .click();
  await page.keyboard.press("Escape");
  assert.equal(await page.locator(".workspace.play-focus").count(), 0);
  assert.equal(await page.evaluate(() => document.body.style.overflow), "");
  checks.push("candidate-first / Space and hold confirmation / focused board");
  await page.evaluate(() => window.murdokuAgent.newSession("glasshouse"));
  await revision(0);
  await page
    .getByRole("button", { name: "Place person (P)", exact: true })
    .click();

  await page.getByRole("button", { name: "Select Ada", exact: true }).click();
  await page.locator('[data-cell="b1"]').click();
  await revision(1);
  assert.deepEqual((await state()).placements, { A: "b1" });
  await page
    .getByRole("button", { name: "Undo (Ctrl+Z)", exact: true })
    .click();
  await revision(2);
  assert.deepEqual((await state()).placements, {});
  await page
    .getByRole("button", { name: "Redo (Ctrl+Shift+Z)", exact: true })
    .click();
  await revision(3);
  assert.deepEqual((await state()).placements, { A: "b1" });
  checks.push("click placement / undo / redo");
  await page
    .getByRole("button", { name: "Open the casebook", exact: true })
    .click();
  await page.locator(".case-card.current").click();
  assert.equal((await state()).revision, 3);
  assert.equal((await state()).placements.A, "b1");
  checks.push("return to current case without losing progress");

  await page.getByRole("button", { name: "Select Basil", exact: true }).click();
  await page
    .getByRole("button", { name: "Pencil candidates (M)", exact: true })
    .click();
  await page.locator('[data-cell="e3"]').click();
  await revision(4);
  assert.deepEqual((await state()).marks.B, ["e3"]);
  await page.locator('[data-cell="e3"]').click();
  await revision(5);
  assert.deepEqual((await state()).marks.B, []);
  await page
    .getByRole("button", { name: "Place person (P)", exact: true })
    .click();
  await page.locator('[data-cell="e3"]').focus();
  await page.keyboard.press("Enter");
  await revision(6);
  assert.equal((await state()).placements.B, "e3");
  await page.waitForFunction(
    () => document.activeElement?.dataset.cell === "e3",
  );
  await page.keyboard.press("ArrowDown");
  assert.equal(
    await page.evaluate(() => document.activeElement?.dataset.cell),
    "e4",
  );
  checks.push("pencil toggle / keyboard placement");

  await page
    .getByRole("button", { name: "Mark clue 1 reviewed", exact: true })
    .click();
  await revision(7);
  assert.equal((await state()).clues[0].reviewed, true);
  await page.getByRole("button", { name: "Diagram", exact: true }).click();
  await page.waitForFunction(
    () => document.querySelector(".scene-svg")?.dataset.style === "diagram",
  );
  await page.screenshot({ path: "artifacts/diagram.png", fullPage: true });
  await page.getByRole("button", { name: "Illustrated", exact: true }).click();
  checks.push("personal clue checklist / both render styles");

  await action({ action: "place", person: "C", cell: "a1" });
  const checked = await action({ action: "check" });
  assert(checked.result.observations.join(" ").includes("cannot be stood on"));
  assert(!("score" in checked.result));
  await action({ action: "undo" });
  if (await page.getByRole("button", { name: "Dismiss message" }).isVisible())
    await page.getByRole("button", { name: "Dismiss message" }).click();
  checks.push("base-rule check; no clue oracle");

  const note = {
    summary:
      "A sample presentation note attached by the test, not a model run.",
    clue_ids: ["clue-1"],
    focus_person: "A",
    focus_cells: ["b1"],
  };
  await action({ action: "present" }, note);
  assert(await page.locator(".reason-note").isVisible());
  const before = (await state()).revision;
  await page.getByRole("button", { name: /Session journal/ }).click();
  await page.getByRole("button", { name: /An unopened case/ }).click();
  await page.locator(".review-banner").waitFor();
  assert.equal((await state()).revision, before);
  await page
    .getByRole("button", { name: "Return to live case", exact: true })
    .click();
  checks.push("public explanation / read-only history");

  await page
    .getByRole("button", { name: "For developers", exact: true })
    .click();
  const downloadWait = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Observation PNG", exact: true })
    .click();
  const downloaded = await downloadWait;
  await downloaded.saveAs("artifacts/browser-observation.png");
  await page
    .getByRole("button", { name: "Close dialog", exact: true })
    .filter({ visible: true })
    .click();
  checks.push("browser PNG export");

  await page.reload({ waitUntil: "networkidle" });
  await page.locator('[data-cell="b1"]').waitFor();
  assert.equal((await state()).revision, before);
  assert.deepEqual((await state()).placements, { A: "b1", B: "e3" });
  checks.push("refresh preserves session");

  await page
    .getByRole("button", { name: "Open object and terrain key", exact: true })
    .click();
  await page.waitForFunction(() =>
    [...document.querySelectorAll(".object-key img")].every(
      (img) => img.complete && img.naturalWidth > 0,
    ),
  );
  assert.equal(
    await page.locator(".object-key img").count(),
    (await state()).scene.props.length,
  );
  await page
    .getByRole("button", { name: "Close dialog", exact: true })
    .filter({ visible: true })
    .click();
  checks.push("named object and terrain key");

  const beforeDrag = (await state()).revision;
  await page
    .getByRole("button", { name: "Select Cleo", exact: true })
    .dragTo(page.locator('[data-cell="c4"]'));
  await revision(beforeDrag + 1);
  assert.equal((await state()).placements.C, "c4");
  checks.push("drag and drop placement");

  await page.evaluate(() => window.murdokuAgent.newSession("glasshouse"));
  await revision(0);
  for (const [person, cell] of Object.entries({
    A: "b1",
    B: "e3",
    C: "c4",
    D: "f5",
    E: "d6",
    V: "a2",
  }))
    await action({ action: "place", person, cell });
  await action({ action: "note", text: "The chairs place Ada and Dorian." });
  const beforeSubmission = await state();
  await page.getByLabel("Choose murderer").selectOption("B");
  await page.getByRole("button", { name: "Submit case", exact: true }).click();
  await page
    .getByRole("dialog")
    .filter({ hasText: "Ready to close the case?" })
    .getByRole("button", { name: "Submit case", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "There is more to this story." })
    .waitFor();
  await page
    .getByRole("button", { name: "Close dialog", exact: true })
    .filter({ visible: true })
    .click();
  await page.reload({ waitUntil: "networkidle" });
  await page.locator('[data-cell="b1"]').waitFor();
  assert.equal((await state()).done, true);
  await page.getByRole("button", { name: "View result", exact: true }).click();
  await page
    .getByRole("button", { name: "Keep investigating", exact: true })
    .click();
  await revision(beforeSubmission.revision);
  assert.deepEqual((await state()).placements, beforeSubmission.placements);
  assert.equal((await state()).notebook, beforeSubmission.notebook);
  assert.equal((await state()).done, false);
  await page.reload({ waitUntil: "networkidle" });
  await page.locator('[data-cell="b1"]').waitFor();
  assert.deepEqual((await state()).placements, beforeSubmission.placements);
  assert.equal((await state()).notebook, beforeSubmission.notebook);
  assert.equal((await state()).done, false);
  checks.push(
    "incorrect verdict / continue with board and notes / refresh recovery",
  );
  await page.getByLabel("Choose murderer").selectOption("A");
  await page.getByRole("button", { name: "Submit case", exact: true }).click();
  await page
    .getByRole("dialog")
    .filter({ hasText: "Ready to close the case?" })
    .getByRole("button", { name: "Submit case", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Case closed. Nicely deduced." })
    .waitFor();
  assert.equal((await state()).terminal.reward, 1);
  checks.push("complete UI submission / correct terminal result");

  const mobile = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    isMobile: true,
    hasTouch: true,
  });
  trackExternalRequests(mobile);
  const phone = await mobile.newPage();
  phone.setDefaultNavigationTimeout(120000);
  phone.setDefaultTimeout(120000);
  phone.on("pageerror", (e) => errors.push(e.message));
  await phone.goto(base, { waitUntil: "networkidle" });
  await phone.locator('[data-cell="b1"]').waitFor();
  assert(
    await phone.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await phone.getByRole("button", { name: "Select Ada", exact: true }).tap();
  await phone.locator('[data-cell="b1"]').tap();
  await phone.waitForFunction(
    () => document.querySelector(".scene-svg")?.dataset.revision === "1",
  );
  assert.deepEqual(
    (await phone.evaluate(() => window.murdokuAgent.observe())).marks.A,
    ["b1"],
  );
  const touch = await mobile.newCDPSession(phone);
  const box = await phone.locator('[data-cell="b1"]').boundingBox();
  await touch.send("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [{ x: box.x + box.width / 2, y: box.y + box.height / 2 }],
  });
  await phone.waitForTimeout(550);
  await touch.send("Input.dispatchTouchEvent", {
    type: "touchEnd",
    touchPoints: [],
  });
  await phone.waitForFunction(
    () => document.querySelector(".scene-svg")?.dataset.revision === "2",
  );
  await phone.waitForTimeout(200);
  const touched = await phone.evaluate(() => window.murdokuAgent.observe());
  assert.equal(touched.revision, 2);
  assert.equal(touched.placements.A, "b1");
  await phone.screenshot({ path: "artifacts/mobile.png", fullPage: true });
  checks.push("390px mobile layout / touch placement / no page overflow");
  await phone.evaluate(() => window.murdokuAgent.newSession("estate"));
  await phone.locator('[data-cell="p16"]').waitFor();
  assert.equal(await phone.locator("[data-cell]").count(), 256);
  assert.equal(
    await phone.locator(".zoom-controls > span").textContent(),
    "200%",
  );
  const zoomButton = await phone
    .getByRole("button", { name: "Zoom in", exact: true })
    .boundingBox();
  assert(zoomButton.width >= 44 && zoomButton.height >= 44);
  assert(
    await phone
      .getByRole("button", { name: "Fit the board", exact: true })
      .isVisible(),
  );
  assert(
    await phone.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await phone.locator('[data-cell="p16"]').tap();
  await phone.waitForFunction(
    () => document.querySelector(".scene-svg")?.dataset.revision === "1",
  );
  const largeMobile = await phone.evaluate(() => window.murdokuAgent.observe());
  assert.deepEqual(largeMobile.marks.A, ["p16"]);
  await phone.screenshot({
    path: "artifacts/estate-mobile.png",
    fullPage: true,
  });
  checks.push("16x16 mobile layout / scrolling and candidate placement");
  await mobile.close();

  await page.evaluate(() => window.murdokuAgent.newSession("lily-pond"));
  await revision(0);
  assert.equal(await page.locator("[data-cell]").count(), 64);
  await page.screenshot({ path: "artifacts/garden.png", fullPage: true });
  const garden = await state();
  assert(garden.scene.cells.some((c) => c.terrain === "water" && !c.standable));
  checks.push("8x8 outdoor terrain case");

  await page.evaluate(() => window.murdokuAgent.newSession("estate"));
  await page.locator('[data-cell="p16"]').waitFor();
  assert.equal(await page.locator("[data-cell]").count(), 256);
  await page.screenshot({
    path: "artifacts/estate-desktop.png",
    fullPage: true,
  });
  for (let i = 0; i < 4; i++)
    await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  assert(
    await page
      .locator(".board-scroll")
      .evaluate((el) => el.scrollWidth > el.clientWidth),
  );
  await page
    .getByRole("button", { name: "Place person (P)", exact: true })
    .click();
  await page.locator('[data-cell="p16"]').click();
  await revision(1);
  assert.equal((await state()).placements.A, "p16");
  checks.push("16x16 scene / 200% zoom / stable cell action");
  const estateCase = JSON.parse(
    await fs.readFile(
      new URL("../../murdoku_lab/visual/cases/estate.json", import.meta.url),
      "utf8",
    ),
  ).murdoku_case;
  const estatePlacements = Object.fromEntries(
    Object.entries(estateCase.solution).map(([person, cell]) => [
      person,
      String.fromCharCode(97 + (cell % estateCase.scene.W)) +
        (Math.floor(cell / estateCase.scene.W) + 1),
    ]),
  );
  for (const [caseId, placements, label, answer] of [
    [
      "lily-pond",
      {
        A: "b1",
        B: "d2",
        C: "f3",
        D: "h4",
        E: "g6",
        F: "e7",
        G: "c8",
        V: "a5",
      },
      "Choose murderer",
      "G",
    ],
    [
      "last-place",
      { A: "b1", B: "e3", C: "c4", D: "f5", E: "d6", V: "a2" },
      "Choose victim square",
      "a2",
    ],
    ["estate", estatePlacements, "Choose murderer", "K"],
  ]) {
    await page.evaluate((id) => window.murdokuAgent.newSession(id), caseId);
    await revision(0);
    for (const [person, cell] of Object.entries(placements))
      await action({ action: "place", person, cell });
    await page.getByLabel(label).selectOption(answer);
    await page
      .getByRole("button", { name: "Submit case", exact: true })
      .click();
    await page
      .getByRole("dialog")
      .filter({ hasText: "Ready to close the case?" })
      .getByRole("button", { name: "Submit case", exact: true })
      .click();
    await page
      .getByRole("heading", { name: "Case closed. Nicely deduced." })
      .waitFor();
    assert.equal((await state()).terminal.reward, 1);
    checks.push(`${caseId} / complete arrangement and correct answer`);
  }
  assert.deepEqual(errors, []);
  assert.deepEqual(externalRequests, []);
  checks.push("all gameplay resources hosted on the same origin");
  const receipt = {
    checks,
    passed: checks.length,
    browser_errors: errors,
    model_calls: 0,
  };
  await fs.writeFile(
    "artifacts/browser-verification.json",
    JSON.stringify(receipt, null, 2) + "\n",
  );
  console.log(JSON.stringify(receipt));
} finally {
  await browser.close();
}
