// The raster renderer consumes only the already-public SVG, via stdin.
import { createRequire } from "node:module";
import path from "node:path";
const require = createRequire(path.join(process.cwd(), "package.json"));
const { Resvg } = require("@resvg/resvg-js");
const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const svg = Buffer.concat(chunks).toString("utf8");
const rendered = new Resvg(svg, {
  font: { loadSystemFonts: true, defaultFontFamily: "DejaVu Sans" },
});
process.stdout.write(rendered.render().asPng());
