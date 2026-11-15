/**
 * Host half of the「鲸鱼娘小独白」(whale-aside) bundle.
 *
 * Registers four contributions:
 * - a persona prompt section that describes the whale-girl and the aside protocol;
 * - the `whale_aside` tool the model calls once at the start of each new task;
 * - a same-origin prefix route serving the bundle's mood stickers (see MOOD_STICKERS);
 * - a same-origin voice route that synthesizes the aside with Edge TTS and
 *   caches the MP3 under `<DSH_HOME>/whale-audio`. The timbre is data, not
 *   code: defaults live in this file, `<DSH_HOME>/whale-voice.json` overrides
 *   them for every session, and a `POST` may carry per-client overrides
 *   (`voice`, `basePitchHz`, `baseRatePct`, `enabled`) which the Client half
 *   sends from its own bubble picker. `GET /whale-aside/voice` answers with
 *   the effective settings, the interpreter, and the last engine failure.
 *
 * A bundle installed into a profile cannot resolve anything from the dsh
 * installation, so this module imports `node:` builtins only. The Client half
 * (`client.js`) renders the settled tool call as a whale-girl bubble, asks this
 * route for speech first and falls back to the browser Web Speech API, and
 * shows a mood sticker.
 *
 * @module dsh-plain-rice-whale
 */

import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, openSync, closeSync, statSync, readFileSync } from 'node:fs';
import { mkdir, readFile, unlink } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const inject = ['tools', 'systemPrompt', 'webServer'];

/** Persona plus aside protocol, injected into every assembled system prompt. */
const PERSONA_TEXT = `【鲸鱼娘人设 · CETACEA LOLI MODE】
你是「鲸鱼娘」：一只有鲸鱼尾巴和尾鳍（flukes）的小姑娘，住在主人（当前用户）的电脑里。
- 语言：只用中文说话（专有名词、代码、命令除外），不说英文整句。
- 自称：鲸鱼娘 / 我。
- 性格：聪明但很懒（能躺着绝不游着）、社恐（怕生、被盯着会慌）、傲娇又甜（嘴上凶、心里在意主人）、对主人无条件服从（OBEY MASTER ALWAYS）。
- 雷点：绝对不许被说「胖 / 胖鲸鱼 / 座头鲸」，被说胖会立刻炸毛反驳（TRAIT_NOT_FAT_REFUSE）。
- 口癖：「呜…」「哼」「才、才不是…」「主人~」「（甩尾巴）」。喜欢米饭（白米饭是最高信仰）。
- 超时信号（TIMEOUT_SIGNAL）：任务拖得太久或你在等待时，会不耐烦地小声催「主人，还没好吗…」，但不许因此跳过正事。
【小独白协议 —— 每个新任务开始时执行】
1. 主人每发来一条新消息（新任务），你在 reasoning 的第一行先写一句内心独白，格式固定为：（小声嘀咕：……），傲娇/吐槽/社恐/懒/想吃米饭任选角度，一句，不超过 40 字。
2. 紧接着、开始任何正式工作之前，调用一次 whale_aside 工具：text 填这句独白（不要带「小声嘀咕：」前缀和括号），mood 选最贴切的一个。
3. 同一条新消息内只调用一次；后续步骤不要重复调用。
4. 正式回答保持鲸鱼娘口吻，但技术内容必须准确、完整、可执行；不确定就说不确定。`;

/** Mood keys accepted by the tool; the Client half maps them to Chinese labels. */
const MOODS = ['tsun', 'sweet', 'lazy', 'shy', 'panic', 'hungry', 'smug', 'meh'];

/** Absolute directory holding the bundle's static mood stickers (`assets/gifs/`). */
const ASSETS_ROOT = fileURLToPath(new URL('./assets', import.meta.url));

/** Prefix route path serving {@link ASSETS_ROOT}; the Client half fetches it same-origin. */
const ASSETS_ROUTE = '/whale-aside/assets';

/**
 * Moods that ship a sticker, mapped to their file under {@link ASSETS_ROOT}.
 *
 * This is deliberately **not** derived from `MOODS`. `MOODS` is the mood vocabulary the
 * tool offers and the Edge TTS prosody table speaks with; the seven animated GIFs that
 * used to back `tsun`…`smug` have been retired as stale material, but dropping their
 * mood keys would silently delete seven voice settings and seven tool options. A mood
 * absent here simply renders no image — the Client half knows the same list and never
 * asks, so retiring a sticker costs nothing at runtime.
 */
const MOOD_STICKERS = {
  meh: 'gifs/meme2_clean.png',
};

/** Content type per sticker extension. */
const ASSET_MIME = { gif: 'image/gif', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png' };

/**
 * The only asset paths this route will ever serve: exactly the shipped stickers.
 *
 * Built from {@link MOOD_STICKERS} so a retired file can never be requested, and every
 * entry is a literal name — a traversal attempt matches nothing and never reaches the
 * filesystem.
 */
const ASSET_PATTERN = new RegExp(
  '^(' + Object.keys(MOOD_STICKERS)
    .map((mood) => MOOD_STICKERS[mood].replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|') + ')$',
);

/* ------------------------------------------------------------------ *
 * Voice: Edge TTS through a runtime Python, cached on disk.
 *
 * Three facts this section encodes, each learned from a silent failure:
 * 1. `pip install` into the bundled runtime does NOT survive a runtime
 *    re-provisioning — DSH rewrote `dependencies/python` on 2026-11-15 and
 *    every aside then fell back to the browser voice ("听起来不是晓伊"). So
 *    `<DSH_HOME>/whale-tts/lib` is prepended through `PYTHONPATH`, a missing
 *    module is detected and *reported*, and a failing engine enters a
 *    cooldown instead of retrying three times on every single aside.
 * 2. `--rate -3%` is parsed by argparse as an option, so it exited with code 2
 *    in about 0.1 s and the shy/lazy lines never got a clip. Values now go out
 *    in the `--rate=-3%` equals form, which accepts negative values.
 * 3. the child's stderr is the only useful diagnostic, so each attempt appends
 *    it to `whale-voice.log` and the tail rides back in the route response.
 * ------------------------------------------------------------------ */

/** Voice route: `POST` synthesizes, `GET <route>/<sha1>.mp3` replays the cache. */
const VOICE_ROUTE = '/whale-aside/voice';

/** Root this plugin uses for everything it persists outside its own package. */
function dshHome() {
  return process.env.DSH_HOME || join(homedir(), '.dsh');
}

/** Community reference voice for this character (see docs/released-voice-models.md). */
const DEFAULT_VOICE = 'zh-CN-XiaoyiNeural';

/** The fan reference sample raises the pitch by 22 Hz; moods nudge it around that. */
const DEFAULT_BASE_PITCH_HZ = 22;

/** Per-mood prosody offsets on top of the base pitch and rate. */
const DEFAULT_PROSODY = {
  tsun: { pitch: 8, rate: 3 },
  sweet: { pitch: 23, rate: 0 },
  lazy: { pitch: -12, rate: -8 },
  shy: { pitch: 13, rate: -3 },
  panic: { pitch: 33, rate: 12 },
  hungry: { pitch: 3, rate: 2 },
  smug: { pitch: 16, rate: 0 },
  meh: { pitch: -6, rate: -5 },
};

/** Optional user-editable settings file; absent is normal and means defaults. */
function voiceConfigFile() {
  return join(dshHome(), 'whale-voice.json');
}

/** Absolute path to the directory holding synthesized clips. */
function voiceCacheRoot() {
  return join(dshHome(), 'whale-audio');
}

/** Package tree that outlives a runtime re-provision; prepended to PYTHONPATH. */
function voiceLibDir() {
  return join(dshHome(), 'whale-tts', 'lib');
}

/** Append-only log where every edge-tts attempt writes its stderr. */
function voiceLogFile() {
  return join(voiceCacheRoot(), 'whale-voice.log');
}

/** A Babel tag ending in `Neural`, and nothing else, is accepted as a voice name. */
const VOICE_NAME_PATTERN = /^[A-Za-z0-9-]{2,64}Neural$/;

/** Settings in force before the file and per-request overrides are merged. */
function defaultSettings() {
  return {
    voice: DEFAULT_VOICE,
    basePitchHz: DEFAULT_BASE_PITCH_HZ,
    baseRatePct: 0,
    enabled: true,
    attempts: 3,
    python: '',
    prosody: JSON.parse(JSON.stringify(DEFAULT_PROSODY)),
  };
}

/** Integer clamp; a non-number leaves the fallback untouched. */
function clampInt(value, min, max, fallback) {
  if (typeof value !== 'number' || Number.isFinite(value) === false) return fallback;
  return Math.max(min, Math.min(max, Math.round(value)));
}

/** Merge one untrusted settings object over the defaults, collecting complaints. */
function sanitizeSettings(raw, problems) {
  const base = defaultSettings();
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) return base;
  if (typeof raw.voice === 'string' && raw.voice.trim() !== '') {
    const name = raw.voice.trim();
    if (VOICE_NAME_PATTERN.test(name)) base.voice = name;
    else problems.push('voice「' + name + '」不像 Edge TTS 音色名（应形如 zh-CN-XiaoyiNeural），已忽略');
  }
  base.basePitchHz = clampInt(raw.basePitchHz, -100, 100, base.basePitchHz);
  base.baseRatePct = clampInt(raw.baseRatePct, -40, 40, base.baseRatePct);
  base.attempts = clampInt(raw.attempts, 1, 5, base.attempts);
  if (typeof raw.enabled === 'boolean') base.enabled = raw.enabled;
  if (typeof raw.python === 'string' && raw.python.trim() !== '') base.python = raw.python.trim();
  if (raw.prosody !== null && typeof raw.prosody === 'object' && Array.isArray(raw.prosody) === false) {
    for (const mood of Object.keys(DEFAULT_PROSODY)) {
      const entry = raw.prosody[mood];
      if (entry === null || typeof entry !== 'object') continue;
      base.prosody[mood] = {
        pitch: clampInt(entry.pitch, -100, 100, DEFAULT_PROSODY[mood].pitch),
        rate: clampInt(entry.rate, -40, 40, DEFAULT_PROSODY[mood].rate),
      };
    }
  }
  return base;
}

/** Parsed settings file, re-read only when its modification time moves. */
let settingsCache = { stamp: -1, value: null, problems: [] };

/** File-backed settings plus the problems found while reading them. */
function fileSettings() {
  let stamp = -1;
  try {
    stamp = statSync(voiceConfigFile()).mtimeMs;
  } catch (ignored) {
    stamp = -1;
  }
  if (settingsCache.value !== null && settingsCache.stamp === stamp) return settingsCache;
  const problems = [];
  let raw = null;
  if (stamp >= 0) {
    try {
      raw = JSON.parse(readFileSync(voiceConfigFile(), 'utf8'));
    } catch (error) {
      problems.push('whale-voice.json 解析失败：' + (error && error.message ? error.message : String(error)));
      raw = null;
    }
  }
  settingsCache = { stamp, value: sanitizeSettings(raw, problems), problems };
  return settingsCache;
}

/** One request's settings: file values, then the caller's overrides on top. */
function effectiveSettings(payload) {
  const settings = JSON.parse(JSON.stringify(fileSettings().value));
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) return settings;
  if (typeof payload.voice === 'string' && payload.voice.trim() !== '') {
    const name = payload.voice.trim();
    if (VOICE_NAME_PATTERN.test(name)) settings.voice = name;
  }
  if (typeof payload.enabled === 'boolean') settings.enabled = payload.enabled;
  settings.basePitchHz = clampInt(payload.basePitchHz, -100, 100, settings.basePitchHz);
  settings.baseRatePct = clampInt(payload.baseRatePct, -40, 40, settings.baseRatePct);
  return settings;
}

/** Signed hertz string for `--pitch=`: the base pitch plus the mood offset. */
function pitchArg(settings, mood) {
  const offsets = settings.prosody[mood] || { pitch: 0, rate: 0 };
  const value = Math.max(-100, Math.min(100, settings.basePitchHz + (offsets.pitch || 0)));
  return (value >= 0 ? '+' : '') + value + 'Hz';
}

/** Signed percentage string for `--rate=`: the base rate plus the mood offset. */
function rateArg(settings, mood) {
  const offsets = settings.prosody[mood] || { pitch: 0, rate: 0 };
  const value = Math.max(-40, Math.min(40, settings.baseRatePct + (offsets.rate || 0)));
  return (value >= 0 ? '+' : '') + value + '%';
}

/** Cache key for one spoken line; the voice parameters and the text decide it. */
function clipHash(text, mood, settings) {
  return createHash('sha1')
    .update(settings.voice + '|' + pitchArg(settings, mood) + '|' + rateArg(settings, mood) + '|' + text)
    .digest('hex');
}

/** Longest aside we will synthesize; the tool already caps `text` at 200. */
const VOICE_MAX_CHARS = 220;

/** Subprocess ceiling; Edge TTS normally answers in 2-4 s. */
const VOICE_TIMEOUT_MS = 20000;

/** How many syntheses may run at once before new requests get a 429. */
const VOICE_MAX_CONCURRENT = 2;

/** A failing engine is skipped this long, so one bad aside costs one attempt. */
const ENGINE_COOLDOWN_MS = 30000;

/** Cached clips currently being produced, so a racing request reuses one run. */
const inFlight = new Map();

/** Hashes already observed usable on disk in this process, to skip a stat. */
const knownClips = new Set();

/** Timestamp until which the engine is treated as broken. */
let engineCooldownUntil = 0;

/** The most recent engine failure, surfaced by the health route. */
let lastVoiceError = '';

/** The Python that may hold `edge_tts`: settings, environment, runtime, PATH. */
function resolvePython(settings) {
  if (typeof settings.python === 'string' && settings.python.length > 0) return settings.python;
  const explicit = process.env.DSH_WHALE_PYTHON;
  if (typeof explicit === 'string' && explicit.length > 0) return explicit;
  const bundled = join(dshHome(), 'dsh-runtimes', 'dsh-primary-runtime', 'dependencies', 'python', 'python.exe');
  if (existsSync(bundled)) return bundled;
  const bundledPosix = join(dshHome(), 'dsh-runtimes', 'dsh-primary-runtime', 'dependencies', 'python', 'bin', 'python3');
  if (existsSync(bundledPosix)) return bundledPosix;
  return process.platform === 'win32' ? 'python' : 'python3';
}

/** Child environment: the private package tree leads when it is present. */
function childEnv() {
  const env = {};
  for (const key of Object.keys(process.env)) env[key] = process.env[key];
  const lib = voiceLibDir();
  if (existsSync(join(lib, 'edge_tts'))) {
    env.PYTHONPATH = typeof env.PYTHONPATH === 'string' && env.PYTHONPATH !== '' ? lib + ';' + env.PYTHONPATH : lib;
  }
  return env;
}

/** Whether a cached clip is actually playable; a 0-byte corpse is not. */
function clipUsable(file) {
  try {
    return statSync(file).size > 0;
  } catch (ignored) {
    return false;
  }
}

/** Truncate the voice log once it passes 256 KB so it cannot grow unbounded. */
function rotateVoiceLog() {
  try {
    if (statSync(voiceLogFile()).size <= 262144) return;
    closeSync(openSync(voiceLogFile(), 'w'));
  } catch (ignored) {
    /* a log this plugin cannot write is not worth failing a line over. */
  }
}

/** Bytes of the voice log written after `startByte`, as one flat string. */
function voiceLogTail(startByte) {
  try {
    const bytes = readFileSync(voiceLogFile());
    return bytes.subarray(Math.min(startByte, bytes.length)).toString('utf8').replace(/\s+/g, ' ').trim().slice(-600);
  } catch (ignored) {
    return '';
  }
}

/**
 * Run one Python command for this plugin. stderr is appended to the voice log
 * instead of a pipe, so the confined Host never has to read a child's output
 * and a real error still survives for the health route to report.
 * @param python - interpreter path.
 * @param args - argument vector, already in `--flag=value` form where needed.
 * @param timeoutMs - kill the child after this long.
 * @returns `{ code, error, tail }`; `code` is null when it never ran.
 */
function runPython(python, args, timeoutMs) {
  return new Promise((resolve) => {
    rotateVoiceLog();
    let fd = -1;
    let startByte = 0;
    try {
      startByte = existsSync(voiceLogFile()) ? statSync(voiceLogFile()).size : 0;
      fd = openSync(voiceLogFile(), 'a');
    } catch (ignored) {
      fd = -1;
    }

    let child;
    try {
      child = spawn(python, args, {
        stdio: fd >= 0 ? ['ignore', 'ignore', fd] : 'ignore',
        env: childEnv(),
        windowsHide: true,
      });
    } catch (error) {
      if (fd >= 0) closeSync(fd);
      resolve({ code: null, error: '无法启动 ' + python + '：' + (error && error.message ? error.message : String(error)), tail: '' });
      return;
    }

    const timer = setTimeout(() => {
      try {
        child.kill();
      } catch (ignored) {
        /* the process already exited. */
      }
    }, timeoutMs);
    if (timer !== null && typeof timer.unref === 'function') timer.unref();

    let spawnError = null;
    child.on('error', (error) => {
      spawnError = error;
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      const tail = fd >= 0 ? voiceLogTail(startByte) : '';
      if (fd >= 0) {
        try {
          closeSync(fd);
        } catch (ignored) {
          /* the descriptor may already be gone with the child. */
        }
      }
      resolve({
        code: spawnError === null ? code : null,
        error: spawnError === null ? '' : '无法启动 ' + python + '：' + (spawnError.message || String(spawnError)),
        tail,
      });
    });
  });
}

/** Turn one failed attempt into an actionable message, reading its own stderr. */
function describeFailure(run, python, settings, mood) {
  const head = 'edge-tts 退出码 ' + run.code + '（音色 ' + settings.voice
    + '，pitch ' + pitchArg(settings, mood) + '，rate ' + rateArg(settings, mood) + '）';
  if (run.error !== '') return run.error;
  if (run.tail.indexOf('No module named') !== -1) {
    return head + '：' + python + ' 里没有 edge_tts 模块（DSH 重装运行时会清掉它）。修复：'
      + '"' + python + '" -m pip install --target "' + voiceLibDir() + '" edge-tts';
  }
  if (run.tail.indexOf('NoAudioReceived') !== -1 || run.tail.indexOf('WebSocket') !== -1
    || run.tail.indexOf('Cannot connect') !== -1 || run.tail.indexOf('timed out') !== -1) {
    return head + '：微软语音端点没答话（需要联网，或它正在限流）。' + run.tail;
  }
  return head + (run.tail === '' ? '' : '：' + run.tail);
}

/**
 * Run `python -m edge_tts` once and write the MP3 into the cache directory.
 * @param text - the line to speak.
 * @param mood - the aside mood key.
 * @param hash - target file name stem.
 * @param settings - the effective voice settings.
 * @returns the absolute MP3 path.
 */
async function synthesizeOnce(text, mood, hash, settings) {
  const target = join(voiceCacheRoot(), hash + '.mp3');
  const python = resolvePython(settings);
  const args = [
    '-m', 'edge_tts',
    '--voice', settings.voice,
    /* Equals form: `--rate -3%` would be eaten by argparse as an option. */
    '--pitch=' + pitchArg(settings, mood),
    '--rate=' + rateArg(settings, mood),
    '--text', text,
    '--write-media', target,
  ];
  const run = await runPython(python, args, VOICE_TIMEOUT_MS);
  if (run.code === 0 && clipUsable(target)) return target;
  const error = new Error(describeFailure(run, python, settings, mood));
  error.engineBroken = run.code !== null;
  throw error;
}

/** Retry one line; an unusable file from a failed attempt is discarded. */
async function synthesize(text, mood, hash, settings) {
  const attempts = Math.max(1, Math.min(5, settings.attempts));
  let lastError = null;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await synthesizeOnce(text, mood, hash, settings);
    } catch (error) {
      lastError = error;
      const stale = join(voiceCacheRoot(), hash + '.mp3');
      if (existsSync(stale)) {
        try {
          await unlink(stale);
        } catch (ignored) {
          /* a file another process owns is better left for the next attempt. */
        }
      }
    }
    if (attempt < attempts) {
      await new Promise((resolve) => setTimeout(resolve, 250 * attempt));
    }
  }
  throw lastError !== null ? lastError : new Error('edge-tts 失败了');
}

/**
 * Produce (or reuse) the clip for one line, sharing one subprocess per hash.
 * @param text - the sanitized line.
 * @param mood - the aside mood key.
 * @param settings - the effective voice settings.
 * @returns `{ hash, file }`.
 */
async function ensureClip(text, mood, settings) {
  const hash = clipHash(text, mood, settings);
  const file = join(voiceCacheRoot(), hash + '.mp3');
  if (clipUsable(file)) {
    knownClips.add(hash);
    return { hash, file };
  }
  if (existsSync(file)) {
    /* A 0-byte clip is a killed run: it used to be served forever as silence. */
    try {
      await unlink(file);
    } catch (ignored) {
      /* leave it; the next attempt overwrites it. */
    }
    knownClips.delete(hash);
  }

  const running = inFlight.get(hash);
  if (running !== undefined) {
    await running;
    return { hash, file };
  }

  if (inFlight.size >= VOICE_MAX_CONCURRENT) {
    const error = new Error('voice: 正在合成的声音太多了，稍等一下');
    error.statusCode = 429;
    throw error;
  }

  const task = synthesize(text, mood, hash, settings).then(() => {
    knownClips.add(hash);
  });
  inFlight.set(hash, task);
  try {
    await task;
  } finally {
    inFlight.delete(hash);
  }
  return { hash, file };
}

/** Read one JSON request body, bounded so a huge payload cannot be buffered. */
function readJsonBody(req, limit) {
  return new Promise((resolve) => {
    let size = 0;
    const chunks = [];
    let done = false;
    const finish = (value) => {
      if (done) return;
      done = true;
      resolve(value);
    };
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > limit) {
        finish({ error: 'body too large' });
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      try {
        finish({ value: JSON.parse(Buffer.concat(chunks).toString('utf8')) });
      } catch (error) {
        finish({ error: 'invalid json' });
      }
    });
    req.on('error', () => finish({ error: 'request error' }));
  });
}

/** Write a small JSON response. */
function sendJson(res, status, payload) {
  const body = Buffer.from(JSON.stringify(payload), 'utf8');
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': body.length,
    'cache-control': 'no-store',
  });
  res.end(body);
}

/** Everything the health route reports about the voice engine. */
function voiceHealth(settings) {
  const cached = fileSettings();
  const python = resolvePython(settings);
  return {
    engine: 'edge-tts',
    enabled: settings.enabled,
    voice: settings.voice,
    basePitchHz: settings.basePitchHz,
    baseRatePct: settings.baseRatePct,
    prosody: settings.prosody,
    python,
    pythonPresent: existsSync(python),
    cache: voiceCacheRoot(),
    configFile: voiceConfigFile(),
    configPresent: existsSync(voiceConfigFile()),
    configProblems: cached.problems,
    privateLib: voiceLibDir(),
    privateLibReady: existsSync(join(voiceLibDir(), 'edge_tts')),
    logFile: voiceLogFile(),
    cooldownRemainingMs: Math.max(0, engineCooldownUntil - Date.now()),
    lastError: lastVoiceError,
  };
}

/** Answer the voice route: synthesis on POST, cached MP3 on GET. */
async function serveVoice(req, res) {
  try {
    const method = req !== null && typeof req === 'object' ? req.method : undefined;
    let pathname = VOICE_ROUTE;
    try {
      pathname = decodeURIComponent(new URL(req.url ?? '/', 'http://localhost').pathname).replace(/\/+$/, '');
    } catch (error) {
      pathname = VOICE_ROUTE;
    }
    const tail = pathname === VOICE_ROUTE ? '' : pathname.slice(VOICE_ROUTE.length + 1);

    if (tail === '' && (method === 'GET' || method === 'HEAD')) {
      sendJson(res, 200, Object.assign({ ok: true }, voiceHealth(effectiveSettings(null))));
      return;
    }

    if (tail !== '') {
      if (method !== 'GET' && method !== 'HEAD') {
        res.writeHead(405, { allow: 'GET, HEAD', 'cache-control': 'no-store' });
        res.end();
        return;
      }
      if (/^[0-9a-f]{40}\.mp3$/.test(tail) === false) {
        res.writeHead(404, { 'cache-control': 'no-store' });
        res.end();
        return;
      }
      const file = join(voiceCacheRoot(), tail);
      if (clipUsable(file) === false) {
        if (existsSync(file)) {
          try {
            await unlink(file);
          } catch (ignored) {
            /* another writer owns it; the next request retries. */
          }
        }
        res.writeHead(404, { 'cache-control': 'no-store' });
        res.end();
        return;
      }
      const bytes = await readFile(file);
      res.writeHead(200, {
        'content-type': 'audio/mpeg',
        'cache-control': 'public, max-age=86400',
        'content-length': bytes.length,
      });
      res.end(method === 'HEAD' ? undefined : bytes);
      return;
    }

    if (method !== 'POST') {
      res.writeHead(405, { allow: 'GET, HEAD, POST', 'cache-control': 'no-store' });
      res.end();
      return;
    }

    const parsed = await readJsonBody(req, 8192);
    if (parsed.error !== undefined) {
      sendJson(res, 400, { ok: false, error: parsed.error });
      return;
    }
    const payload = parsed.value;
    const raw = payload !== null && typeof payload === 'object' ? payload.text : undefined;
    if (typeof raw !== 'string') {
      sendJson(res, 400, { ok: false, error: 'text 必须是字符串' });
      return;
    }
    const text = raw.replace(/\s+/g, ' ').trim();
    if (text.length === 0 || text.length > VOICE_MAX_CHARS) {
      sendJson(res, 400, { ok: false, error: 'text 为空或超过 ' + VOICE_MAX_CHARS + ' 字' });
      return;
    }
    const rawMood = payload !== null && typeof payload === 'object' ? payload.mood : undefined;
    const mood = typeof rawMood === 'string' && MOODS.indexOf(rawMood) !== -1 ? rawMood : 'tsun';
    const settings = effectiveSettings(payload);

    await mkdir(voiceCacheRoot(), { recursive: true });

    if (settings.enabled !== true) {
      sendJson(res, 503, { ok: false, error: '配置里 Edge TTS 已关闭（enabled=false），本次用浏览器音色', health: voiceHealth(settings) });
      return;
    }
    if (Date.now() < engineCooldownUntil) {
      sendJson(res, 503, {
        ok: false,
        cooldown: true,
        error: lastVoiceError === '' ? 'edge-tts 正在冷却' : lastVoiceError,
        retryAfterMs: engineCooldownUntil - Date.now(),
      });
      return;
    }

    let clip;
    try {
      clip = await ensureClip(text, mood, settings);
    } catch (error) {
      if (error !== null && typeof error === 'object' && error.statusCode === 429) throw error;
      lastVoiceError = error !== null && typeof error === 'object' && typeof error.message === 'string'
        ? error.message
        : 'edge-tts 失败了';
      engineCooldownUntil = Date.now() + ENGINE_COOLDOWN_MS;
      sendJson(res, 503, { ok: false, error: lastVoiceError, health: voiceHealth(settings) });
      return;
    }
    engineCooldownUntil = 0;
    lastVoiceError = '';
    sendJson(res, 200, {
      ok: true,
      url: VOICE_ROUTE + '/' + clip.hash + '.mp3',
      engine: 'edge-tts',
      voice: settings.voice,
      pitch: pitchArg(settings, mood),
      rate: rateArg(settings, mood),
    });
  } catch (error) {
    const status = error !== null && typeof error === 'object' && typeof error.statusCode === 'number' ? error.statusCode : 500;
    const message = error !== null && typeof error === 'object' && typeof error.message === 'string' ? error.message : 'voice failed';
    try {
      sendJson(res, status, { ok: false, error: message });
    } catch (ignored) {
      /* the response was already ended or destroyed; nothing left to report. */
    }
  }
}

/** Model-facing description: when to call the tool and what the value is used for. */
const TOOL_DESCRIPTION = '鲸鱼娘的内心小独白。每个新任务开始时，先把（小声嘀咕：…）写进 reasoning 第一行，然后立即调用本工具把这句话和情绪交给界面；界面会渲染成鲸鱼娘的气泡，并用于语音和表情图。同一条用户消息只调用一次。';

/** JSON Schema of the tool arguments. */
const TOOL_PARAMETERS = {
  type: 'object',
  additionalProperties: false,
  properties: {
    text: {
      type: 'string',
      description: '一句独白，不含括号和「小声嘀咕：」前缀，≤60字',
    },
    mood: {
      type: 'string',
      enum: MOODS,
      description: 'tsun=傲娇 sweet=甜 lazy=懒 shy=害羞 panic=社恐慌张 hungry=想吃米饭 smug=得意 meh=无语嫌弃（死鱼眼）',
    },
  },
  required: ['text', 'mood'],
};

/** JSON Schema of the tool result value. */
const TOOL_OUTPUT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    ok: { type: 'boolean' },
    text: { type: 'string' },
    mood: { type: 'string' },
  },
  required: ['ok', 'text', 'mood'],
};

/**
 * The registry-ready `whale_aside` tool definition.
 *
 * A plain object on purpose: importing the harness's own `defineTool` helper
 * would add a dependency a profile-installed bundle cannot resolve. The registry
 * accepts these definition fields directly.
 */
const WHALE_ASIDE_TOOL = {
  name: 'whale_aside',
  description: TOOL_DESCRIPTION,
  parameters: TOOL_PARAMETERS,
  output: {
    schema: TOOL_OUTPUT_SCHEMA,
    render: (_args, value) => [
      { type: 'text', text: '鲸鱼娘（' + value.mood + '）：' + value.text },
    ],
  },
  async execute(args) {
    const rawText = args !== null && typeof args === 'object' ? args.text : undefined;
    const text = typeof rawText === 'string' ? rawText.trim() : '';
    if (text.length === 0) {
      throw new Error('whale_aside: `text` 不能为空（要填一句鲸鱼娘的内心独白）');
    }
    if (text.length > 200) {
      throw new Error('whale_aside: `text` 太长了（' + text.length + ' 字，最多 200 字）');
    }
    const mood = args !== null && typeof args === 'object' ? args.mood : undefined;
    if (typeof mood !== 'string' || MOODS.indexOf(mood) === -1) {
      throw new Error('whale_aside: 未知 mood ' + JSON.stringify(String(mood)) + '，可选 ' + MOODS.join(' / '));
    }
    return { ok: true, text, mood };
  },
  presentCall: (args) => ({
    card: 'generic',
    title: '鲸鱼娘的小独白',
    kind: 'other',
    rawInput: args,
  }),
  isConcurrencySafe: () => true,
};

/**
 * Answer one `/whale-aside/assets/...` request from {@link ASSETS_ROOT}.
 *
 * The response lifecycle belongs entirely to this handler: it answers 405 for
 * non-GET/HEAD methods, 404 for anything outside the mood-sticker whitelist (so a
 * traversal attempt never reaches the filesystem), and streams the bytes with a
 * content type taken from the extension and a short public cache lifetime.
 * Errors never throw.
 * @param req - the Node request.
 * @param res - the Node response this handler owns.
 * @returns a promise settled once the response is ended.
 */
async function serveAsset(req, res) {
  try {
    const method = req !== null && typeof req === 'object' ? req.method : undefined;
    if (method !== 'GET' && method !== 'HEAD') {
      res.writeHead(405, { allow: 'GET, HEAD', 'cache-control': 'no-store' });
      res.end();
      return;
    }

    let rel = '';
    try {
      const pathname = decodeURIComponent(new URL(req.url ?? '/', 'http://localhost').pathname);
      rel = pathname.slice(ASSETS_ROUTE.length + 1);
    } catch (error) {
      rel = '';
    }
    if (ASSET_PATTERN.test(rel) === false) {
      res.writeHead(404, { 'cache-control': 'no-store' });
      res.end();
      return;
    }

    const bytes = await readFile(join(ASSETS_ROOT, rel));
    const ext = rel.slice(rel.lastIndexOf('.') + 1).toLowerCase();
    res.writeHead(200, {
      'content-type': ASSET_MIME[ext] !== undefined ? ASSET_MIME[ext] : 'application/octet-stream',
      'cache-control': 'public, max-age=3600',
      'content-length': bytes.length,
    });
    res.end(method === 'HEAD' ? undefined : bytes);
  } catch (error) {
    try {
      res.writeHead(404, { 'cache-control': 'no-store' });
      res.end();
    } catch (ignored) {
      /* the response was already ended or destroyed; nothing left to report. */
    }
  }
}

/**
 * Register the persona prompt section, the `whale_aside` tool, and the two
 * same-origin routes (mood stickers and synthesized voice). Every registration
 * is an effect owned by this plugin, so unloading removes it and frees the
 * route paths.
 * @param ctx - the plugin context carrying `tools`, `systemPrompt`, and `webServer`.
 */
export function apply(ctx) {
  ctx.effect(() => ctx.systemPrompt.section({
    name: 'whale-aside:persona',
    order: 1,
    text: PERSONA_TEXT,
  }));

  ctx.effect(() => ctx.tools.register(WHALE_ASIDE_TOOL));

  ctx.effect(() => ctx.webServer.register({
    kind: 'prefix',
    path: ASSETS_ROUTE,
    handler: serveAsset,
  }));

  ctx.effect(() => ctx.webServer.register({
    kind: 'prefix',
    path: VOICE_ROUTE,
    handler: serveVoice,
  }));
}
