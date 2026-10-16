#!/usr/bin/env node

/**
 * Offline renderer bundled with create-document-visuals.
 * Renderer version: 0.2.0
 * Derived from the 2026-08-05 candidate renderer snapshot whose SHA-256 was
 * 97513C8E009615AC8E6A822AA5283274060DD96D97B52B972BE367F6862FAB7C.
 *
 * Required environment variable:
 *   CODEX_VIS_NODE_MODULES=<bundled node_modules path>
 *
 * Commands:
 *   node <script> version
 *   node <script> inspect <input.mmd>
 *   node <script> diagram <input.mmd> <output.svg> <output.png>
 *   node <script> mermaid <input.mmd> <output.svg> <output.png>
 *   node <script> check-layout <input.svg> [--width 1000] [--output report.json]
 *   node <script> image   <input.svg> <output.png>
 *   node <script> pdf     <input.md> <output.html> <output.pdf>
 *
 * The Mermaid-compatible parser deliberately supports only the flowchart
 * supported subset: LR/RL/TD/TB direction, quoted rectangle/decision nodes,
 * labeled or unlabeled arrows, chains, and subgraphs. Unknown syntax fails
 * closed instead of silently producing a partial diagram.
 */

import fs from "node:fs";
import fsp from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL, fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const [command, ...args] = process.argv.slice(2);
const moduleRoot = process.env.CODEX_VIS_NODE_MODULES;
const RENDERER_VERSION = "0.2.0";

if (!moduleRoot && !["version", "inspect"].includes(command)) {
  throw new Error("CODEX_VIS_NODE_MODULES is required; point it to the bundled node_modules directory.");
}

const localRequire = createRequire(import.meta.url);

function requireRuntime(relativePath) {
  const requested = path.join(moduleRoot, relativePath);
  if (relativePath.replaceAll("\\", "/") === "sharp/lib/index.js" && !fs.existsSync(requested)) {
    return localRequire(path.join(moduleRoot, "sharp/dist/index.cjs"));
  }
  return localRequire(requested);
}

function ensureParent(filePath) {
  fs.mkdirSync(path.dirname(path.resolve(filePath)), { recursive: true });
}

function assertDistinctPaths(inputPath, ...outputPaths) {
  const normalize = (filePath) => {
    const resolved = path.resolve(filePath);
    return process.platform === "win32" ? resolved.toLowerCase() : resolved;
  };
  const seen = new Set([normalize(inputPath)]);
  for (const outputPath of outputPaths) {
    const normalized = normalize(outputPath);
    if (seen.has(normalized)) {
      throw new Error("Input and output paths must be distinct: " + path.resolve(outputPath));
    }
    seen.add(normalized);
  }
}

function escapeDot(value) {
  return String(value)
    .replaceAll("\\", "\\\\")
    .replaceAll('"', '\\"')
    .replaceAll("\r\n", "\n")
    .replaceAll("\n", "\\n");
}

function parseMermaidFlowchart(source) {
  const lines = source.split(/\r?\n/);
  const nodes = new Map();
  const edges = [];
  const clusters = new Map();
  let direction = null;
  let currentCluster = null;

  function registerNode(token, clusterId) {
    const { id, rectangleLabel, decisionLabel } = token;
    const explicitLabel = (rectangleLabel ?? decisionLabel)?.replaceAll("\\n", "\n");
    const shape = decisionLabel !== undefined ? "diamond" : "box";
    const prior = nodes.get(id) ?? { id, label: id, shape: "box", cluster: null };

    if (explicitLabel !== undefined) {
      prior.label = explicitLabel;
      prior.shape = shape;
    }
    if (clusterId) {
      if (prior.cluster && prior.cluster !== clusterId) {
        throw new Error(`Node ${id} cannot belong to both ${prior.cluster} and ${clusterId}.`);
      }
      prior.cluster = clusterId;
      clusters.get(clusterId).nodes.add(id);
    }
    nodes.set(id, prior);
    return prior;
  }

  function parseNodeAtStart(fragment) {
    const match = fragment.match(/^\s*([A-Za-z_][A-Za-z0-9_-]*)(?:\[\s*"([^"]*)"\s*\]|\{\s*"([^"]*)"\s*\})?/);
    if (!match) return null;
    return {
      token: {
        id: match[1],
        rectangleLabel: match[2],
        decisionLabel: match[3],
      },
      rest: fragment.slice(match[0].length),
    };
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith("%%")) continue;

    const header = line.match(/^flowchart\s+(LR|RL|TD|TB)$/i);
    if (header) {
      direction = header[1].toUpperCase();
      continue;
    }

    const subgraph = line.match(/^subgraph\s+([A-Za-z_][A-Za-z0-9_-]*)\s*\[(.+)\]$/);
    if (subgraph) {
      if (currentCluster) throw new Error(`Nested subgraphs are not supported: ${line}`);
      currentCluster = subgraph[1];
      if (clusters.has(currentCluster)) throw new Error(`Duplicate subgraph ID: ${currentCluster}`);
      clusters.set(currentCluster, { id: currentCluster, label: subgraph[2].replaceAll("\\n", "\n"), nodes: new Set() });
      continue;
    }

    if (line === "end") {
      if (!currentCluster) throw new Error("Unexpected subgraph end.");
      currentCluster = null;
      continue;
    }

    if (/^direction\b/i.test(line)) {
      throw new Error(`Subgraph direction overrides are not supported: ${line}`);
    }

    const first = parseNodeAtStart(line);
    if (!first) throw new Error(`Unsupported Mermaid-lite line: ${line}`);
    let previous = registerNode(first.token, currentCluster);
    let rest = first.rest;
    let edgeCount = 0;
    while (rest.trim()) {
      const arrow = rest.match(/^\s*(?:--\s*"([^"]*)"\s*-->|-->)\s*/);
      if (!arrow) throw new Error(`Unsupported Mermaid-lite syntax near: ${rest.trim()}`);
      rest = rest.slice(arrow[0].length);
      const next = parseNodeAtStart(rest);
      if (!next) throw new Error(`Arrow is missing a supported target node: ${line}`);
      const target = registerNode(next.token, currentCluster);
      edges.push({ from: previous.id, to: target.id, label: (arrow[1] ?? "").replaceAll("\\n", "\n") });
      edgeCount += 1;
      previous = target;
      rest = next.rest;
    }

    const hasDeclaration = first.token.rectangleLabel !== undefined || first.token.decisionLabel !== undefined;
    if (edgeCount === 0 && !hasDeclaration) {
      throw new Error(`Bare node references are not supported: ${line}`);
    }
  }

  if (!direction) throw new Error("Missing flowchart direction header.");
  if (currentCluster) throw new Error(`Subgraph ${currentCluster} is not closed.`);
  if (nodes.size === 0 || edges.length === 0) throw new Error("Diagram has no nodes or edges.");

  const rankdir = direction === "TD" || direction === "TB" ? "TB" : direction;
  const nodeLines = [];
  const declaredInCluster = new Set();

  function nodeDot(node) {
    const attributes = [
      `label="${escapeDot(node.label)}"`,
      `shape=${node.shape}`,
    ];
    if (node.shape === "diamond") {
      attributes.push('style="filled"', 'fillcolor="#FFF2D9"', 'color="#B7791F"');
    }
    return `    ${node.id} [${attributes.join(", ")}];`;
  }

  const clusterLines = [];
  for (const cluster of clusters.values()) {
    clusterLines.push(`  subgraph cluster_${cluster.id} {`);
    clusterLines.push(`    label="${escapeDot(cluster.label)}";`);
    clusterLines.push('    color="#CBD5E1"; style="rounded,filled"; fillcolor="#F8FAFC"; penwidth=1.1;');
    for (const nodeId of cluster.nodes) {
      clusterLines.push(nodeDot(nodes.get(nodeId)));
      declaredInCluster.add(nodeId);
    }
    clusterLines.push("  }");
  }

  for (const node of nodes.values()) {
    if (!declaredInCluster.has(node.id)) nodeLines.push(nodeDot(node));
  }

  const nodeOrder = new Map([...nodes.keys()].map((nodeId, index) => [nodeId, index]));
  const edgeLines = edges.map((edge) => {
    const attributes = [];
    if (edge.label) attributes.push(`label="${escapeDot(edge.label)}"`);
    if (nodeOrder.get(edge.to) <= nodeOrder.get(edge.from)) {
      attributes.push("constraint=false");
    }
    const suffix = attributes.length ? ` [${attributes.join(", ")}]` : "";
    return `  ${edge.from} -> ${edge.to}${suffix};`;
  });

  return [
    "digraph VisualPilot {",
    `  graph [rankdir=${rankdir}, bgcolor="transparent", pad="0.25", nodesep="0.38", ranksep="0.62", splines=polyline, outputorder=edgesfirst, fontname="Microsoft YaHei", fontsize=15];`,
    '  node [shape=box, style="rounded,filled", fillcolor="#F3F6FA", color="#8190A5", penwidth=1.15, fontname="Microsoft YaHei", fontcolor="#17202A", fontsize=12, width=2.45, margin="0.34,0.16"];',
    '  edge [color="#64748B", penwidth=1.25, arrowsize=0.75, fontname="Microsoft YaHei", fontcolor="#334155", fontsize=10];',
    ...clusterLines,
    ...nodeLines,
    ...edgeLines,
    "}",
  ].join("\n");
}

function summarizeDot(dot) {
  return {
    rendererVersion: RENDERER_VERSION,
    grammar: "mermaid-lite-flowchart-v1",
    nodes: [...dot.matchAll(/^ {4}[A-Za-z_][A-Za-z0-9_-]* \[label=/gm)].length,
    edges: [...dot.matchAll(/^ {2}[A-Za-z_][A-Za-z0-9_-]* -> [A-Za-z_][A-Za-z0-9_-]*/gm)].length,
    subgraphs: [...dot.matchAll(/^ {2}subgraph cluster_/gm)].length,
  };
}

async function inspectDiagram(inputPath) {
  const source = await fsp.readFile(inputPath, "utf8");
  const dot = parseMermaidFlowchart(source);
  return summarizeDot(dot);
}

function assertSafeSvg(source) {
  const rejected = [
    /<script\b/i,
    /<foreignObject\b/i,
    /<!ENTITY\b/i,
    /\son[a-z]+\s*=/i,
    /(?:href|xlink:href)\s*=\s*["']\s*(?:https?:|file:|\/\/)/i,
    /url\(\s*["']?\s*(?:https?:|file:|\/\/)/i,
  ];
  if (rejected.some((pattern) => pattern.test(source))) {
    throw new Error("SVG contains scripts, active content, or external references.");
  }
}

function assertSafeMarkdown(source) {
  const rejected = [
    /<(?:script|iframe|object|embed|link)\b/i,
    /\son[a-z]+\s*=/i,
    /!\[[^\]]*\]\(\s*https?:\/\//i,
    /<img\b[^>]*\bsrc\s*=\s*["']\s*(?:https?:)?\/\//i,
  ];
  if (rejected.some((pattern) => pattern.test(source))) {
    throw new Error("Markdown contains active HTML or remote image resources.");
  }
}

async function renderDiagram(inputPath, svgPath, pngPath) {
  assertDistinctPaths(inputPath, svgPath, pngPath);
  const fontCache = path.join(os.tmpdir(), "codex-visual-font-cache");
  fs.mkdirSync(fontCache, { recursive: true });
  process.env.XDG_CACHE_HOME ??= fontCache;
  const { instance } = requireRuntime(path.join("@viz-js", "viz", "dist", "viz.cjs"));
  const sharp = requireRuntime(path.join("sharp", "lib", "index.js"));
  const source = await fsp.readFile(inputPath, "utf8");
  const dot = parseMermaidFlowchart(source);
  const summary = summarizeDot(dot);
  const viz = await instance();
  const svg = viz.renderString(dot, { format: "svg", engine: "dot" });

  ensureParent(svgPath);
  ensureParent(pngPath);
  await fsp.writeFile(svgPath, svg, "utf8");
  await sharp(Buffer.from(svg), { density: 180 })
    .flatten({ background: "#FFFFFF" })
    .resize({ width: 2200, withoutEnlargement: true })
    .png({ compressionLevel: 9 })
    .toFile(pngPath);
  return {
    ...summary,
    source: path.resolve(inputPath),
    svg: path.resolve(svgPath),
    png: path.resolve(pngPath),
  };
}

async function renderSvgImage(inputPath, pngPath) {
  assertDistinctPaths(inputPath, pngPath);
  const sharp = requireRuntime(path.join("sharp", "lib", "index.js"));
  const svgSource = await fsp.readFile(inputPath, "utf8");
  assertSafeSvg(svgSource);
  const svg = Buffer.from(svgSource, "utf8");
  ensureParent(pngPath);
  await sharp(svg, { density: 180 })
    .flatten({ background: "#FFFFFF" })
    .resize({ width: 2200, withoutEnlargement: true })
    .png({ compressionLevel: 9 })
    .toFile(pngPath);
  return {
    rendererVersion: RENDERER_VERSION,
    source: path.resolve(inputPath),
    png: path.resolve(pngPath),
  };
}

function findBrowserExecutable() {
  const candidates = [
    process.env.CODEX_VIS_BROWSER,
    path.join(process.env["ProgramFiles"] || path.join(path.parse(os.homedir()).root, "Program Files"), "Google/Chrome/Application/chrome.exe"),
    path.join(process.env["ProgramFiles(x86)"] || path.join(path.parse(os.homedir()).root, "Program Files (x86)"), "Microsoft/Edge/Application/msedge.exe"),
    path.join(process.env["ProgramFiles"] || path.join(path.parse(os.homedir()).root, "Program Files"), "Microsoft/Edge/Application/msedge.exe"),
  ].filter(Boolean);
  const executable = candidates.find((candidate) => fs.existsSync(candidate));
  if (!executable) throw new Error("No supported local Chrome or Edge executable was found.");
  return executable;
}

async function renderMarkdownPdf(inputPath, htmlPath, pdfPath) {
  assertDistinctPaths(inputPath, htmlPath, pdfPath);
  const markedModulePath = path.join(moduleRoot, "marked", "lib", "marked.esm.js");
  const { marked } = await import(pathToFileURL(markedModulePath).href);
  const { chromium } = requireRuntime(path.join("playwright", "index.js"));
  const markdown = await fsp.readFile(inputPath, "utf8");
  assertSafeMarkdown(markdown);
  const firstHeading = markdown.match(/^#\s+(.+)$/m)?.[1] ?? path.basename(inputPath, path.extname(inputPath));
  const body = marked.parse(markdown, { gfm: true, breaks: false });
  const baseHref = pathToFileURL(`${path.dirname(path.resolve(inputPath))}${path.sep}`).href;
  const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <base href="${baseHref}">
  <title>${firstHeading.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")}</title>
  <style>
    @page { size: A4; margin: 14mm 14mm 16mm; }
    * { box-sizing: border-box; }
    body { margin: 0; color: #17202a; font-family: "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif; font-size: 10.5pt; line-height: 1.62; }
    h1 { margin: 0 0 9mm; font-size: 21pt; line-height: 1.25; color: #0f172a; }
    h2 { margin: 8mm 0 3mm; font-size: 15pt; line-height: 1.3; color: #1e3a5f; break-after: avoid; }
    h3 { margin: 6mm 0 2mm; font-size: 12.5pt; line-height: 1.35; color: #334155; break-after: avoid; }
    p { margin: 0 0 3.2mm; }
    ul, ol { margin: 1.5mm 0 3.5mm; padding-left: 6mm; }
    li { margin: 0 0 1.2mm; }
    blockquote { margin: 3mm 0; padding: 2.5mm 4mm; border-left: 3px solid #4f78a8; background: #f4f7fb; color: #334155; }
    table { width: 100%; border-collapse: collapse; margin: 3mm 0 5mm; font-size: 9.2pt; break-inside: avoid; }
    th, td { border: 1px solid #cbd5e1; padding: 2mm 2.2mm; vertical-align: top; }
    th { background: #edf2f7; text-align: left; color: #1e293b; }
    img { display: block; max-width: 100%; max-height: 220mm; object-fit: contain; margin: 4mm auto 2mm; break-inside: avoid; }
    em { color: #475569; }
    code { font-family: Consolas, "Courier New", monospace; font-size: 9pt; background: #f1f5f9; padding: 0.2mm 0.8mm; }
    pre { white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #e2e8f0; padding: 3mm; }
    hr { border: 0; border-top: 1px solid #cbd5e1; margin: 6mm 0; }
    a { color: #245a92; text-decoration: none; }
  </style>
</head>
<body>${body}</body>
</html>`;

  ensureParent(htmlPath);
  ensureParent(pdfPath);
  await fsp.writeFile(htmlPath, html, "utf8");

  const browser = await chromium.launch({
    executablePath: findBrowserExecutable(),
    headless: true,
    args: ["--allow-file-access-from-files", "--disable-gpu"],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
    await page.route("**/*", async (route) => {
      const protocol = new URL(route.request().url()).protocol;
      if (["file:", "data:", "blob:", "about:"].includes(protocol)) {
        await route.continue();
      } else {
        await route.abort("blockedbyclient");
      }
    });
    await page.goto(pathToFileURL(path.resolve(htmlPath)).href, { waitUntil: "load" });
    await page.evaluate(async () => {
      if (document.fonts?.ready) await document.fonts.ready;
      await Promise.all([...document.images].map((image) => image.complete
        ? Promise.resolve()
        : new Promise((resolve, reject) => {
            image.addEventListener("load", resolve, { once: true });
            image.addEventListener("error", reject, { once: true });
          })));
      const broken = [...document.images].filter((image) => image.naturalWidth === 0);
      if (broken.length) throw new Error(`Broken images: ${broken.map((image) => image.src).join(", ")}`);
    });
    await page.pdf({
      path: pdfPath,
      format: "A4",
      printBackground: true,
      preferCSSPageSize: true,
      displayHeaderFooter: true,
      headerTemplate: "<span></span>",
      footerTemplate: '<div style="width:100%;font-family:Arial,sans-serif;font-size:8px;color:#64748b;text-align:center;"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
      margin: { top: "14mm", right: "14mm", bottom: "16mm", left: "14mm" },
    });
  } finally {
    await browser.close();
  }
  return {
    rendererVersion: RENDERER_VERSION,
    source: path.resolve(inputPath),
    html: path.resolve(htmlPath),
    pdf: path.resolve(pdfPath),
  };
}

function usage() {
  return [
    "Usage:",
    "  version",
    "  inspect <input.mmd>",
    "  diagram <input.mmd> <output.svg> <output.png>",
    "  mermaid <input.mmd> <output.svg> <output.png>",
    "  check-layout <input.svg> [--width 1000] [--output report.json] [--screenshot preview.png]",
    "  image   <input.svg> <output.png>",
    "  pdf     <input.md> <output.html> <output.pdf>",
  ].join("\n");
}

let result;
if (command === "version" && args.length === 0) {
  result = { rendererVersion: RENDERER_VERSION };
} else if (command === "inspect" && args.length === 1) {
  result = await inspectDiagram(...args);
} else if (command === "diagram" && args.length === 3) {
  result = await renderDiagram(...args);
} else if (command === "mermaid" && args.length === 3) {
  const { renderMermaid } = await import("./render_mermaid.mjs");
  result = { rendererVersion: RENDERER_VERSION, ...(await renderMermaid(...args)) };
} else if (command === "check-layout" && args.length >= 1) {
  const checkerPath = new URL("./check_visual_layout.mjs", import.meta.url);
  const checked = spawnSync(process.execPath, [fileURLToPath(checkerPath), ...args], {
    env: process.env, encoding: "utf8", windowsHide: true,
  });
  if (checked.stdout) process.stdout.write(checked.stdout);
  if (checked.stderr) process.stderr.write(checked.stderr);
  if (checked.error) throw checked.error;
  process.exit(checked.status ?? 1);
} else if (command === "image" && args.length === 2) {
  result = await renderSvgImage(...args);
} else if (command === "pdf" && args.length === 3) {
  result = await renderMarkdownPdf(...args);
} else {
  throw new Error(usage());
}

console.log(JSON.stringify(result, null, 2));
