# 鲸鱼娘插件：语音合成与 GIF 落地方案（whale-aside）

> 回答用户两问：②「语音合成怎么给插件一个合成模型」③「GIF 图放插件本地吗」。前提：`whale_aside` 工具契约 `{ text, mood }` 不变，只加语音/图标两条旁路。
> 基座：本机 DSH 的 app.asar 内包源码 + `cordis_inspect_query`。`待验证` = 撰写时无法实测。
> **修订（同日实测）**：pwsh 已恢复；`Slots.listSubTree` 已确认 `tool.call.toolview` 的 occupant 含 `callId`；已装插件的 `/whale-aside/assets/gifs/<mood>.gif` 七个槽位全部返回 `200 image/gif`，穿越测试 404。故 §8 中“client inspect 超时 / pwsh 不可用”两项已消除。
>
> **修订二（2026-11-15，whale-aside 1.3.0）**：方案 A（浏览器 Web Speech）早已不是主路——现在主路是宿主 Edge TTS，浏览器只剩兜底，且音色改为**数据可配**：气泡上的发声徽章选择器（本浏览器）+ `~/.dsh/whale-voice.json`（全局，热加载）。当天定位并修掉两个真实故障：运行时被重新装配抹掉 `edge_tts`（改由 `~/.dsh/whale-tts/lib` + `PYTHONPATH` 兜住，并把 stderr 回传显示），以及 `--rate -3%` 被 argparse 当成选项导致害羞/慵懒/无语三档永远拿不到音频（改等号形式）。现状与排查见 [voice-customization.md](voice-customization.md)。

## 1. 现状结论（均已在安装包里核对）

1. **Harness 没有 TTS 服务。** 唯一语音服务 `speechToText` 只有 `register/listProviders/follow/snapshot/configure/prepare/cancelPreparation/resolve/transcribe`，全是“语音→文字”；experimental 语音包也只有 `dsh-experimental-speech-to-text(-sensevoice)`、`dsh-experimental-api-speech-to-text`（转录）。
   证据：`cordis_inspect_query(host, Service, {service:"speechToText"})`；`references/packages.md` experimental 段。
2. **可注册同源 HTTP 路由。** `ctx.webServer.register(route)` 返回 disposer；`WebRoute = { kind:'exact'|'prefix', path, handler(req,res) }`（Node `IncomingMessage`/`ServerResponse`）；prefix 命中“相等或以 `<prefix>/` 开头”，最长前缀优先；webserver 不鉴权，响应由 handler 完全拥有。
   证据：`cordis_inspect_query(host, Service, {service:"webServer"})`；`@deepseek-ai/dsh-host-webserver/lib/index.js` 的 `register()`/`match()`。
3. **静态资源路由有现成先例。** `dsh-host-open-in-app` 有 3 条路由（`GET /open-in-app/apps`、`GET /open-in-app/icon` 前缀、`POST /open-in-app/open`）；图标路由手写 `content-type`、`cache-control: public, max-age=3600`，并用 `connection.requestRejection(req)` 做 Host/Origin/登录 cookie 护栏。frontend-static 则默认公开非 index 资源，只有 index 走 `authorizeIndex`。
   证据：`@deepseek-ai/dsh-host-open-in-app/lib/index.js` 第 1126–1133、1271–1319 行；`@deepseek-ai/dsh-host-frontend-static/lib/index.js` 第 10–16、49–75 行。
4. **客户端半边调不到 Host Service。** 走 Remote 要 Typert 生成定义 + `ctx.remote.$mount(contribution)`（重）；现有客户端 inject 是 `remote/slots/locale/pluginNavigation` 这类。open-in-app 客户端改用普通 `fetch()` 访问同源路由（路径取 document-relative 形式）。
   证据：`@deepseek-ai/dsh-experimental-client-ui-voice-input/lib/client.js` 第 2869–2975 行；`@deepseek-ai/dsh-client-ui-open-in-app/lib/client.js` 第 11–16、64–120 行。
5. **本地模型有成熟先例（SenseVoice）。** Config 强制绝对路径 `dataRoot`/`modelDirectory`，用 `ctx.subprocess.spawn` 起自带 worker，含 HF 源探测下载、磁盘估算、preparation 状态机、idle 停机。
   证据：`@deepseek-ai/dsh-experimental-speech-to-text-sensevoice/lib/index.js` 第 745–814、883–955 行。
6. **工具视图能拿到 `callId`。** `tool.call.toolview` 按 wire tool 名 keyed 注册，occupant props（`ToolCallOwnerProps`）含 `callId`、`toolName`、phase，且 `callId` 三阶段不变。
   证据：`@deepseek-ai/dsh-client-ui-tool/README.md` 第 34–52 行；`@deepseek-ai/dsh-client-ui-cordis/lib/client.js` 第 1446–1486 行；本仓 `whale-aside/client.js` 第 311–319 行已按 key `whale_aside` 注册（组件只读 `props.block`）。

**结论：** 语音 = A 浏览器 Web Speech（v1，零依赖）→ B Host 路由 + 本地引擎（v2）→ 克隆音色（v3）；GIF = 插件本地 assets + 同一个 Host 前缀路由。两条都不改工具契约，也不需要 Typert Remote；v1 的工具描述已写明“用于语音和表情图”（`whale-aside/index.js` 第 36 行），方向与现契约一致。

## 2. 三种 TTS 方案对比

| 维度 | A 浏览器 Web Speech | B 本地模型引擎 | C 云端 API |
|---|---|---|---|
| 依赖 | 0（`window.speechSynthesis`） | Python/Node 或 exe + 模型文件 | 网络 + API Key |
| 体积 | 0 | edge-tts ~10MB（仍联网）；Piper 60–100MB；克隆模型数百 MB–GB | 0 |
| 延迟 | 首次选 voice 几十 ms | Piper 0.3–1.5s；克隆 ≥1s；冷启动另计 | 200ms–1s + 网络 |
| 音色 | 系统 zh-CN 声，机械，不可定制 | 可选 zh 女声，克隆可贴人设 | 最好，可指定/克隆 |
| 离线 | 是 | Piper 是；edge-tts 否 | 否 |
| 风险 | 无 | 模型/引擎许可证（待核验） | 条款与费用 |
| 工作量 | 小（纯 client） | 中（Config + subprocess + 缓存 + 路由） | 小-中（Key + 路由） |

推荐路线（同一 `VoiceProvider` 接口后面换实现）：**A** 用 `speechSynthesis`，zh-CN、`rate≈1.15`、`pitch≈1.5`，不做 Host 改动；**B1** Host 路由 + `edge-tts`（`zh-CN-XiaoyiNeural` 为候选，voice 列表待核验）；**B2** Piper 全离线（zh_CN `.onnx` + 可执行文件，放外部目录）；**C** GPT-SoVITS/CosyVoice 克隆（吃 GPU）。

## 3. “给插件一个合成模型”的三种落地方式

| 方式 | 做法 | 优点 | 代价/风险 | 建议 |
|---|---|---|---|---|
| ① bundle 内 `assets/models/` | 模型随包，`package.json files` 列出 | 版本一致、安装即用 | 安装包膨胀、升级重装；`install_bundle` 本地目录是链接 checkout，`files` 不过滤链接目录 | 只放小文件（GIF/试听） |
| ② Config 指向外部模型目录 | Config 加绝对路径字段，`apply` 里校验 `isAbsolute`（照 SenseVoice） | 不进安装包、可复用、换模型不改代码 | 路径失效/权限；用户自备文件 | **本地引擎首选** |
| ③ `$DSH_HOME` 托管目录 | 插件在 `$DSH_HOME/whale-aside/...` 首次使用时下载/校验/缓存 | 跨 profile 复用、可做进度 | 下载失败/断点/许可证；首用等待 | v2.5 自动下载 |
| ④ 云端（无模型） | Key 走 `credentialRef('WHALE_TTS_API_KEY')` + Config `.role('credential-ref')` | 零体积、音色好 | 联网、费用、隐私 | 可选实现 |

凭证顺序：凭证文件 > 启动环境 > 项目 `.env` > `$DSH_HOME/.env`（证据：`@deepseek-ai/dsh-llm-deepseek-api-key/lib/index.js` 的 `credentialRef(...)`；`@deepseek-ai/dsh-credentials-local/README.md` 第 12、69–80 行）。**模型/图片不是 package import**，不必进 `exports`，只需进 `files`（发布时）并由 Host 用 Node fs 读（证据：`references/host-plugin.md` 第 35、44–51 行）。

## 4. VoiceProvider 接口草案（Host 侧）

```ts
type Mood = 'tsun' | 'sweet' | 'lazy' | 'shy' | 'panic' | 'hungry' | 'smug' // 与 whale-aside/index.js 第 33 行 MOODS 一致
interface VoiceClip { bytes: Uint8Array; mime: 'audio/mpeg' | 'audio/wav' }
interface VoiceProvider {
  readonly id: string
  prepare?(): Promise<void>      // 起进程/探活，失败不阻断聊天
  synthesize(req: { text: string; mood: Mood; callId: string; signal: AbortSignal }): Promise<VoiceClip>
  dispose?(): Promise<void>
}
// Config（schemastery）：voice.mode: 'off'|'browser'|'local'|'cloud'
// voice.engine / executable / modelDir / voice / timeoutMs / cacheDir；gif.dir / gif.baseUrl / gif.enabled
```

## 5. Host 路由 + 客户端播放生命周期（代码草图）

| 路由 | 方法 | 作用 | 头 |
|---|---|---|---|
| `/whale-aside/assets`（prefix） | GET/HEAD | `gif/<mood>.gif` 与 `voice/<callId>.mp3` | `content-type` 按扩展名；`cache-control: public, max-age=3600` |
| `/whale-aside/voice`（exact） | POST | 按 `{callId,text,mood}` 合成，落缓存后回 `{url}` | `application/json`、`no-store`；明确 `415/413/429` |
| `/whale-aside/health`（可选） | GET | 引擎 ready / mode | `no-store` |

要点：路由路径全局唯一（重复注册 throw）；prefix 自己剥前缀、只认白名单文件名；POST 限长度/并发，并用 `connection.requestRejection` 做同源栅栏。

```ts
// whale-aside/host/routes.js（示意）
const assetsRoot = fileURLToPath(new URL('../assets', import.meta.url))
const AUDIO_MIME = { '.mp3': 'audio/mpeg', '.wav': 'audio/wav' }
const cache = new Map<string, VoiceClip>()          // callId → clip，LRU ~32

ctx.effect(() => ctx.webServer.register({
  kind: 'prefix', path: '/whale-aside/assets',
  async handler(req, res) {
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405, { allow: 'GET, HEAD' }); res.end(); return }
    const rel = decodeURIComponent(new URL(req.url ?? '/', 'http://x').pathname.slice('/whale-aside/assets/'.length))
    if (!/^(gif\/[a-z]+\.gif|voice\/[A-Za-z0-9_-]{1,64}\.(mp3|wav))$/.test(rel)) { res.writeHead(404); res.end(); return }
    try {
      const bytes = await readFile(join(assetsRoot, rel))
      res.writeHead(200, { 'content-type': rel.endsWith('.gif') ? 'image/gif' : AUDIO_MIME[extname(rel)]!,
                           'cache-control': 'public, max-age=3600' })
      res.end(req.method === 'HEAD' ? undefined : bytes)
    } catch { res.writeHead(404); res.end() }
  },
}), 'whale-aside: assets')

ctx.effect(() => ctx.webServer.register({
  kind: 'exact', path: '/whale-aside/voice',
  async handler(req, res) { /* 校验 method/content-type/长度 → provider.synthesize → cache → { url: `whale-aside/assets/voice/${callId}.mp3` } */ },
}), 'whale-aside: voice')
```

证据：路由形态/重复注册 throw/最长前缀匹配见 `webServer` 契约与 `dsh-host-webserver/lib/index.js`；`content-type`+`cache-control` 写法照 open-in-app 图标路由（第 1314–1317 行）。

**客户端播放生命周期**（新增 `whale-aside/client-voice.js`，或直接内联进现有 `client.js`；注册沿用 v1 的 `ctx.slots.inject('tool.call.toolview', ... key:'whale_aside')`）：一个共享 `HTMLAudioElement`；按 `callId` 去重；只播“挂载期间从流式变为 settled”的 aside；历史回放/HMR 重挂载不重播；静音与音量用 `localStorage` 持久化。

```ts
const audio = new Audio()                                   // 单例，切歌先 pause() 再换 src
const played = new Set<string>()                            // callId
document.addEventListener('pointerdown', () => { audio.muted = false }, { once: true }) // 首次手势解锁

const seenSettled = useRef(false)
useEffect(() => {                                           // occupant props: callId + block
  const settled = Boolean(props.block) && 'kind' in props.block   // v1：settled 的 block 带 kind
  const wasSettled = seenSettled.current
  seenSettled.current = settled
  if (!settled || wasSettled || played.has(props.callId)) return   // 初始即 settled 的历史不播
  played.add(props.callId)
  void speakOnce(props.callId, aside.text, aside.mood)      // aside = deriveAside(props.block)
}, [props.block, props.callId])

async function speakOnce(callId: string, text: string, mood: Mood) {
  if (settings.muted) return
  if (mode === 'browser') {                                 // 方案 A
    const u = new SpeechSynthesisUtterance(text)
    Object.assign(u, { lang: 'zh-CN', rate: 1.15, pitch: 1.5, volume: settings.volume })
    speechSynthesis.speak(u); return
  }
  try {                                                     // 方案 B/C：同源 POST → 路由 URL
    const r = await fetch('whale-aside/voice', { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ callId, text, mood }), signal: AbortSignal.timeout(8000) })
    if (!r.ok) throw new Error(String(r.status))
    const { url } = await r.json()
    Object.assign(audio, { src: new URL(url, document.baseURI).href, volume: settings.volume })
    await audio.play()                                      // 首次手势前可能 NotAllowedError → 落 catch
  } catch { speakOnceBrowser(text) }                        // 可选降级
}
// 卸载：ctx.effect(() => () => { audio.pause(); speechSynthesis.cancel() })
```

- 自动播放：`play()` 在无用户手势时可能抛 `NotAllowedError`，`speechSynthesis` 在部分 Chromium 版本同样受限；策略是静音默认 + 手势解锁 + catch 不重试（平台约束，需实测，`待验证`）。
- 静音/音量：`localStorage`（键 `dsh.whale-aside.voice`）足够，v1 不新增客户端依赖；若以后要跨组件共享 UI 状态，可再引入 `@deepseek-ai/dsh-client-store`（需在 `dsh.client.external` 声明，细节 `待验证`）；气泡加喇叭按钮。

## 6. GIF 本地化方案（第 ③ 问：放插件本地）

**放本地。** 目录约定：`whale-aside/assets/gifs/<mood>.gif`（tsun/sweet/lazy/shy/panic/hungry/smug，与 mood 枚举一一对应）、可选 `_fallback.png`；`package.json` 的 `files` 加 `assets/**`（发布时）。

- **为什么本地**：离线可用；随版本 review/回滚；不引第三方 CDN（隐私、可用性、referrer 泄漏）；`<img>` 直接吃同源路由，无需 token。
- **体积**：实测按「宽 128px、保留全部 120 帧、8 帧步进（80ms/帧，12.5fps）」出图，单张 324–553KB、七张合计 3.2MB。早期为压体积做的 120KB / 40 帧 / 6fps 版本播放明显卡顿，已废弃。**结论：宁可 500KB 也不掉帧** —— 素材走本机同源路由、一次气泡只加载一张，体积不是瓶颈，帧率才是观感瓶颈。若日后要发到公共 npm 包再考虑降档。
- **服务**：`/whale-aside/assets` 前缀路由，`content-type: image/gif`，`cache-control: public, max-age=3600`；因为缓存 1 小时，`client.js` 的 `GIF_BASE` 拼图时带 `?v=GIF_VERSION`（当前 `'3'`）做 bust，**重做素材后必须 bump 这个常量**，否则浏览器会继续用旧图。
- **气泡用法**：v1 曾是“内联 SVG 尾巴 + 气泡文本”，无 `<img>`；**现已落地**：`whale-aside/client.js` 的 `GIF_BASE = '/whale-aside/assets/gifs/'`（第 58 行）拼 `mood + '.gif'` 渲染贴图，`onError` 回落 `MOOD_EMOJI`（hungry=🍚，其余 🐳），`prefers-reduced-motion` 时隐藏动图。实现在 `renderSticker()`。
- **Config 覆盖**：`gif.dir`（绝对路径，用户自加 GIF 不必重装）；`gif.baseUrl`（自建图床/远端：改动最小但断网即坏、有隐私/版权风险、无法随版本冻结，只作兜底，不作默认）。
- **无障碍**：`prefers-reduced-motion` 时用静态 PNG 或 emoji；`alt` 走 locale 文案。

## 7. 分阶段实施路线

| 阶段 | 内容 | 验收 |
|---|---|---|
| P1（v1，0 依赖） | 客户端 Web Speech + 喇叭静音 + 静音持久化；GIF 本地 7 张 + 前缀路由 + emoji 兜底 | **已完成**（`whale-aside@1.0.0` 已装入 desktop profile；路由七槽 200、穿越 404；slot occupant 已确认）。剩余验收需真人一轮对话听声音看动图 |
| P2（v2） | `POST /whale-aside/voice` + `VoiceProvider` + edge-tts；失败降级 Web Speech | 首次合成 P50 <2.5s；同 callId 不重复合成；断网不报错 |
| P3 | Piper 离线引擎（Config 指外部模型目录）+ 健康检查/预热；可选克隆音色或云 API | 无网可合成；模型缺失时可读报错并自动降级；同接口换实现，契约零改动 |

## 8. 风险清单 + 待验证

1. 自动播放/静音与首个片段延迟：手势前 `play()` 被拒；默认静音 + 手势解锁 + 6–8s 超时 + 降级 + 预热。
2. 体积与升级：大模型进 bundle 会膨胀安装包；用 Config 外部目录或 `$DSH_HOME` 托管。
3. 许可证：Piper voice、GPT-SoVITS/CosyVoice 权重、edge-tts 条款均需核验（`待验证`）。
4. 重复播放：历史/刷新/HMR 都会重挂载工具行；必须 `callId` + “block 从流式变为 settled”双条件。
5. 本地进程：`ctx.subprocess.spawn` 的真实可执行路径/参数需在真机终端验证（`待验证`；本会话 pwsh 已恢复，但 TTS 引擎尚未落地）。
6. 路由与路径：webserver 不自动鉴权，合成 POST 建议加栅栏与限流（`待验证`）；只接受白名单正则，拒绝 `..`、绝对路径、非法扩展名。**已实测**：GET `/whale-aside/assets/gifs/../../index.js` → 404（白名单挡住，未触达 fs）。
- ~~live slot 的 `props.callId` 是否与 README 一致~~ **已实测**：`Slots.listSubTree('tool.call.toolview')` 显示 occupant `whale_aside` 由 `Kb` 注册且 active，`ToolCallCommonProps.callId` 存在。
- `connection.requestRejection` 对同源 `<img>/<audio>` GET、对同源 POST 的判定（读实现或实测）。
- 本机可用的 TTS 引擎/可执行路径（pwsh 已可用，但未选型实测）。

## 9. 下一步清单（文件级）

> P1 已落地，下面 1/5 中的常量与素材已存在（`whale-aside/index.js` 的 `MOODS`/`ASSETS_ROUTE`/`ASSET_PATTERN`、`whale-aside/assets/gifs/*.gif` + `SOURCES.md`）；其余为 P2/P3 待办。

1. `whale-aside/shared/voice.js`：`Mood`、`VoiceProvider`、路由路径常量（Host 侧；client 侧在 `client.js` 内复制常量，浏览器模块不 import Node 文件）。
2. `whale-aside/host/routes.js`：`/whale-aside/assets` 前缀（已有，在 `index.js` 的 `serveAsset`）+ `/whale-aside/voice` POST + 白名单/缓存/限流。
3. `whale-aside/host/voice/{edge-tts,piper,cloud}.js`：各实现 `VoiceProvider` 的 `prepare/synthesize/dispose`。
4. `whale-aside/client-voice.js`（或内联 `client.js`）：替换现有 `speakLine()`（Web Speech）为可插拔播放器：单例 `Audio`、`played:Set<callId>`（已有）、settled 转移判定（已有 `previousPhase` ref）、手势解锁、mute/volume、合成失败降级回 `speechSynthesis`。
5. `whale-aside/assets/gifs/*.gif`：7 张 mood 图（已就位，单张 324–553KB，128px 宽，120 帧全帧，素材来自 PC2005-cloud/dsh-pet，MIT，见 `assets/gifs/SOURCES.md`）；`package.json` 的 `files` 已含 `assets`。
6. `whale-aside/index.js`：`export const Config`（voice/gif 字段、绝对路径校验）+ `inject` 追加 `subprocess`/`credentials`（按需）；实现后回填本文件的实测/许可证结论。
