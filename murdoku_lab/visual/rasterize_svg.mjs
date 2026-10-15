// The raster renderer consumes only the already-public SVG, via stdin.
// Optional argv[2] is a JSON font profile: {"fontFiles": [...], "loadSystemFonts": false,
// "defaultFontFamily": "DM Sans"}. Without it, the legacy system-font profile is used.
import { createRequire } from "node:module";
import path from "node:path";
const require = createRequire(path.join(process.cwd(), "package.json"));
const { Resvg } = require("@resvg/resvg-js");
const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const svg = Buffer.concat(chunks).toString("utf8");
const profile = process.argv[2] ? JSON.parse(process.argv[2]) : null;
const font = profile
  ? {
      fontFiles: profile.fontFiles,
      loadSystemFonts: Boolean(profile.loadSystemFonts),
      defaultFontFamily: profile.defaultFontFamily || "DM Sans",
    }
  : { loadSystemFonts: true, defaultFontFamily: "DejaVu Sans" };
const options = { font };
if (profile && profile.fitWidth) options.fitTo = { mode: "width", value: profile.fitWidth };
const rendered = new Resvg(svg, options);
process.stdout.write(rendered.render().asPng());
