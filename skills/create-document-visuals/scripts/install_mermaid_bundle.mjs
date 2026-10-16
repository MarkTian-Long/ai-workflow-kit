#!/usr/bin/env node
// Explicit setup only: download one fixed public npm archive, verify it and
// extract only the integrity-checked standalone bundle. No credentials or npm
// install scripts, no global configuration, and no overwrite of prior files.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import { fileURLToPath } from 'node:url';

const ARCHIVE_URL = 'https://registry.npmjs.org/mermaid/-/mermaid-12.2.0.tgz';
const ARCHIVE_SHA512 = 'w7nr/SFrLO7BaVTs3dQTvYSV6nYSBj0Yy9DjBhsIJtAcHqRzXSq4Pg32ujHZ/AdWsAMNEvvhbm5dt9E2tOiHzw==';
const BUNDLE_SHA256 = 'a8a6a6f805b074a8261a2825c86f99c8054acb3b35f50bb7e24a4f9f2c3c3b9f';
const BUNDLE_BYTES = 5494801;
const HERE = path.dirname(fileURLToPath(import.meta.url));
const TARGET = path.resolve(HERE, '../assets/vendor/mermaid/mermaid.min.js');
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

export function bundleFromArchive(archive) {
  if (crypto.createHash('sha512').update(archive).digest('base64') !== ARCHIVE_SHA512) throw new Error('Official archive integrity mismatch.');
  const tar = gunzipSync(archive, { maxOutputLength: 160 * 1024 * 1024 });
  for (let offset = 0; offset + 512 <= tar.length;) {
    const header = tar.subarray(offset, offset + 512);
    if (header.every(value => value === 0)) break;
    const name = header.subarray(0, 100).toString('utf8').split('\0')[0];
    const prefix = header.subarray(345, 500).toString('utf8').split('\0')[0];
    const entry = prefix ? `${prefix}/${name}` : name;
    const size = parseInt(header.subarray(124, 136).toString('ascii').replace(/\0/g, '').trim(), 8);
    if (!Number.isSafeInteger(size) || size < 0 || offset + 512 + size > tar.length) throw new Error('Invalid archive entry.');
    if (entry === 'package/dist/mermaid.min.js') {
      if (![0, 48].includes(header[156])) throw new Error('Bundle entry is not a regular file.');
      const bytes = tar.subarray(offset + 512, offset + 512 + size);
      if (bytes.length !== BUNDLE_BYTES || digest(bytes) !== BUNDLE_SHA256) throw new Error('Standalone bundle integrity mismatch.');
      return bytes;
    }
    offset += 512 + Math.ceil(size / 512) * 512;
  }
  throw new Error('Standalone bundle not found in fixed archive.');
}

async function install() {
  try {
    const existing = await fs.readFile(TARGET);
    if (digest(existing) !== BUNDLE_SHA256) throw new Error('Existing bundle differs; preserve and review it before replacing.');
    return { status: 'already-present', version: '12.2.0', target: TARGET, sha256: BUNDLE_SHA256 };
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  if (!process.argv.includes('--download')) throw new Error('Bundle is absent. Explicit setup: node install_mermaid_bundle.mjs --download');
  const response = await fetch(ARCHIVE_URL, { redirect: 'error', signal: AbortSignal.timeout(45000) });
  if (!response.ok) throw new Error(`Official npm download failed: HTTP ${response.status}.`);
  const chunks = []; let downloaded = 0;
  for await (const chunk of response.body) {
    downloaded += chunk.length;
    if (downloaded > 30 * 1024 * 1024) throw new Error('Archive exceeds the fixed download limit.');
    chunks.push(chunk);
  }
  const bundle = bundleFromArchive(Buffer.concat(chunks));
  await fs.mkdir(path.dirname(TARGET), { recursive: true });
  const staged = `${TARGET}.${crypto.randomUUID()}.tmp`;
  try {
    await fs.writeFile(staged, bundle, { flag: 'wx' });
    await fs.link(staged, TARGET);
  } finally { await fs.unlink(staged).catch(() => {}); }
  return { status: 'installed', version: '12.2.0', target: TARGET, bytes: bundle.length, sha256: BUNDLE_SHA256, downloaded_bytes: downloaded };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { process.stdout.write(`${JSON.stringify(await install())}\n`); }
  catch (error) { process.stderr.write(`${error.message}\n`); process.exitCode = 1; }
}
