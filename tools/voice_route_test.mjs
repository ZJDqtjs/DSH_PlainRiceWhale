/**
 * End-to-end harness for the plugin's HTTP routes, without DSH.
 *
 * Imports the real Host half (it only depends on node: builtins), captures the
 * routes it registers, serves them from a throwaway http server on localhost,
 * and exercises them with real fetch calls.
 */
import http from 'node:http';
import { pathToFileURL } from 'node:url';

const PLUGIN = 'D:/code/DSH_PlainRiceWhale/whale-aside/index.js';

const routes = [];
const ctx = {
  systemPrompt: { section: () => () => {} },
  tools: { register: () => () => {} },
  webServer: {
    register(route) {
      routes.push(route);
      return () => {};
    },
  },
  effect(factory) {
    factory();
  },
};

const plugin = await import(pathToFileURL(PLUGIN).href + '?t=' + Date.now());
plugin.apply(ctx);
console.log('routes:', routes.map((r) => `${r.kind} ${r.path}`).join(', '));

function pick(pathname) {
  let best = null;
  for (const route of routes) {
    if (route.kind === 'prefix') {
      if (pathname === route.path || pathname.startsWith(route.path + '/')) {
        if (best === null || route.path.length > best.path.length) best = route;
      }
    } else if (route.path === pathname) {
      best = route;
    }
  }
  return best;
}

const server = http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
  const route = pick(pathname);
  if (route === null) {
    res.writeHead(404).end();
    return;
  }
  Promise.resolve(route.handler(req, res)).catch((error) => {
    try {
      res.writeHead(500).end(String(error));
    } catch (ignored) {}
  });
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}`;
console.log('listening', base);

const api = (path, init) => fetch(base + path, init);

console.log('\n--- GET /whale-aside/voice ---');
{
  const r = await api('/whale-aside/voice');
  console.log('status', r.status, 'ctype', r.headers.get('content-type'));
  console.log('body', JSON.stringify(await r.json()).slice(0, 240));
}

console.log('\n--- POST synthesize (tsun) ---');
let clipUrl = null;
{
  const t0 = Date.now();
  const r = await api('/whale-aside/voice', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ text: '哼，主人又来了…才没有在等你呢。', mood: 'tsun' }),
  });
  const ms = Date.now() - t0;
  console.log('status', r.status, 'elapsed', ms + 'ms');
  const body = await r.json();
  console.log('body', JSON.stringify(body).slice(0, 300));
  clipUrl = body.url;
}

if (clipUrl) {
  console.log('\n--- GET clip', clipUrl, '---');
  {
    const t0 = Date.now();
    const r = await api(clipUrl);
    const buf = Buffer.from(await r.arrayBuffer());
    console.log('status', r.status, 'ctype', r.headers.get('content-type'),
      'bytes', buf.length, 'magic', buf.subarray(0, 2).toString('hex'),
      'elapsed', (Date.now() - t0) + 'ms');
  }
  console.log('\n--- GET same clip again (disk cache) ---');
  {
    const t0 = Date.now();
    const r = await api(clipUrl);
    const buf = Buffer.from(await r.arrayBuffer());
    console.log('status', r.status, 'bytes', buf.length, 'elapsed', (Date.now() - t0) + 'ms');
  }
  console.log('\n--- HEAD clip ---');
  {
    const r = await api(clipUrl, { method: 'HEAD' });
    console.log('status', r.status, 'content-length', r.headers.get('content-length'));
  }
  console.log('\n--- POST same text again (cache hit) ---');
  {
    const t0 = Date.now();
    const r = await api('/whale-aside/voice', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ text: '哼，主人又来了…才没有在等你呢。', mood: 'tsun' }),
    });
    const body = await r.json();
    console.log('status', r.status, 'elapsed', (Date.now() - t0) + 'ms', 'same url', body.url === clipUrl);
  }
}

console.log('\n--- rejects ---');
for (const payload of [{ text: '', mood: 'tsun' }, { text: 'x'.repeat(400), mood: 'tsun' }, { mood: 'tsun' }]) {
  const r = await api('/whale-aside/voice', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const body = await r.json().catch(() => ({}));
  console.log(' payload', JSON.stringify(payload).slice(0, 36), '->', r.status, JSON.stringify(body).slice(0, 90));
}

console.log('\n--- bad paths ---');
for (const path of ['/whale-aside/voice/../../../index.js', '/whale-aside/voice/zzz.mp3', '/whale-aside/voice/']) {
  const r = await api(path);
  console.log(' ', path, '->', r.status);
}

console.log('\n--- gif route still works ---');
{
  const r = await api('/whale-aside/assets/gifs/tsun.gif');
  console.log('status', r.status, 'ctype', r.headers.get('content-type'), 'len', r.headers.get('content-length'));
}

server.close();
