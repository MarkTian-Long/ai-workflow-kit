#!/usr/bin/env node
/**
 * Local SVG geometry check, after real browser font/layout resolution.
 * Usage: node check_visual_layout.mjs input.svg [--width 1000]
 *        [--output report.json] [--screenshot preview.png]
 * CODEX_VIS_NODE_MODULES may point to an existing node_modules directory.
 * No downloads; Chrome/Edge runs headlessly with scripts and network disabled.
 * Exit codes: 0 pass, 2 revise, 3 structural-only, 1 invocation/runtime failure.
 * `pass` covers the reported geometry only, never business correctness.
 */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const VERSION = '0.2.0';
const MANUAL_CHECKS = [
  'Confirm business order, branch conditions, arrow direction and exception/return paths against the source.',
  'Inspect the actual delivery size for readable Chinese, hierarchy, region meaning and intentional overlaps.',
  'Review heuristic edge findings and any unmeasured/unsupported elements; geometry is not semantic acceptance.',
];

function parseArgs(argv) {
  if (!argv.length || argv.includes('--help')) return null;
  const options = { input: path.resolve(argv[0]), width: 1000 };
  for (let i = 1; i < argv.length; i += 2) {
    const flag = argv[i], value = argv[i + 1];
    if (!['--width', '--output', '--screenshot'].includes(flag) || !value) throw new Error(`Invalid option: ${flag}`);
    if (flag === '--width') options.width = Number(value);
    else options[flag.slice(2)] = path.resolve(value);
  }
  if (!Number.isInteger(options.width) || options.width < 200 || options.width > 10000) throw new Error('--width must be an integer from 200 to 10000.');
  const paths = [options.input, options.output, options.screenshot].filter(Boolean);
  const keys = paths.map(p => process.platform === 'win32' ? p.toLowerCase() : p);
  if (new Set(keys).size !== keys.length) throw new Error('Input, JSON output and screenshot paths must all be distinct.');
  for (const output of [options.output, options.screenshot].filter(Boolean)) {
    if (fs.existsSync(output) && fs.statSync(options.input).ino === fs.statSync(output).ino && fs.statSync(options.input).dev === fs.statSync(output).dev) {
      throw new Error('An output is the same underlying file as the input.');
    }
  }
  if (path.extname(options.input).toLowerCase() !== '.svg') throw new Error('Input must be an SVG file.');
  return options;
}

function runtime() {
  const roots = [process.env.CODEX_VIS_NODE_MODULES, path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')].filter(Boolean);
  for (const root of roots) {
    const entry = path.join(root, 'playwright/index.js');
    if (fs.existsSync(entry)) return require(entry).chromium;
  }
  try { return require('playwright').chromium; }
  catch { throw new Error('Existing Playwright not found. Set CODEX_VIS_NODE_MODULES; this checker does not install dependencies.'); }
}

function browserExecutable() {
  const paths = [process.env.CODEX_VIS_BROWSER, process.env.CODEX_VIS_BROWSER_EXECUTABLE, process.env.CHROME_PATH,
    path.join(process.env["ProgramFiles"] || path.join(path.parse(os.homedir()).root, "Program Files"), "Google/Chrome/Application/chrome.exe"),
    path.join(process.env["ProgramFiles(x86)"] || path.join(path.parse(os.homedir()).root, "Program Files (x86)"), "Microsoft/Edge/Application/msedge.exe"),
    path.join(process.env["ProgramFiles"] || path.join(path.parse(os.homedir()).root, "Program Files"), "Microsoft/Edge/Application/msedge.exe"),
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'];
  const found = paths.filter(Boolean).find(p => fs.existsSync(p));
  if (!found) throw new Error('No local Chrome/Edge found. Set CODEX_VIS_BROWSER_EXECUTABLE to an existing browser.');
  return found;
}

export async function checkVisualLayout(options) {
  const source = fs.readFileSync(options.input, 'utf8');
  if (Buffer.byteLength(source) > 16 * 1024 * 1024) throw new Error('SVG exceeds the 16 MiB local inspection limit.');
  const report = {
    checker_version: VERSION, input: path.resolve(options.input), viewport: { width: options.width, height: 900 },
    status: 'structural-only', acceptance: 'Automated geometry only; pass is not visual or business acceptance.', coverage: { level: 'none', scope: 'SVG geometry only; no business semantics' },
    unsupported: [], manual_checks: MANUAL_CHECKS, issues: [],
    security: { scripts_disabled: true, foreign_object_allowed: false, external_resources_allowed: false, blocked_requests: 0 },
  };
  if (/<!ENTITY\b|<!DOCTYPE[^>]*\[/i.test(source)) {
    report.unsupported.push('XML entities/internal DTD subsets are rejected before browser parsing.');
    return report;
  }
  const browser = await runtime().launch({ executablePath: browserExecutable(), headless: true, args: ['--disable-gpu'] });
  try {
    const context = await browser.newContext({ viewport: report.viewport, javaScriptEnabled: false, serviceWorkers: 'block', acceptDownloads: false });
    await context.route('**/*', route => {
      // Input is inlined. There is no reason to fetch even another local file.
      // This is stricter than the file/data/blob/about scheme ceiling.
      report.security.blocked_requests++;
      return route.abort('blockedbyclient');
    });
    const page = await context.newPage();
    await page.setContent('<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'none\'; style-src \'unsafe-inline\'; img-src data:; font-src \'none\'; object-src \'none\'; base-uri \'none\'"><style>html,body{margin:0;background:white}body>svg{display:block;max-width:100%;height:auto}</style><body></body>');
    const safety = await page.evaluate(svgSource => {
      const doc = new DOMParser().parseFromString(svgSource, 'image/svg+xml');
      if (doc.querySelector('parsererror') || doc.documentElement.localName !== 'svg') return { rejected: ['Invalid SVG/XML.'] };
      const rejected = [];
      const dangerous = new Set(['script', 'foreignobject', 'iframe', 'object', 'embed', 'audio', 'video', 'animate', 'animatemotion', 'animatetransform', 'set', 'discard']);
      const safeRef = value => /^#[\w:.-]+$/.test(value.trim()) || /^data:image\/(png|jpe?g|gif|webp);base64,[a-z\d+/=\s]+$/i.test(value.trim());
      for (const element of [doc.documentElement, ...doc.querySelectorAll('*')]) {
        if (dangerous.has(element.localName.toLowerCase())) rejected.push(`Disallowed SVG element: ${element.localName}`);
        if (element.namespaceURI !== 'http://www.w3.org/2000/svg') rejected.push(`Unsupported element namespace: ${element.localName}`);
        for (const attr of element.attributes) {
          const name = attr.localName.toLowerCase(), value = attr.value;
          if (name.startsWith('on')) rejected.push(`Disallowed event attribute: ${attr.name}`);
          if (['href', 'src'].includes(name) && !safeRef(value)) rejected.push(`External/unsafe reference on ${element.localName}.${name}`);
          if (/javascript\s*:|@import\b/i.test(value)) rejected.push(`Unsafe resource/style attribute: ${attr.name}`);
          for (const match of value.matchAll(/url\(\s*["']?([^)'"\s]+)["']?\s*\)/gi)) {
            if (!safeRef(match[1])) rejected.push(`External/unsafe CSS resource: ${attr.name}`);
          }
        }
        if (element.localName === 'style') {
          if (/@import\b|javascript\s*:/i.test(element.textContent)) rejected.push('External/unsafe stylesheet.');
          for (const match of element.textContent.matchAll(/url\(\s*["']?([^)'"\s]+)["']?\s*\)/gi)) {
            if (!safeRef(match[1])) rejected.push('External/unsafe stylesheet resource.');
          }
        }
      }
      if (rejected.length) return { rejected: [...new Set(rejected)] };
      document.body.append(document.importNode(doc.documentElement, true));
      return { rejected: [] };
    }, source);
    if (safety.rejected.length) {
      report.unsupported.push(...safety.rejected, 'Input was not inserted or rendered; no geometry acceptance was performed.');
      return report;
    }
    await page.evaluate(async () => {
      document.body.getBoundingClientRect();
      await document.fonts.ready;
    });
    const geometry = await page.evaluate(() => {
      const svg = document.body.querySelector('svg'), issues = [], unsupported = [];
      const nodeSelector = '[data-visual-node],g.node';
      const regionSelector = '[data-visual-region],g.cluster';
      const edgeSelector = '[data-visual-edge],g.edge,g.edgePath';
      const ownerSelector = `${nodeSelector},${regionSelector},${edgeSelector}`;
      const round = n => Math.round(n * 100) / 100;
      const box = element => {
        const r = element.getBoundingClientRect();
        return { x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, bottom: r.bottom };
      };
      const shown = el => {
        const s = getComputedStyle(el), r = box(el);
        return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) !== 0 && (r.width > 0 || r.height > 0);
      };
      const area = el => { const r = box(el); return r.width * r.height; };
      function owner(el, group) { return el.closest(ownerSelector) === group; }
      function idOf(group, index, kind) {
        return group.getAttribute(`data-visual-${kind}`) || [...group.children].find(el => el.localName === 'title')?.textContent || group.id || `${kind}-${index + 1}`;
      }
      function primaryShape(group, selector) {
        const shapes = [...group.querySelectorAll('rect,ellipse,circle,polygon,path')].filter(el =>
          owner(el, group, selector) && !el.closest('defs,marker,clipPath,mask') && shown(el) && typeof el.isPointInFill === 'function');
        const explicit = shapes.filter(el => el.hasAttribute('data-visual-shape'));
        if (explicit.length > 1) return null;
        return explicit[0] || shapes.filter(el => el.matches('.label-container,.outer,.basic')).sort((a,b) => area(b) - area(a))[0]
          || shapes.sort((a,b) => area(b) - area(a))[0] || null;
      }
      function contains(shape, x, y) {
        try {
          const matrix = shape.getScreenCTM();
          if (!matrix) return false;
          return shape.isPointInFill(new DOMPoint(x, y).matrixTransform(matrix.inverse()));
        } catch { return false; }
      }
      function textPoints(text, inset = 0) {
        const b = text.getBBox(), m = text.getScreenCTM();
        if (!m) return [];
        const points = [[b.x,b.y], [b.x+b.width,b.y], [b.x+b.width,b.y+b.height], [b.x,b.y+b.height], [b.x+b.width/2,b.y], [b.x+b.width/2,b.y+b.height]]
          .map(([x,y]) => new DOMPoint(x,y).matrixTransform(m));
        const center = new DOMPoint(b.x+b.width/2,b.y+b.height/2).matrixTransform(m);
        return points.map(p => ({ x: p.x + Math.sign(center.x-p.x)*Math.min(inset,Math.abs(center.x-p.x)), y: p.y + Math.sign(center.y-p.y)*Math.min(inset,Math.abs(center.y-p.y)) }));
      }
      const nodeGroups = [...svg.querySelectorAll(nodeSelector)];
      const regionGroups = [...svg.querySelectorAll(regionSelector)];
      const nodes = [], regions = [];
      for (const [kind, groups, selector, result] of [['node',nodeGroups,nodeSelector,nodes], ['region',regionGroups,regionSelector,regions]]) {
        groups.forEach((group,i) => {
          const id = idOf(group,i,kind), shape = primaryShape(group,selector);
          if (!shape) { unsupported.push(`${kind} ${id}: no unambiguous supported primary shape.`); return; }
          const texts = [...group.querySelectorAll('text')].filter(el => owner(el,group,selector) && shown(el) && el.textContent.trim());
          result.push({ id, group, shape, texts, box: box(shape) });
          // Region titles may sit on the boundary; only explicit node labels use containment.
          if (kind === 'node') for (const text of texts) {
            const points = textPoints(text,1.5);
            if (points.length && points.some(p => !contains(shape,p.x,p.y))) issues.push({
              type:'text-overflow', severity:'error', confidence:'high', node:id,
              text:text.textContent.trim(), message:'Rendered text extends beyond its primary shape (1.5 px tolerance).',
              text_bounds:box(text), shape_bounds:box(shape),
            });
          }
          if (kind === 'node' && group.querySelector(nodeSelector)) unsupported.push(`${kind} ${id}: nested node semantics require manual review.`);
        });
      }
      function intersection(a,b) {
        const x=Math.max(a.x,b.x), y=Math.max(a.y,b.y), right=Math.min(a.right,b.right), bottom=Math.min(a.bottom,b.bottom);
        return right-x>2 && bottom-y>2 ? {x,y,width:right-x,height:bottom-y} : null;
      }
      // Bounding-box overlap alone is insufficient for diamonds/circles; sample actual fills.
      function fillsOverlap(a,b) {
        const r=intersection(a.box,b.box); if (!r) return false;
        let shared=0;
        for (let x=1;x<=7;x++) for(let y=1;y<=7;y++) {
          const px=r.x+r.width*x/8, py=r.y+r.height*y/8;
          if (contains(a.shape,px,py) && contains(b.shape,px,py)) shared++;
        }
        return shared>=3;
      }
      for(let i=0;i<nodes.length;i++) for(let j=i+1;j<nodes.length;j++) {
        const a=nodes[i],b=nodes[j];
        if (a.group.contains(b.group)||b.group.contains(a.group)) continue;
        if (fillsOverlap(a,b)) issues.push({type:'node-overlap',severity:'error',confidence:'high',nodes:[a.id,b.id],message:'Distinct node shapes have overlapping interiors.'});
      }
      const edges=[...svg.querySelectorAll(edgeSelector)], edgeLabels=[];
      let checkedEdges=0;
      const routes=[],sampledRoutes=[];
      // Exact centerline intersections for one continuous M/L/H/V path only.
      // Curves, disconnected subpaths, stroke width and bridge symbolism need human review.
      const eps=0.01, near=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y)<eps;
      const cross=(a,b)=>a.x*b.y-a.y*b.x;
      const sub=(a,b)=>({x:a.x-b.x,y:a.y-b.y});
      function linearPoints(line) {
        const d=line.getAttribute('d')||'', tokens=d.match(/[a-zA-Z]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?/g)||[];
        if(d.replace(/[a-zA-Z]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?|[\s,]/g,'') || !tokens.length) return null;
        let at=0,command='',x=0,y=0,points=[];
        while(at<tokens.length) {
          if(/^[a-zA-Z]$/.test(tokens[at])) command=tokens[at++];
          const c=command.toUpperCase(), relative=command!==c;
          if(!['M','L','H','V'].includes(c) || (c==='M' && points.length)) return null;
          const count=c==='H'||c==='V'?1:2;
          if(at+count>tokens.length || tokens.slice(at,at+count).some(t=>/^[a-zA-Z]$/.test(t))) return null;
          const a=Number(tokens[at++]), b=count===2?Number(tokens[at++]):0;
          if(c==='M'||c==='L') {x=relative?x+a:a;y=relative?y+b:b;}
          if(c==='H') x=relative?x+a:a;
          if(c==='V') y=relative?y+a:a;
          const point=new DOMPoint(x,y).matrixTransform(line.getScreenCTM());
          if(!points.length||!near(points.at(-1),point)) points.push({x:point.x,y:point.y});
          if(c==='M') command=relative?'l':'L';
        }
        return points.length>1?points:null;
      }
      function segmentHits(a,b,c,d) {
        const r=sub(b,a),t=sub(d,c),v=sub(c,a),den=cross(r,t);
        if(Math.abs(den)>1e-8) {
          const u=cross(v,t)/den,w=cross(v,r)/den;
          return u>=-1e-8&&u<=1+1e-8&&w>=-1e-8&&w<=1+1e-8?[{x:a.x+u*r.x,y:a.y+u*r.y}]:[];
        }
        if(Math.abs(cross(v,r))>eps*Math.hypot(r.x,r.y)) return [];
        const rr=r.x*r.x+r.y*r.y, project=p=>((p.x-a.x)*r.x+(p.y-a.y)*r.y)/rr;
        const lo=Math.max(0,Math.min(project(c),project(d))),hi=Math.min(1,Math.max(project(c),project(d)));
        if(hi<lo-1e-8) return [];
        return [lo,(lo+hi)/2,hi].map(u=>({x:a.x+u*r.x,y:a.y+u*r.y}));
      }
      function simplify(points) {
        const out=[];
        for(const p of points) {
          if(out.length&&near(out.at(-1),p)) continue;
          while(out.length>1) {
            const a=out.at(-2),b=out.at(-1),u=sub(b,a),v=sub(p,b);
            if(Math.abs(cross(u,v))>eps || u.x*v.x+u.y*v.y<0) break;
            out.pop();
          }
          out.push(p);
        }
        return out;
      }
      function tail(points,index,p) {return simplify([p,...points.slice(index+1)]);}
      function equalRoute(a,b) {return a.length===b.length&&a.every((p,i)=>near(p,b[i]));}
      function expectedJunction(a,b,i,j,p) {
        const aPorts=[[a.from,a.points[0]],[a.to,a.points.at(-1)]],bPorts=[[b.from,b.points[0]],[b.to,b.points.at(-1)]];
        if(aPorts.some(([id,point])=>near(point,p)&&bPorts.some(([other,q])=>id===other&&near(q,p)))) return true;
        // Sharing a logical node alone does not exempt a crossing elsewhere.
        // Only an identical route from the contact to that common port is exempt.
        if(a.to===b.to&&equalRoute(tail(a.points,i,p),tail(b.points,j,p))) return true;
        if(a.from===b.from&&equalRoute(simplify([p,...a.points.slice(0,i+1).reverse()]),simplify([p,...b.points.slice(0,j+1).reverse()]))) return true;
        return false;
      }
      let checkedPairs=0,exactPairs=0,sampledPairs=0,expectedJunctions=0,segmentComparisons=0,budgetExceeded=false;
      edges.forEach((group,i)=>{
        const id=idOf(group,i,'edge');
        const title=[...group.children].find(el=>el.localName==='title')?.textContent || '';
        const gv=title.match(/^(.+?)->(.+?)(?::[^:]*)?$/);
        const from=group.getAttribute('data-from') || gv?.[1], to=group.getAttribute('data-to') || gv?.[2];
        const labels=[...group.querySelectorAll('text')].filter(shown);
        labels.forEach(text=>edgeLabels.push({edge:id,text,box:box(text)}));
        if (!from || !to || !nodes.some(n=>n.id===from) || !nodes.some(n=>n.id===to)) {
          unsupported.push(`edge ${id}: missing/resolved endpoints; crossings are not inferred from proximity.`); return;
        }
        const lines=[...group.querySelectorAll('path[data-visual-line],path')].filter(el=>!el.closest('defs,marker') && shown(el));
        if (!lines.length) { unsupported.push(`edge ${id}: no measurable path.`); return; }
        checkedEdges++;
        const points=lines.length===1&&!group.querySelector('line,polyline')?linearPoints(lines[0]):null;
        if(points) routes.push({id,from,to,points});
        else if(lines.length===1) {
          const line=lines[0],length=line.getTotalLength(),matrix=line.getScreenCTM();
          if(length&&matrix) {
            const count=Math.min(240,Math.max(16,Math.ceil(length/6))),sampled=[];
            for(let k=0;k<=count;k++) {const p=line.getPointAtLength(length*k/count).matrixTransform(matrix);sampled.push({x:p.x,y:p.y});}
            sampledRoutes.push({id,from,to,points:sampled,approximate:true});
          }
        }
        if(!points) unsupported.push(`edge ${id}: exact edge-to-edge intersections unmeasured; single curves may have sampled candidates, while multi-path edges remain unmeasured. Manual review required.`);
        for(const region of regions) for(const label of region.texts) {
          const r=box(label); let crossesLabel=false;
          for(const line of lines) {
            const len=line.getTotalLength(),m=line.getScreenCTM(); if(!m || !len) continue;
            const samples=Math.min(600,Math.max(12,Math.ceil(len/4))); let hits=0;
            for(let s=1;s<samples;s++) {
              const p=line.getPointAtLength(len*s/samples).matrixTransform(m);
              if(p.x>r.x+1 && p.x<r.right-1 && p.y>r.y+1 && p.y<r.bottom-1) hits++;
            }
            if(hits>=2) crossesLabel=true;
          }
          if(crossesLabel) issues.push({type:'edge-cross-label',severity:'review',confidence:'heuristic',edge:id,region:region.id,
            text:label.textContent.trim(),message:'Sampled edge path crosses region-title bounds; inspect the glyphs and intended route.'});
        }
        for(const node of nodes.filter(n=>n.id!==from && n.id!==to)) {
          let crossing=false;
          for(const line of lines) {
            const len=line.getTotalLength(), m=line.getScreenCTM(); if(!m || !len) continue;
            const samples=Math.min(600,Math.max(12,Math.ceil(len/4))); let hits=0;
            for(let s=1;s<samples;s++) {
              const p=line.getPointAtLength(len*s/samples).matrixTransform(m);
              if(contains(node.shape,p.x,p.y)) hits++;
            }
            if(hits>=2) crossing=true;
          }
          if(crossing) issues.push({type:'edge-cross-node',severity:'review',confidence:'heuristic',edge:id,node:node.id,message:'Sampled edge path enters a non-endpoint node; inspect visually before changing it.'});
          for(const text of labels) if(textPoints(text).some(p=>contains(node.shape,p.x,p.y))) issues.push({type:'edge-label-overlap',severity:'review',confidence:'heuristic',edge:id,node:node.id,message:'An edge label may overlap a non-endpoint node.'});
        }
      });
      const candidateRoutes=[...routes,...sampledRoutes];
      for(let a=0;a<candidateRoutes.length;a++) for(let b=a+1;b<candidateRoutes.length;b++) {
        const first=candidateRoutes[a],second=candidateRoutes[b],findings=[],approximate=first.approximate||second.approximate;
        if(budgetExceeded) continue;
        checkedPairs++; if(approximate) sampledPairs++; else exactPairs++;
        for(let i=0;i<first.points.length-1&&!budgetExceeded;i++) for(let j=0;j<second.points.length-1&&!budgetExceeded;j++) {
          if(++segmentComparisons>500000) {budgetExceeded=true;continue;}
          for(const p of segmentHits(first.points[i],first.points[i+1],second.points[j],second.points[j+1])) {
            if(expectedJunction(first,second,i,j,p)) {expectedJunctions++;continue;}
            if(!findings.some(q=>near(p,q))) findings.push(p);
          }
        }
        if(findings.length) issues.push({type:'edge-edge-crossing',severity:'review',confidence:approximate?'heuristic':'geometric',edges:[first.id,second.id],
          points:findings.map(p=>({x:round(p.x),y:round(p.y)})),
          message:'Distinct edge centerlines intersect/touch/overlap outside a verified shared port or common trunk. Check whether accidental, an explicit junction, or a deliberate crossover; geometry alone cannot decide intent.'});
      }
      for(let i=0;i<edgeLabels.length;i++) for(let j=i+1;j<edgeLabels.length;j++) {
        if(edgeLabels[i].edge===edgeLabels[j].edge) continue;
        if(intersection(edgeLabels[i].box,edgeLabels[j].box)) issues.push({type:'edge-label-overlap',severity:'review',confidence:'heuristic',edges:[edgeLabels[i].edge,edgeLabels[j].edge],message:'Edge label bounds overlap; check the actual glyphs.'});
      }
      if(budgetExceeded) unsupported.push('Edge-pair segment-comparison budget exceeded; some pairs/segments were not checked.');
      const allText=[...svg.querySelectorAll('text')].filter(el=>shown(el) && el.textContent.trim());
      const mappedText=new Set([...nodes,...regions].flatMap(n=>n.texts).concat(edgeLabels.map(l=>l.text)));
      const unmappedText=allText.filter(t=>!mappedText.has(t)).length;
      if(unmappedText) unsupported.push(`${unmappedText} visible text element(s) lack a recognized node/region/edge owner.`);
      const ungroupedPaths=[...svg.querySelectorAll('path,line,polyline')].filter(el=>!el.closest('defs,marker,clipPath,mask') && !el.closest(ownerSelector) && shown(el) && getComputedStyle(el).stroke!=='none').length;
      if(ungroupedPaths) unsupported.push('Visible stroked paths/lines outside recognized owners are unmeasured; edge-pair coverage is incomplete.');
      
      if(!nodes.length) unsupported.push('No recognized node geometry: use Graphviz g.node or explicit data-visual-node groups.');
      if(svg.querySelector('g.actor,g[class*="entity"],g.stateGroup,.stateDiagram,.sequenceDiagram,.erDiagram')) unsupported.push('State/ER/sequence geometry has partial coverage; diagram-specific semantics and unrecognized shapes require manual review.');
      if(svg.querySelector('filter,mask,clipPath,use,image,textPath')) unsupported.push('Filters, clipping, masks, use/image/textPath effects are not fully represented by the geometry checks.');
      return {
        coverage:{ level:!nodes.length?'none':unsupported.length?'partial':'geometry',scope:'SVG geometry only; no business semantics',
          fonts_ready:document.fonts.status==='loaded',rendered_svg_bounds:box(svg),recognized_node_groups:nodeGroups.length,checked_nodes:nodes.length,
          recognized_regions:regionGroups.length,checked_regions:regions.length,recognized_edge_groups:edges.length,checked_edges:checkedEdges,
          visible_text_elements:allText.length,unmapped_text_elements:unmappedText,
          edge_pair_checks:{method:'exact centerline intersections for continuous M/L/H/V paths; bounded sampled candidates for single curves',
            recognized_edges:edges.length,supported_routes:routes.length,sampled_routes:sampledRoutes.length,checked_pairs:checkedPairs,exact_pairs:exactPairs,sampled_pairs:sampledPairs,segment_comparisons:Math.min(segmentComparisons,500000),budget_exceeded:budgetExceeded,expected_junctions:expectedJunctions,
            complete:routes.length===edges.length&&!ungroupedPaths&&!budgetExceeded,
            limitations:['Curves only produce sampled heuristic candidates; tangencies or small crossings can be missed. Multi-path and unrecognized edges remain unmeasured.','Stroke width, arrowheads, self-crossings, edge-to-label clearance, jumps/bridges and intended junction semantics require manual review.','Shared logical endpoints only exempt identical common routes to the same port.']},
          node_bounds:nodes.map(n=>({id:n.id,...Object.fromEntries(Object.entries(n.box).map(([k,v])=>[k,round(v)]))})),
          checks:{text_containment:'actual rendered SVG text bounds against primary shape fill',node_overlap:'actual shape-fill samples within intersecting bounds',edge_node_crossings:'heuristic path samples against non-endpoint node fills',edge_crossings:'edge-to-edge centerline checks; see edge_pair_checks coverage and limitations',region_titles:'heuristic path samples against title bounds; containment not enforced'} },
        issues,unsupported:[...new Set(unsupported)],
      };
    });
    Object.assign(report,geometry);
    report.status = report.issues.some(issue=>issue.severity==='error') ? 'revise'
      : report.coverage.level === 'geometry' && !report.issues.length ? 'pass' : 'structural-only';
    if (options.screenshot) {
      fs.mkdirSync(path.dirname(options.screenshot),{recursive:true});
      await page.screenshot({path:options.screenshot,fullPage:true});
      report.screenshot=path.resolve(options.screenshot);
    }
    return report;
  } finally { await browser.close(); }
}

async function main() {
  try {
    const options=parseArgs(process.argv.slice(2));
    if(!options) { console.log('Usage: node check_visual_layout.mjs input.svg [--width 1000] [--output report.json] [--screenshot preview.png]'); return; }
    const report=await checkVisualLayout(options), json=JSON.stringify(report,null,2)+'\n';
    if(options.output) { fs.mkdirSync(path.dirname(options.output),{recursive:true}); fs.writeFileSync(options.output,json); }
    process.stdout.write(json);
    process.exitCode={pass:0,revise:2,'structural-only':3}[report.status];
  } catch(error) {
    process.stderr.write(`Layout check failed: ${error.message}\n`);
    process.exitCode=1;
  }
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) await main();
