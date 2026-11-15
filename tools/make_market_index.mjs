#!/usr/bin/env node
/**
 * Generate and validate the plugin market index (format 1) for this repository.
 *
 * Why a generator instead of a hand-written JSON: format 1 has rules that are easy to
 * violate quietly — every version needs an integer `publishTimestamp`, `title` must
 * contain `en`, `category`/`labels` must reference ids declared in index metadata, the
 * git source needs a lowercase 40-hex commit, and an `engines.dsh` range written as
 * `>=0.2.2` does **not** match a running `0.2.2-rc.3` under SemVer prerelease rules.
 * The official validator (`@deepseek-ai/dsh-plugin-market-index`) is the same rule set
 * the Host reads with, so this script fails instead of publishing a broken index.
 *
 * Usage:
 *   node tools/make_market_index.mjs <40-hex-commit> [--url <index URL>] [--out <dir>]
 *
 * The validator is not vendored; install it once where this script can resolve it:
 *   npm install --prefix .work/validator @deepseek-ai/dsh-plugin-market-index
 */
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const BASE = join(dirname(fileURLToPath(import.meta.url)), '..');

const argv = process.argv.slice(2);
const flag = (name, fallback) => {
  const at = argv.indexOf(name);
  return at !== -1 && argv[at + 1] !== undefined ? argv[at + 1] : fallback;
};
const commit = argv.find((a) => !a.startsWith('--'));
const OUT_DIR = flag('--out', join(BASE, 'market'));
const REPO = 'ZJDqtjs/DSH_PlainRiceWhale';
const INDEX_URL = flag('--url', `https://${REPO.split('/')[0].toLowerCase()}.github.io/${REPO.split('/')[1]}/index.json`);

if (typeof commit !== 'string' || /^[0-9a-f]{40}$/.test(commit) === false) {
  console.error('usage: node tools/make_market_index.mjs <40-hex-commit> [--url <index URL>] [--out <dir>]');
  process.exit(2);
}

const pkg = JSON.parse(await readFile(join(BASE, 'whale-aside', 'package.json'), 'utf8'));

/** Unix seconds for the release stamp; override with --publish-timestamp when backdating. */
function publishStamp() {
  const given = flag('--publish-timestamp', '');
  if (given !== '') {
    const n = Number(given);
    if (!Number.isInteger(n) || n < 0) throw new Error('--publish-timestamp must be a non-negative integer');
    return n;
  }
  return Math.floor(Date.now() / 1000);
}

const zhDescription = '鲸鱼娘小独白：注入鲸鱼娘人设并注册 whale_aside 工具，把模型每个新任务开始时的一句内心独白渲染成聊天里的鲸鱼娘气泡，带情绪贴图，并用 Edge TTS 朗读（默认晓伊 +22Hz，音色可在气泡面板或 ~/.dsh/whale-voice.json 自定义，合成失败自动回退浏览器系统音）。注意：语音走的是 Edge「大声朗读」的非官方消费者端点，微软未声明允许再分发其输出；美术素材按 as-is 分发、不含在 MIT 许可内，来源与下架联系方式见 PROVENANCE.md。';
const enDescription = 'Whale Girl Aside: injects a whale-girl persona and registers the whale_aside tool, rendering the model\'s one-line inner monologue at the start of each task as a speech bubble with a mood sticker, spoken by Edge TTS (zh-CN-XiaoyiNeural +22 Hz by default; timbre configurable from the bubble badge or ~/.dsh/whale-voice.json, with automatic fallback to the browser voice). Note: the voice uses Edge Read Aloud\'s unofficial consumer endpoint, whose output Microsoft has not documented as redistributable; the artwork ships as-is and is outside the MIT license — see PROVENANCE.md.';

const index = {
  format: 1,
  title: { en: 'Whale Girl Aside index', zh: '鲸鱼娘小独白 插件索引' },
  description: {
    en: 'Community index hosting dsh-whale-aside, installed from its public Git repository pinned to a commit.',
    zh: '收录 dsh-whale-aside 的社区索引，从公开 Git 仓库按 commit 钉版本安装。',
  },
  metadata: {
    categories: {
      persona: { title: { en: 'Persona & companions', zh: '人设与陪伴' } },
      voice: { title: { en: 'Speech & audio', zh: '语音与音频' } },
      interface: { title: { en: 'Interface & decoration', zh: '界面与装饰' } },
    },
    labels: {
      chinese: { title: { en: 'Chinese UI', zh: '中文界面' } },
      'edge-tts': { title: { en: 'Uses Edge TTS', zh: '使用 Edge TTS' } },
      'git-source': { title: { en: 'Installed from Git', zh: '从 Git 安装' } },
    },
  },
  plugins: [
    {
      name: pkg.name,
      title: { en: 'Whale Girl Aside', zh: '鲸鱼娘小独白' },
      description: { en: enDescription, zh: zhDescription },
      icon: 'icon.svg',
      author: typeof pkg.author === 'string' ? pkg.author : REPO.split('/')[0],
      homepage: `https://github.com/${REPO}`,
      repository: {
        url: `https://github.com/${REPO}`,
        directory: 'whale-aside',
      },
      metadata: {
        category: 'persona',
        keywords: pkg.keywords ?? [],
        labels: ['chinese', 'edge-tts', 'git-source'],
      },
      versions: [
        {
          version: pkg.version,
          publishTimestamp: publishStamp(),
          source: {
            type: 'git',
            url: `https://github.com/${REPO}.git`,
            commit,
            path: 'whale-aside',
          },
          engines: pkg.engines ?? {},
        },
      ],
    },
  ],
};

await mkdir(OUT_DIR, { recursive: true });
await writeFile(join(OUT_DIR, 'index.json'), `${JSON.stringify(index, null, 2)}\n`, 'utf8');
await copyFile(join(BASE, 'whale-aside', 'icon.svg'), join(OUT_DIR, 'icon.svg'));

/* ------------------------------------------------------------------ *
 * Validate with the official rule set, exactly as the Host would.
 * ------------------------------------------------------------------ */
// The package is not vendored, and Node resolves bare specifiers from this script's
// directory, which will not see a scratch install. Load it by absolute path instead:
// its own `semver` import then resolves relative to where it actually lives.
const CANDIDATES = [
  process.env.DSH_MARKET_INDEX_PKG,
  join(BASE, '.work', 'validator', 'node_modules', '@deepseek-ai', 'dsh-plugin-market-index'),
  join(BASE, 'node_modules', '@deepseek-ai', 'dsh-plugin-market-index'),
].filter((p) => typeof p === 'string' && p !== '');

let parseMarketIndex;
let marketInstallTarget;
let loadedFrom = null;
const tried = [];
for (const dir of CANDIDATES) {
  const entry = join(dir, 'lib', 'index.js');
  tried.push(entry);
  try {
    ({ parseMarketIndex, marketInstallTarget } = await import(pathToFileURL(entry).href));
    loadedFrom = dir;
    break;
  } catch (error) {
    if (error && error.code !== 'ERR_MODULE_NOT_FOUND' && error.code !== 'ENOENT') {
      console.error(`validator at ${dir} failed to load: ${error.message}`);
    }
  }
}
if (loadedFrom === null) {
  console.error('format-1 validator not found. Install it once, then re-run:');
  console.error('  npm install --prefix .work/validator @deepseek-ai/dsh-plugin-market-index');
  console.error(`tried:\n  ${tried.join('\n  ')}`);
  process.exit(3);
}

let validated;
try {
  validated = parseMarketIndex(JSON.parse(await readFile(join(OUT_DIR, 'index.json'), 'utf8')), INDEX_URL);
} catch (error) {
  console.error(`INDEX INVALID  ${error.name}: ${error.message}`);
  if (error.path !== undefined) console.error(`  at ${error.path} — ${error.reason}`);
  process.exit(1);
}

const target = marketInstallTarget(validated.plugins[0].name, validated.plugins[0].versions[0]);
console.log(`wrote ${join('market', 'index.json')} and ${join('market', 'icon.svg')}`);
console.log(`validated: format ${validated.format}, ${validated.plugins.length} plugin, `
  + `${validated.plugins[0].versions.length} version, title langs=${Object.keys(validated.title).join('/')}`);
console.log(`icon resolved -> ${validated.plugins[0].icon}`);
console.log(`install spec -> ${target.spec}`);
console.log(`pinned commit -> ${commit}`);
console.log(`publishTimestamp -> ${validated.plugins[0].versions[0].publishTimestamp}`);
console.log('OK: the index satisfies format 1.');
