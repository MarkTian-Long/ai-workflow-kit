import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ENGINE_VERSION = '12.2.0';
const BUNDLE_SHA256 = 'a8a6a6f805b074a8261a2825c86f99c8054acb3b35f50bb7e24a4f9f2c3c3b9f';
const BUNDLE_PATH = path.resolve(HERE, '../assets/vendor/mermaid/mermaid.min.js');
const MAX_SOURCE_BYTES = 256 * 1024;
const MAX_DIMENSION = 16000;
const MAX_PIXELS = 40_000_000;

// The library is complete; this adapter intentionally exposes only the three
// additional diagram families verified with the bundled offline runtime.
const TYPES = [
  [/^sequenceDiagram\b/, 'sequence'],
  [/^stateDiagram(?:-v2)?\b/, 'state'],
  [/^erDiagram\b/, 'er'],
];

function validateSource(source) {
  if (!source.trim() || source.includes('\0')) throw new Error('Empty source or NUL byte.');
  if (/^\s*---(?:\r?\n|$)/.test(source) || /%%\s*\{/.test(source)) {
    throw new Error('Source configuration/frontmatter is disabled; renderer security and styling are fixed.');
  }
  if (/(?:https?|ftp|file|data|javascript|vbscript|wss?|blob):|\/\//i.test(source)) {
    throw new Error('URLs and remote/local resource references are disabled.');
  }
  const markupCandidate = source.replace(/<<(?:choice|fork|join)>>/g, '');
  if (/<\s*\/?\s*[A-Za-z!]|\bon[a-z]+\s*=|\burl\s*\(/i.test(markupCandidate)) {
    throw new Error('HTML, event handlers and CSS resource URLs are disabled.');
  }
  if (/^\s*(?:click|links?|callback|href|classDef|style|linkStyle|cssClass)\b/im.test(source)
      || /\[[^\]\r\n]*\]\s*\(/.test(source)) {
    throw new Error('Clicks, links, callbacks and source styling are disabled.');
  }
  const firstLine = source.split(/\r?\n/).find((line) => line.trim() && !/^\s*%%/.test(line))?.trim();
  const selected = TYPES.find(([pattern]) => pattern.test(firstLine || ''));
  if (!selected) throw new Error('This route accepts sequenceDiagram, stateDiagram-v2 and erDiagram only.');
  return selected[1];
}

async function exists(target) {
  try { await fs.lstat(target); return true; } catch (error) {
    if (error.code === 'ENOENT') return false;
    throw error;
  }
}

async function canonical(target) {
  const resolved = await fs.realpath(target).catch((error) => {
    if (error.code !== 'ENOENT') throw error;
    return path.resolve(target);
  });
  return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
}

async function loadPlaywright() {
  const roots = [
    process.env.CODEX_VIS_NODE_MODULES,
    process.env.DOCUMENT_VISUALS_NODE_MODULES,
    path.resolve(HERE, '../node_modules'),
    path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'),
  ].filter(Boolean);
  for (const root of roots) {
    if (!await exists(path.join(root, 'playwright/package.json'))) continue;
    return createRequire(path.join(root, '__document_visuals_loader__.cjs'))('playwright');
  }
  throw new Error('Local Playwright is missing. Set CODEX_VIS_NODE_MODULES to an existing node_modules directory. No packages are downloaded.');
}

async function findBrowser() {
  const candidates = [
    process.env.CODEX_VIS_BROWSER,
    process.env.DOCUMENT_VISUALS_CHROME,
    path.join(process.env["ProgramFiles"] || path.join(path.parse(os.homedir()).root, "Program Files"), "Google/Chrome/Application/chrome.exe"),
    path.join(process.env["ProgramFiles(x86)"] || path.join(path.parse(os.homedir()).root, "Program Files (x86)"), "Microsoft/Edge/Application/msedge.exe"),
    path.join(process.env["ProgramFiles"] || path.join(path.parse(os.homedir()).root, "Program Files"), "Microsoft/Edge/Application/msedge.exe"),
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ].filter(Boolean);
  for (const candidate of candidates) if (await exists(candidate)) return candidate;
  throw new Error('An existing Chrome/Chromium/Edge executable is required. Set CODEX_VIS_BROWSER; no browser is downloaded.');
}

async function within(promise, milliseconds, label) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(`${label} timed out.`)), milliseconds); }),
    ]);
  } finally { clearTimeout(timer); }
}

async function writePair(svgPath, svg, pngPath, png) {
  // No-clobber publication: failures never overwrite or remove earlier results.
  const staged = [];
  const published = [];
  try {
    for (const [target, content] of [[svgPath, svg], [pngPath, png]]) {
      await fs.mkdir(path.dirname(target), { recursive: true });
      const temporary = path.join(path.dirname(target), `.${path.basename(target)}.${crypto.randomUUID()}.tmp`);
      await fs.writeFile(temporary, content, { flag: 'wx' });
      staged.push([temporary, target]);
    }
    for (const [temporary, target] of staged) {
      // Same-directory hard links are atomic and refuse an existing destination.
      await fs.link(temporary, target);
      published.push(target);
    }
  } catch (error) {
    await Promise.all(published.map((target) => fs.unlink(target).catch(() => {})));
    throw error;
  } finally {
    await Promise.all(staged.map(([temporary]) => fs.unlink(temporary).catch(() => {})));
  }
}

export async function renderMermaid(inputPath, outputSvgPath, outputPngPath) {
  if (!inputPath || !outputSvgPath || !outputPngPath) throw new Error('Three paths are required: input.mmd output.svg output.png.');
  const sourcePath = path.resolve(inputPath);
  const svgPath = path.resolve(outputSvgPath);
  const pngPath = path.resolve(outputPngPath);
  if (path.extname(svgPath).toLowerCase() !== '.svg' || path.extname(pngPath).toLowerCase() !== '.png') {
    throw new Error('Output extensions must be .svg and .png.');
  }
  const destinations = await Promise.all([sourcePath, svgPath, pngPath].map(canonical));
  if (new Set(destinations).size !== 3) throw new Error('Input, SVG and PNG paths must be different.');
  if (await exists(svgPath) || await exists(pngPath)) throw new Error('Output already exists; choose new output paths. Earlier results are preserved.');
  const sourceBytes = await fs.readFile(sourcePath);
  if (sourceBytes.length > MAX_SOURCE_BYTES) throw new Error(`Source exceeds ${MAX_SOURCE_BYTES} bytes.`);
  const source = new TextDecoder('utf-8', { fatal: true }).decode(sourceBytes);
  const diagramType = validateSource(source);
  const bundle = await fs.readFile(BUNDLE_PATH);
  if (crypto.createHash('sha256').update(bundle).digest('hex') !== BUNDLE_SHA256) {
    throw new Error('Vendored Mermaid bundle integrity check failed.');
  }
  const [{ chromium }, executablePath] = await Promise.all([loadPlaywright(), findBrowser()]);
  const browser = await chromium.launch({
    executablePath,
    headless: true,
    timeout: 30000,
    args: [
      '--disable-background-networking', '--disable-component-update', '--disable-sync',
      '--no-first-run', '--no-default-browser-check', '--disable-domain-reliability',
      '--disable-client-side-phishing-detection', '--metrics-recording-only',
      '--host-resolver-rules=MAP * ~NOTFOUND',
    ],
  });
  let context;
  try {
    context = await browser.newContext({
      offline: true, serviceWorkers: 'block', viewport: { width: 1600, height: 1200 },
      deviceScaleFactor: 1, colorScheme: 'light', locale: 'zh-CN',
    });
    const blockedRequests = [];
    await context.route('**/*', async (route) => {
      blockedRequests.push(route.request().url());
      await route.abort('blockedbyclient');
    });
    const page = await context.newPage();
    page.setDefaultTimeout(30000);
    await page.setContent('<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; img-src \'none\'; font-src \'none\'; connect-src \'none\'; frame-src \'none\'; base-uri \'none\'; form-action \'none\'"><style>html,body{margin:0;background:#fff}#diagram-root{display:flow-root;font-family:Microsoft YaHei,Segoe UI,Arial,sans-serif}svg{display:block;background:#fff}</style></head><body><main id="diagram-root"></main></body></html>');
    // Only the fixed, integrity-checked official bundle is executable content.
    await page.addScriptTag({ content: bundle.toString('utf8') });
    const id = `mermaid_${crypto.createHash('sha256').update(sourceBytes).digest('hex').slice(0, 16)}`;
    const rendered = await within(page.evaluate(async ({ source, id, maxDimension, maxPixels }) => {
      const mermaid = globalThis.mermaid;
      if (!mermaid?.render) throw new Error('The fixed Mermaid browser bundle did not initialize.');
      mermaid.initialize({
        startOnLoad: false, securityLevel: 'strict', suppressErrorRendering: true,
        htmlLabels: false, deterministicIds: true, deterministicIDSeed: 'document-visuals-offline',
        fontFamily: 'Microsoft YaHei, Segoe UI, Arial, sans-serif', theme: 'base',
        themeVariables: {
          fontFamily: 'Microsoft YaHei, Segoe UI, Arial, sans-serif', fontSize: '16px',
          primaryColor: '#eef2fb', primaryTextColor: '#1f2937', primaryBorderColor: '#5b6b8c',
          lineColor: '#5b6b8c', secondaryColor: '#eaf5ef', tertiaryColor: '#fff4dd',
          background: '#ffffff',
        },
        flowchart: { htmlLabels: false, useMaxWidth: false },
        sequence: { useMaxWidth: false }, er: { useMaxWidth: false }, state: { useMaxWidth: false },
      });
      await mermaid.parse(source);
      const result = await mermaid.render(id, source);
      const parsed = new DOMParser().parseFromString(result.svg, 'image/svg+xml');
      const svg = parsed.documentElement;
      if (parsed.querySelector('parsererror') || svg.localName !== 'svg') throw new Error('Renderer returned invalid SVG.');
      for (const node of [svg, ...svg.querySelectorAll('*')]) {
        if (['script', 'foreignObject', 'iframe', 'image', 'a', 'animate', 'set'].includes(node.localName)) {
          throw new Error(`Unsafe/non-static SVG element: ${node.localName}.`);
        }
        for (const attribute of node.attributes) {
          if (/^on/i.test(attribute.name)) throw new Error('SVG event handlers are disabled.');
          if (/(?:^|:)href$/i.test(attribute.name) && !attribute.value.startsWith('#')) throw new Error('SVG resource references are disabled.');
        }
        const styles = node.localName === 'style' ? node.textContent : node.getAttribute('style') || '';
        if (/@import|@font-face/i.test(styles)) throw new Error('External CSS/font declarations are disabled.');
        for (const match of styles.matchAll(/url\(\s*['"]?([^)'"\s]+)/gi)) {
          if (!match[1].startsWith('#')) throw new Error('Only SVG fragment references are allowed.');
        }
      }
      const viewBox = svg.getAttribute('viewBox')?.trim().split(/[\s,]+/).map(Number);
      if (!viewBox || viewBox.length !== 4 || viewBox.some((n) => !Number.isFinite(n))) throw new Error('SVG has no finite viewBox.');
      const width = Math.ceil(viewBox[2]);
      const height = Math.ceil(viewBox[3]);
      if (width < 1 || height < 1 || width > maxDimension || height > maxDimension || width * height > maxPixels) {
        throw new Error('Diagram dimensions exceed the local export limits.');
      }
      svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      svg.setAttribute('width', String(width));
      svg.setAttribute('height', String(height));
      svg.style.maxWidth = 'none';
      svg.style.background = '#ffffff';
      document.getElementById('diagram-root').replaceChildren(document.importNode(svg, true));
      await document.fonts.ready;
      return {
        svg: new XMLSerializer().serializeToString(document.querySelector('#diagram-root > svg')),
        width, height, libraryDiagramType: result.diagramType || null,
      };
    }, { source, id, maxDimension: MAX_DIMENSION, maxPixels: MAX_PIXELS }), 30000, 'Mermaid render');
    const png = await page.locator('#diagram-root > svg').screenshot({ type: 'png', animations: 'disabled' });
    if (blockedRequests.length) throw new Error('The renderer attempted a network request; export was rejected.');
    if (!png.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
        || png.readUInt32BE(16) !== rendered.width || png.readUInt32BE(20) !== rendered.height) {
      throw new Error('PNG signature or dimensions do not match the SVG.');
    }
    if (!rendered.svg.includes('<text') || rendered.svg.length < 500 || png.length < 500) {
      throw new Error('Diagram output is empty or has no SVG text.');
    }
    await writePair(svgPath, rendered.svg, pngPath, png);
    return {
      ok: true, engine: 'mermaid', engineVersion: ENGINE_VERSION, diagramType,
      source: sourcePath, svg: svgPath, png: pngPath, width: rendered.width, height: rendered.height,
      networkRequestsBlocked: 0,
    };
  } finally {
    await context?.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.length !== 3) {
    process.stderr.write('Usage: node render_mermaid.mjs input.mmd output.svg output.png\n');
    process.exitCode = 2;
  } else {
    try { process.stdout.write(`${JSON.stringify(await renderMermaid(...args))}\n`); }
    catch (error) {
      process.stderr.write(`${JSON.stringify({ ok: false, engine: 'mermaid', engineVersion: ENGINE_VERSION, error: String(error.message).slice(0, 1200) })}\n`);
      process.exitCode = 1;
    }
  }
}
