# 鲸鱼娘小独白 · whale-aside

一个 [DeepSeek Harness](https://github.com/deepseek-ai)（DSH）插件 bundle：给会话注入「鲸鱼娘」人设，注册 `whale_aside` 工具，把模型在每个新任务开始时的一句**内心小独白**渲染成聊天里的鲸鱼娘气泡——带情绪贴图，并用 Edge TTS 朗读出来。

```
┌ 小独白  🐳 无语  🔊 ─────────────┐
│ 主人干嘛突然盯着我看啦…    [贴图] │
└──────────────────────────────────┘
```

## 目录

```
whale-aside/     插件本体（Host 半边 index.js + Client 半边 client.js + 素材）
tools/           素材抓取、清洗、合成与自检脚本（Python / Node）
docs/            设计与调研记录
samples/         语音试听样本
```

## 安装

插件是**纯 ESM、零依赖**的 bundle：`index.js` 只 import `node:` 内置模块，`client.js` 走 DSH 的 `window.__ModuleLoader__`，因此装进 profile 后不需要 `npm install`。

```bash
# 以本地链接方式装进某个 profile（改动即时生效，无需重新打包）
pnpm --dir ~/.dsh/profiles/<profile> add -D link:/path/to/this/repo/whale-aside
```

`whale-aside/cordis.patch.yml` 会把 `whale-aside` 这个 id 插入 profile 的启动 patch。改完代码需要**重载插件或重启 DSH**；Client 半边要**刷新浏览器**（安装型 bundle 不在 `dev:web` 的 HMR 范围内）。

## 它注册了什么

| 贡献 | 说明 |
| --- | --- |
| 系统提示段 | 鲸鱼娘人设 + 「每个新任务先写一句小声嘀咕、再调一次 `whale_aside`」的协议 |
| `whale_aside` 工具 | 入参 `{ text, mood }`，`mood` 取 8 个情绪之一；每个新任务只调用一次 |
| `/whale-aside/assets` 路由 | 同源提供情绪贴图，白名单逐个文件名匹配，目录穿越一律 404 |
| `/whale-aside/voice` 路由 | `POST` 用 Edge TTS 合成并把 MP3 缓存到 `~/.dsh/whale-audio`，`GET` 回放缓存，`GET /` 返回当前生效配置 |

## 情绪与贴图

`MOODS`（情绪词表）和 `MOOD_STICKERS`（贴图清单）是**两层**，故意分开：

| mood | 中文 | 语音韵律（相对基准 +22Hz） | 贴图 |
| --- | --- | --- | --- |
| `tsun` | 傲娇 | +8Hz / +3% | — |
| `sweet` | 甜 | +23Hz / +0% | — |
| `lazy` | 懒 | −12Hz / −8% | — |
| `shy` | 害羞 | +13Hz / −3% | — |
| `panic` | 慌 | +33Hz / +12% | — |
| `hungry` | 想吃米饭 | +3Hz / +2% | — |
| `smug` | 得意 | +16Hz / +0% | — |
| `meh` | 无语 | −6Hz / −5% | `meme2_clean.png` |

那七张动图是旧资源、已于 2026-11-15 下线，但情绪键**保留**——它们各自带着一条 TTS 韵律设置，砍掉就等于废掉语音表情。没有贴图的情绪在前端**不渲染 `<img>`、不发请求**，所以不会有 404 闪烁。来源、清洗过程与 MIT 署名见 [`whale-aside/assets/gifs/SOURCES.md`](whale-aside/assets/gifs/SOURCES.md)。

## 语音

优先走 Host 的 Edge TTS（默认 `zh-CN-XiaoyiNeural`），失败或离线时自动回退浏览器 Web Speech API。气泡上的徽章会**如实显示**刚才发声的是 Edge 还是系统音。

音色是数据不是代码，三层覆盖：

1. `index.js` 里的默认值；
2. `~/.dsh/whale-voice.json` —— 全局默认，对所有会话生效；
3. 气泡里的选取面板（音色 / 音高 / 语速 + 「试听这句」）—— 本页覆盖，随每次 `POST` 带上。

`edge-tts` 装在插件私有目录 `~/.dsh/whale-tts/lib`，不污染宿主 Python；合成失败会记录原因并进入冷却，`GET /whale-aside/voice` 能把解释器路径、缓存目录、冷却剩余和最近一次错误一次看全。

## 自检

```bash
node --check whale-aside/index.js
node --check whale-aside/client.js
node tools/check_sticker_ext.mjs   # Host 清单 / Client 清单 / 磁盘文件 三方一致
python tools/meme_verify.py        # 素材体检：尺寸、帧、透明占比、绿幕残留、体积预算
```

`check_sticker_ext.mjs` 会把「素材目录里的孤儿文件」和「清单里引用了却不在磁盘上的文件」都当成失败——把 GIF 压成 zip 留在素材目录里导致整批 404 这种事故，就是这么被抓住的。

## 仓库里没有的东西

`.gitignore` 明确排除了两类内容，都不是遗漏：

- **第三方媒体**：调研音色和贴图时抓下来的 B 站视频、语音包、桌宠素材原图、抓取页面与日志（约 70MB）。它们不归我们所有，也不该由我们分发；全部能用 `tools/` 里的抓取脚本重新获得。
- **`.work/`**：一次性草稿、探测输出、TTS 试听、梗图原图。

## 许可

插件代码按仓库声明的许可使用。`assets/gifs/SOURCES.md` 保留了已退役动图素材的 **MIT** 署名（PC2005-cloud/dsh-pet）。
