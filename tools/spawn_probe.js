/* Reproduce the plugin's edge-tts spawn exactly, but capture stderr to a file.
   Run: node tools/spawn_probe.js  */
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const PY = 'C:\\Users\\Administrator\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe';
const CACHE = path.join(os.homedir(), '.dsh', 'whale-audio');
const SAMPLES = 'D:\\code\\DSH_PlainRiceWhale\\samples';
const LOGDIR = 'D:\\code\\DSH_PlainRiceWhale\\.work\\spawn_probe';
fs.mkdirSync(LOGDIR, { recursive: true });

const TEXT_SHY = '呜…主人想换我的嗓子？先让我照照镜子看看现在用的是哪副声带';
const TEXT_TEST = '测试线路一：鲸鱼娘的喉咙检查';

const CASES = [
  { id: 'A_p22_r0_to_cache', pitch: '+22Hz', rate: '+0%', text: TEXT_TEST, out: path.join(CACHE, 'probe_a.mp3') },
  { id: 'B_p30_r3_to_samples', pitch: '+30Hz', rate: '+3%', text: TEXT_TEST, out: path.join(SAMPLES, 'probe_b.mp3') },
  { id: 'C_p35_rminus3', pitch: '+35Hz', rate: '-3%', text: TEXT_TEST, out: path.join(SAMPLES, 'probe_c.mp3') },
  { id: 'D_exact_shy_route', pitch: '+35Hz', rate: '-3%', text: TEXT_SHY, out: path.join(CACHE, 'probe_d.mp3') },
  { id: 'E_stdio_ignore', pitch: '+30Hz', rate: '+3%', text: TEXT_TEST, out: path.join(SAMPLES, 'probe_e.mp3'), ignore: true },
];

for (const c of CASES) {
  const args = ['-m', 'edge_tts', '--voice', 'zh-CN-XiaoyiNeural', '--pitch', c.pitch,
                '--rate', c.rate, '--text', c.text, '--write-media', c.out];
  const errFile = path.join(LOGDIR, c.id + '.err.log');
  const outFile = path.join(LOGDIR, c.id + '.out.log');
  if (fs.existsSync(c.out)) fs.unlinkSync(c.out);
  let stdio;
  const fdErr = fs.openSync(errFile, 'w');
  const fdOut = fs.openSync(outFile, 'w');
  if (c.ignore) {
    stdio = ['ignore', 'ignore', fdErr];
  } else {
    stdio = ['ignore', fdOut, fdErr];
  }
  const t0 = Date.now();
  const r = spawnSync(PY, args, { stdio, windowsHide: true });
  fs.closeSync(fdErr);
  fs.closeSync(fdOut);
  const dt = Date.now() - t0;
  const errText = fs.readFileSync(errFile, 'utf8').replace(/\s+/g, ' ').trim();
  const ok = r.status === 0 && fs.existsSync(c.out) && fs.statSync(c.out).size > 0;
  console.log('%s%s %-18s exit=%s %5dms  media=%s',
    ok ? 'OK  ' : 'BAD ', '', c.id, r.status, dt,
    fs.existsSync(c.out) ? fs.statSync(c.out).size + 'B' : 'none');
  if (r.error) console.log('    spawn error:', r.error.message);
  if (errText) console.log('    stderr:', errText.slice(0, 700));
}
