"""Offline harness for the voice route: exercise serveVoice without DSH.

Replaces the `node:` imports with stubs is unnecessary (they are real builtins),
so this just imports the plugin module and drives the registered handlers with
fake req/res objects. It never touches the running Harness.
"""
import asyncio
import json
import os
import sys
import time
import types

sys.stdout.reconfigure(encoding='utf-8')

PLUGIN = r'D:\code\DSH_PlainRiceWhale\whale-aside\index.js'
src = open(PLUGIN, encoding='utf-8').read()
mod = types.ModuleType('whale_aside_plugin')
mod.__file__ = PLUGIN
exec(compile(src, PLUGIN, 'exec'), mod.__dict__)

routes = []


class FakeWebServer:
    def register(self, route):
        routes.append(route)
        return lambda: None


class FakeTools:
    def register(self, definition):
        return lambda: None


class FakePrompt:
    def section(self, section):
        return lambda: None


class FakeCtx:
    def __init__(self):
        self.tools = FakeTools()
        self.systemPrompt = FakePrompt()
        self.webServer = FakeWebServer()

    def effect(self, factory):
        factory()


mod.apply(FakeCtx())
print('routes:', [(r['kind'], r['path']) for r in routes])
handler = [r for r in routes if r['path'] == '/whale-aside/voice'][0]['handler']


class Res:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.chunks = []

    def writeHead(self, status, headers=None):
        self.status = status
        self.headers = dict(headers or {})

    def end(self, body=None):
        if body is not None:
            self.chunks.append(body if isinstance(body, bytes) else str(body).encode())

    @property
    def body(self):
        return b''.join(self.chunks)


class GetReq:
    def __init__(self, path):
        self.method = 'GET'
        self.url = path

    def on(self, *args):
        pass


class PostReq:
    def __init__(self, path, payload):
        self.method = 'POST'
        self.url = path
        self.payload = payload
        self.events = {}

    def on(self, event, cb):
        self.events.setdefault(event, []).append(cb)


def run_get(path):
    res = Res()
    asyncio.run(handler(GetReq(path), res))
    return res


def run_post(path, payload):
    res = Res()
    req = PostReq(path, payload)
    body = json.dumps(payload).encode()

    async def go():
        task = asyncio.create_task(handler(req, res))
        await asyncio.sleep(0.05)
        for cb in req.events.get('data', []):
            cb(body)
        for cb in req.events.get('end', []):
            cb()
        await task

    asyncio.run(go())
    return res


print()
print('--- GET /whale-aside/voice ---')
r = run_get('/whale-aside/voice')
print('status', r.status, 'body', r.body.decode()[:200])

print()
print('--- POST synthesize (tsun) ---')
t0 = time.time()
r = run_post('/whale-aside/voice', {'text': '哼，主人又来了…才没有在等你呢。', 'mood': 'tsun'})
print('status', r.status, 'elapsed %.2fs' % (time.time() - t0))
print('body', r.body.decode()[:400])

if r.status == 200:
    info = json.loads(r.body)
    url = info['url']
    print()
    print('--- GET clip', url, '---')
    t1 = time.time()
    r2 = run_get(url)
    print('status', r2.status, 'bytes', len(r2.body), 'magic', r2.body[:2], 'elapsed %.3fs' % (time.time() - t1))
    print()
    print('--- GET same clip again (cache) ---')
    t2 = time.time()
    r3 = run_get(url)
    print('status', r3.status, 'bytes', len(r3.body), 'elapsed %.3fs' % (time.time() - t2))
    print()
    print('--- HEAD clip ---')
    r4 = Res()
    asyncio.run(handler(type('H', (), {'method': 'HEAD', 'url': url, 'on': lambda *a: None})(), r4))
    print('status', r4.status, 'bytes', len(r4.body))

print()
print('--- rejects ---')
for path, payload in (('/whale-aside/voice', {'text': '', 'mood': 'tsun'}),
                      ('/whale-aside/voice', {'text': 'x' * 400, 'mood': 'tsun'}),
                      ('/whale-aside/voice', {'mood': 'tsun'})):
    rr = run_post(path, payload)
    print(' payload', str(payload)[:40], '->', rr.status, rr.body.decode()[:120])

print()
print('--- traversal / bad path ---')
for p in ('/whale-aside/voice/../../index.js', '/whale-aside/voice/zzz.mp3', '/whale-aside/voice/'):
    rr = run_get(p)
    print(' ', p, '->', rr.status, rr.body.decode()[:100])
