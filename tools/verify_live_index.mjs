/**
 * Verify the LIVE index: fetch it over plain HTTPS with no credentials, validate the
 * fetched bytes with the official format-1 rule set, and print what a user would get.
 *
 * Checking the file in the working tree is not enough — Pages may serve a stale build,
 * a different path, or mangle the body. This reads exactly what the Host would read.
 *
 * Usage: node tools/verify_live_index.mjs [index URL]
 */
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const BASE = join(dirname(fileURLToPath(import.meta.url)), '..');
const INDEX_URL = process.argv[2] ?? 'https://zjdqtjs.github.io/DSH_PlainRiceWhale/market/index.json';

const validatorDir = join(BASE, '.work', 'validator', 'node_modules', '@deepseek-ai', 'dsh-plugin-market-index');
const { parseMarketIndex, marketInstallTarget } = await import(pathToFileURL(join(validatorDir, 'lib', 'index.js')).href);

const problems = [];

const res = await fetch(INDEX_URL, { headers: { 'user-agent': 'dsh-index-verify' } });
console.log(`GET ${INDEX_URL}`);
console.log(`  status      : ${res.status}`);
console.log(`  content-type: ${res.headers.get('content-type')}`);
console.log(`  cache       : ${res.headers.get('cache-control')}`);
if (res.ok === false) {
  console.error('LIVE index is not reachable');
  process.exit(1);
}
const body = await res.text();

let live;
try {
  live = JSON.parse(body);
} catch (error) {
  console.error(`live body is not JSON: ${error.message}`);
  process.exit(1);
}

let validated;
try {
  validated = parseMarketIndex(live, INDEX_URL);
} catch (error) {
  console.error(`LIVE INDEX INVALID: ${error.message}`);
  process.exit(1);
}

const local = JSON.parse(await readFile(join(BASE, 'docs', 'market', 'index.json'), 'utf8'));
if (JSON.stringify(local) !== JSON.stringify(live)) {
  problems.push('the served document differs from docs/market/index.json');
}

const plugin = validated.plugins[0];
const version = plugin.versions[0];
const target = marketInstallTarget(plugin.name, version);

const iconRes = await fetch(plugin.icon, { headers: { 'user-agent': 'dsh-index-verify' } });
if (iconRes.ok === false) problems.push(`icon ${plugin.icon} answered ${iconRes.status}`);

// The pinned commit must exist publicly AND contain the package the index names.
// Anonymous api.github.com is rate limited (403 for busy IPs), and a 403 there says
// nothing about reachability, so probe the raw file host at the commit instead.
const commit = version.source.commit;
const pkgUrl = `https://raw.githubusercontent.com/ZJDqtjs/DSH_PlainRiceWhale/${commit}/${version.source.path}/package.json`;
const pkgRes = await fetch(pkgUrl, { headers: { 'user-agent': 'dsh-index-verify' } });
if (pkgRes.ok === false) {
  problems.push(`pinned commit ${commit.slice(0, 12)} does not expose ${version.source.path}/package.json (${pkgRes.status})`);
} else {
  const pinned = JSON.parse(await pkgRes.text());
  if (pinned.name !== plugin.name) problems.push(`pinned package is ${pinned.name}, index says ${plugin.name}`);
  if (pinned.version !== version.version) problems.push(`pinned package is ${pinned.version}, index says ${version.version}`);
  console.log('  pinned pkg :', `${pinned.name}@${pinned.version} at ${commit.slice(0, 12)} (${pkgRes.status})`);
}

console.log('  format      :', validated.format);
console.log('  title langs :', Object.keys(validated.title).join('/'));
console.log('  plugin      :', plugin.name);
console.log('  version     :', version.version, '| publishTimestamp', version.publishTimestamp);
console.log('  source      :', version.source.type, version.source.url, `#${commit.slice(0, 12)}`, 'path', version.source.path);
console.log('  engines     :', JSON.stringify(version.engines));
console.log('  icon        :', plugin.icon, `(${iconRes.status})`);
console.log('  category    :', plugin.metadata.category, '| labels', plugin.metadata.labels.join(','));
console.log('  install     :', target.spec);
console.log('  served == repo file :', problems.some((p) => p.startsWith('the served')) === false);

if (problems.length > 0) {
  console.error('FAIL\n  ' + problems.join('\n  '));
  process.exit(1);
}
console.log('OK: the live index satisfies format 1 and its install target is publicly resolvable.');
