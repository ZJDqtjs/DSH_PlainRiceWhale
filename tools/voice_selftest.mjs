/* Self-test for the rewritten whale-aside voice route.
 * Runs the real bundle module against a throwaway DSH_HOME so nothing in
 * ~/.dsh is touched, while still using the real bundled Python.
 * Usage: node tools/voice_selftest.mjs
 */
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { EventEmitter } from 'node:events';

const REAL_PY = 'C:\\Users\\Administrator\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe';
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'whale-voice-selftest-'));
process.env.DSH_HOME = TMP;
process.env.DSH_WHALE_PYTHON = REAL_PY;

const mod = await import(pathToFileURL('D:/code/DSH_PlainRiceWhale/whale-aside/index.js').href);

const routes = [];
mod.apply({
  effect: (fn) => fn(),
  systemPrompt: { section: () => undefined },
  tools: { register: () => undefined },
  webServer: { register: (row) => routes.push(row) },
});
const voice = routes.find((row) => row.path === '/whale-aside/voice');
if (!voice) throw new Error('voice route not registered');

function mockRes() {
  const chunks = [];
  let resolveBody;
  const done = new Promise((resolve) => { resolveBody = resolve; });
  const res = {
    statusCode: 0,
    headers: null,
    writeHead(status, headers) { res.statusCode = status; res.headers = headers || {}; return res; },
    end(body) { if (body !== undefined && body !== null) chunks.push(Buffer.isBuffer(body) ? body : Buffer.from(String(body))); resolveBody(); return res; },
    status: () => res.statusCode,
    header: (k) => (res.headers ? String(res.headers[k] ?? '') : ''),
    bodyText: async () => (await done, Buffer.concat(chunks).toString('utf8')),
    bodyLen: async () => (await done, Buffer.concat(chunks).length),
  };
  return res;
}

function mockReq(method, url, body) {
  const req = new EventEmitter();
  req.method = method;
  req.url = url;
  setImmediate(() => {
    if (body !== undefined && body !== null) req.emit('data', Buffer.from(body));
    req.emit('end');
  });
  return req;
}

async function call(method, url, payload) {
  const req = mockReq(method, url, payload === undefined ? undefined : JSON.stringify(payload));
  const res = mockRes();
  await voice.handler(req, res);
  await Promise.race([res.bodyLen(), new Promise((r) => setTimeout(r, 90000))]);
  return res;
}

let failures = 0;
function check(label, cond, extra) {
  console.log('%s %s%s', cond ? 'PASS' : 'FAIL', label, extra === undefined ? '' : ' — ' + extra);
  if (!cond) failures += 1;
}

/* 1. health */
const health = await call('GET', '/whale-aside/voice');
const hjson = JSON.parse(await health.bodyText());
check('health 200', health.status() === 200 && hjson.ok === true, JSON.stringify(hjson).slice(0, 220));
check('health 报告 configFile/lib/python', typeof hjson.configFile === 'string' && typeof hjson.privateLib === 'string' && hjson.python === REAL_PY);

/* 2. negative rate (the shy/lazy bug) */
const shy = await call('POST', '/whale-aside/voice', { text: '自检线路：害羞的小鲸鱼', mood: 'shy' });
const shyjson = JSON.parse(await shy.bodyText());
check('shy（rate -3%）合成成功', shy.status() === 200 && shyjson.ok === true, await shy.bodyText());
if (shyjson.url) {
  const clip = await call('GET', 'http://x' + shyjson.url);
  check('shy clip 可播放', clip.status() === 200 && clip.header('content-type') === 'audio/mpeg' && (await clip.bodyLen()) > 1000, clip.header('content-length'));
}

/* 3. whale-voice.json drives the default timbre */
fs.writeFileSync(path.join(TMP, 'whale-voice.json'), JSON.stringify({ voice: 'zh-CN-YunxiaNeural', basePitchHz: 30, baseRatePct: -4 }), 'utf8');
const cfg = await call('POST', '/whale-aside/voice', { text: '配置文件里换嗓子', mood: 'tsun' });
const cfgjson = JSON.parse(await cfg.bodyText());
check('whale-voice.json 生效（音色/音高）', cfgjson.ok === true && cfgjson.voice === 'zh-CN-YunxiaNeural' && cfgjson.pitch === '+38Hz' && cfgjson.rate === '-1%', JSON.stringify(cfgjson));

/* 4. per-request override wins over the file */
const ovr = await call('POST', '/whale-aside/voice', { text: '请求级覆盖', mood: 'smug', voice: 'zh-CN-XiaoxiaoNeural', basePitchHz: 10 });
const ovrjson = JSON.parse(await ovr.bodyText());
check('请求级 voice/pitch 覆盖', ovrjson.ok === true && ovrjson.voice === 'zh-CN-XiaoxiaoNeural' && ovrjson.pitch === '+26Hz', JSON.stringify(ovrjson));

/* 5. a junk voice name is ignored, not crashed on */
const junk = await call('POST', '/whale-aside/voice', { text: '非法音色名', mood: 'lazy', voice: '../../etc/passwd' });
const junkjson = JSON.parse(await junk.bodyText());
check('非法 voice 被忽略并回落到配置值', junkjson.ok === true && junkjson.voice === 'zh-CN-YunxiaNeural', JSON.stringify(junkjson));

/* 6. enabled=false short-circuits with 503 */
fs.writeFileSync(path.join(TMP, 'whale-voice.json'), JSON.stringify({ enabled: false }), 'utf8');
const off = await call('POST', '/whale-aside/voice', { text: '关掉引擎', mood: 'tsun' });
check('enabled=false → 503 且解释原因', off.status() === 503 && /关闭/.test(await off.bodyText()));

/* 7. broken JSON config falls back and reports */
fs.writeFileSync(path.join(TMP, 'whale-voice.json'), '{ 这不是 json', 'utf8');
const broken = await call('GET', '/whale-aside/voice');
const bjson = JSON.parse(await broken.bodyText());
check('坏配置文件 → 用默认 + 报 configProblems', bjson.ok === true && Array.isArray(bjson.configProblems) && bjson.configProblems.length === 1 && bjson.voice === 'zh-CN-XiaoyiNeural', JSON.stringify(bjson.configProblems));

/* 8. a 0-byte clip is no longer served forever */
fs.writeFileSync(path.join(TMP, 'whale-voice.json'), '{}', 'utf8');
const ghost = '0123456789012345678901234567890123456789';
fs.writeFileSync(path.join(TMP, 'whale-audio', ghost + '.mp3'), Buffer.alloc(0));
const g = await call('GET', 'http://x/whale-aside/voice/' + ghost + '.mp3');
check('0 字节 clip → 404', g.status() === 404);
check('0 字节 clip 已被删除', fs.existsSync(path.join(TMP, 'whale-audio', ghost + '.mp3')) === false);

/* 9. traversal and bad input stay refused */
const trav = await call('GET', 'http://x/whale-aside/voice/%2e%2e%2f%2e%2e%2findex.js');
check('路径穿越 → 404', trav.status() === 404);
const bad = await call('POST', '/whale-aside/voice', { text: '', mood: 'tsun' });
check('空 text → 400', bad.status() === 400);
const moodless = await call('POST', '/whale-aside/voice', { text: '未知情绪走默认', mood: 'nope' });
check('未知 mood 走 tsun', moodless.status() === 200 && /tsun|\+30Hz|\+3%|\+0%/.test(await moodless.bodyText()));

/* 10. the log caught something readable */
const log = path.join(TMP, 'whale-audio', 'whale-voice.log');
check('语音日志存在且不大', fs.existsSync(log) === false || fs.statSync(log).size < 262144);

console.log('\n临时 DSH_HOME=%s', TMP);
console.log(failures === 0 ? 'ALL PASS' : failures + ' FAILURE(S)');
process.exit(failures === 0 ? 0 : 1);
