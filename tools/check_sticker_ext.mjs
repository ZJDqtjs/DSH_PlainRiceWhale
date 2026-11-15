/**
 * Assert that the two halves and the asset folder agree on which stickers ship.
 *
 * `MOOD_STICKERS` (Host) builds the route whitelist; `STICKER_ASSETS` (Client) builds
 * the `<img>` src. They live in separate files with no shared module — a profile bundle
 * cannot import across the Host/Client boundary — so a drifting list means either a 404
 * or a dead file. This also walks the folder itself, because a GIF that was retired but
 * left behind, or a zip dropped into the asset dir, is exactly the kind of drift that
 * silently breaks the bubble.
 *
 * Usage: `node tools/check_sticker_ext.mjs`
 */
import { readFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join, basename } from 'node:path';

const BASE = join(dirname(fileURLToPath(import.meta.url)), '..');
const ASSET_DIR = join(BASE, 'whale-aside', 'assets', 'gifs');

function sliceTo(source, anchor, open, close) {
  const at = source.indexOf(anchor);
  if (at === -1) throw new Error('anchor not found: ' + anchor);
  const from = source.indexOf(open, at);
  const to = from === -1 ? -1 : source.indexOf(close, from + 1);
  if (from === -1 || to === -1) throw new Error('unterminated list after: ' + anchor);
  return source.slice(from + 1, to);
}

/** Parse a `key: 'value'` object body without importing the module. */
function objectEntries(body) {
  return [...body.matchAll(/([a-z_]+)\s*:\s*'([^']+)'/g)].map((m) => [m[1], m[2]]);
}

const quoted = (body) => [...body.matchAll(/'([a-z]+)'/g)].map((m) => m[1]);

const host = await readFile(join(BASE, 'whale-aside', 'index.js'), 'utf8');
const client = await readFile(join(BASE, 'whale-aside', 'client.js'), 'utf8');

const moods = quoted(sliceTo(host, 'const MOODS =', '[', ']'));
const hostStickers = objectEntries(sliceTo(host, 'const MOOD_STICKERS =', '{', '}'));
const clientStickers = objectEntries(sliceTo(client, 'const STICKER_ASSETS =', '{', '}'));
const version = (client.match(/const GIF_VERSION = '([^']+)'/) ?? [])[1];

const problems = [];

// 1. both lists must name the same file for the same mood
const hostMap = new Map(hostStickers);
const clientMap = new Map(clientStickers);
if (hostMap.size === 0) problems.push('MOOD_STICKERS is empty — nothing ships a sticker');
for (const [mood, file] of clientMap) {
  if (moods.indexOf(mood) === -1) problems.push(`Client sticker for unknown mood ${mood}`);
  if (hostMap.get(mood) !== 'gifs/' + file) {
    problems.push(`mood ${mood}: Host serves ${hostMap.get(mood) ?? '(nothing)'}, Client asks gifs/${file}`);
  }
}
for (const [mood, rel] of hostMap) {
  if (!clientMap.has(mood)) problems.push(`Host ships ${rel} but the Client never asks for it (mood ${mood})`);
}

// 2. rebuild the route whitelist the same way index.js does and probe it
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const pattern = new RegExp('^(' + [...hostMap.values()].map(escapeRe).join('|') + ')$');
for (const rel of hostMap.values()) {
  if (pattern.test(rel) === false) problems.push(`whitelist rejects its own entry ${rel}`);
}
for (const probe of ['gifs/tsun.gif', 'gifs/smus.gif', 'gifs/meh.jpg', 'gifs/gifs.zip',
                     'gifs/../index.js', 'gifs/meme2_clean.png/../../index.js', 'index.js']) {
  if (pattern.test(probe) === true) problems.push(`whitelist wrongly accepts ${probe}`);
}

// 3. the folder must contain exactly the shipped files, plus the attribution note
const onDisk = (await readdir(ASSET_DIR)).filter((n) => !n.startsWith('.'));
const wanted = new Set([...hostMap.values()].map((rel) => basename(rel)));
wanted.add('SOURCES.md');
for (const name of onDisk) {
  if (wanted.has(name) === false) problems.push(`orphan in assets/gifs: ${name}`);
}
for (const name of wanted) {
  if (onDisk.indexOf(name) === -1) problems.push(`missing from assets/gifs: ${name}`);
}

console.log('moods (tool + voice) :', moods.join(' '));
console.log('stickers shipped     :', [...hostMap.entries()].map(([m, r]) => m + '→' + r).join(' ') || '(none)');
console.log('files on disk        :', onDisk.join(' '));
console.log('GIF_VERSION          :', version);
if (problems.length > 0) {
  console.error('FAIL\n  ' + problems.join('\n  '));
  process.exit(1);
}
console.log('OK: Host list, Client list and the asset folder agree; retired files are gone and unreachable.');
