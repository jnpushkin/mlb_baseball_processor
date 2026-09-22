import { build } from "esbuild";
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import path from "node:path";
const [source, out] = process.argv.slice(2);
if (!source || !out)
  throw new Error("Usage: node frontend/build.mjs source.jsx output-directory");
mkdirSync(path.join(out, "assets"), { recursive: true });
const result = await build({
  stdin: {
    // Shared chunks also run against the legacy ReactDOM browser global.
    // The compiled build supplies that API from each function's actual module.
    contents: `import React from 'react';\nimport { createPortal } from 'react-dom';\nimport { createRoot } from 'react-dom/client';\nimport Chart from 'chart.js/auto';\nimport L from 'leaflet';\nconst ReactDOM = { createRoot, createPortal };\n${readFileSync(source, "utf8")}`,
    resolveDir: process.cwd(),
    loader: "jsx",
  },
  bundle: true,
  minify: true,
  write: false,
  format: "iife",
  target: ["es2020"],
  define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "none",
});
const js = result.outputFiles[0].contents;
const hash = (bytes) =>
  createHash("sha256").update(bytes).digest("hex").slice(0, 16);
const jsName = `assets/app-${hash(js)}.js`;
writeFileSync(path.join(out, jsName), js);
execFileSync(
  process.execPath,
  [
    "node_modules/tailwindcss/lib/cli.js",
    "-i",
    "frontend/style.css",
    "-o",
    source + ".css",
    "--content",
    source,
    "--minify",
  ],
  { stdio: ["ignore", "ignore", "pipe"] },
);
const css = Buffer.concat([
  readFileSync("node_modules/leaflet/dist/leaflet.css"),
  readFileSync(source + ".css"),
]);
const cssName = `assets/app-${hash(css)}.css`;
writeFileSync(path.join(out, cssName), css);
const assets = { js: jsName, css: cssName };
mkdirSync(path.join(out, "assets/images"), { recursive: true });
for (const name of [
  "marker-icon.png",
  "marker-icon-2x.png",
  "marker-shadow.png",
  "layers.png",
  "layers-2x.png",
]) {
  const target = `assets/images/${name}`;
  copyFileSync(
    `node_modules/leaflet/dist/images/${name}`,
    path.join(out, target),
  );
  assets[name] = target;
}
console.log(JSON.stringify(assets));
