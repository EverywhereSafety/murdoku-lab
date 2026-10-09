import { parseArgs } from "node:util";
import fs from "node:fs/promises";
import path from "node:path";
import { Resvg } from "@resvg/resvg-js";

const { values } = parseArgs({
  options: {
    url: { type: "string", default: "http://127.0.0.1:8765" },
    case: { type: "string", default: "glasshouse" },
    scope: { type: "string", default: "full" },
    style: { type: "string", default: "art" },
    out: { type: "string", default: "artifacts/observation.png" },
  },
});
if (
  !["full", "scene"].includes(values.scope) ||
  !["art", "diagram"].includes(values.style)
)
  throw new Error("Invalid scope or style");
const start = await fetch(`${values.url}/api/sessions`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ case_id: values.case }),
});
if (!start.ok) throw new Error(`Session creation failed: ${start.status}`);
const observation = await start.json();
const response = await fetch(
  `${values.url}/api/sessions/${observation.session_id}/${values.scope === "scene" ? "scene" : "observation"}.svg?style=${values.style}`,
);
if (!response.ok)
  throw new Error(`Observation render failed: ${response.status}`);
const svg = await response.text();
const out = path.resolve(values.out);
await fs.mkdir(path.dirname(out), { recursive: true });
const renderer = new Resvg(svg, {
  font: { loadSystemFonts: true, defaultFontFamily: "DejaVu Sans" },
});
const raster = renderer.render();
await fs.writeFile(out, out.endsWith(".svg") ? svg : raster.asPng());
await fs.writeFile(
  out.replace(/\.(png|svg)$/i, ".json"),
  JSON.stringify(
    {
      kind: "public_observation_render",
      case_id: values.case,
      scope: values.scope,
      style: values.style,
      width: raster.width,
      height: raster.height,
      model_calls: 0,
    },
    null,
    2,
  ) + "\n",
);
console.log(
  JSON.stringify({
    out,
    width: raster.width,
    height: raster.height,
    model_calls: 0,
  }),
);
