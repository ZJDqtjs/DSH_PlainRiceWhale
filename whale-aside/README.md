# 鲸鱼娘小独白 · dsh-plain-rice-whale

DeepSeek Harness（DSH）插件 bundle。它给会话注入「鲸鱼娘」人设，并注册 `whale_aside` 工具：模型在每个新任务开始时写下的那句内心独白，会被渲染成聊天里的一只鲸鱼娘气泡，带情绪贴图，并用 Edge TTS 朗读出来。

许可：代码 [MIT](https://github.com/ZJDqtjs/DSH_PlainRiceWhale/blob/main/LICENSE)，美术与音频素材**不在 MIT 内**，逐项来源与下架联系方式见 [PROVENANCE.md](https://github.com/ZJDqtjs/DSH_PlainRiceWhale/blob/main/PROVENANCE.md)。

> 注意：这两个文件在**仓库根目录**，不在 npm 压缩包里（`files` 只覆盖本目录）。所以本段用绝对链接，并且下面「已知限制」与 `assets/NOTICE.md` 会把素材条款和下架联系方式**就地写全**，装了包的人不需要仓库文件也能看到。

## 注册了什么

| 贡献 | 说明 |
| --- | --- |
| 系统提示段 | 鲸鱼娘人设 + 「每个新任务先写一句小声嘀咕、再调用一次 `whale_aside`」协议 |
| `whale_aside` 工具 | 入参 `{ text, mood }`，`mood` 取 8 个情绪之一；同一条用户消息内只调用一次 |
| `/whale-aside/assets` 路由 | 同源提供情绪贴图。白名单是逐个文件名的字面匹配，目录穿越一律 404 |
| `/whale-aside/voice` 路由 | `POST` 用 Edge TTS 合成并把 MP3 缓存到 `~/.dsh/whale-audio`；`GET` 回放缓存；`GET /whale-aside/voice` 返回当前生效配置、解释器路径、最近一次失败原因与冷却剩余 |

## 情绪

| mood | 中文 | 语音韵律（相对基准 `zh-CN-XiaoyiNeural` +22 Hz） |
| --- | --- | --- |
| `tsun` | 傲娇 | +8 Hz / +3 % |
| `sweet` | 甜 | +23 Hz / +0 % |
| `lazy` | 懒 | −12 Hz / −8 % |
| `shy` | 害羞 | +13 Hz / −3 % |
| `panic` | 慌 | +33 Hz / +12 % |
| `hungry` | 想吃米饭 | +3 Hz / +2 % |
| `smug` | 得意 | +16 Hz / +0 % |
| `meh` | 无语 | −6 Hz / −5 % |

情绪词表与贴图清单是**两层**（`MOODS` 与 `MOOD_STICKERS` / `STICKER_ASSETS`）。没有贴图的情绪不渲染 `<img>`、不发起请求，因此不会出现 404 闪烁，气泡只是退化为纯文字独白。

## 音色配置

三层覆盖，后者优先：

1. `index.js` 内置默认值；
2. `~/.dsh/whale-voice.json` —— 全局默认，对所有会话生效；
3. 气泡上的发声徽章面板 —— 本页选择音色 / 音高 / 语速，可「试听这句」。

徽章会**如实显示**刚才发声的是 Edge TTS 还是浏览器系统音，不做美化。

## 安装

```bash
# 从插件市场（Discover）安装，见仓库根 README 的索引地址
# 或以本地链接方式装进某个 profile 做开发
pnpm --dir ~/.dsh/profiles/<profile> add -D link:/path/to/DSH_PlainRiceWhale/whale-aside
```

改完代码需要重载插件或重启 DSH；Client 半边要刷新浏览器（安装型 bundle 不在 `dev:web` 的 HMR 范围内）。

## 已知限制

- **`edge-tts` 不是官方 API。** 它调用 Microsoft Edge「大声朗读」的消费者端点，微软未公开声明允许再分发经此途径生成的音频，端点也可能随时变更、限流或停止。本插件**不打包** `edge-tts`，而是首次使用时 `pip install --target ~/.dsh/whale-tts/lib` 装到私有目录并以子进程调用（子进程调用不使本插件的 MIT 代码构成 GPL-3.0 衍生作品）。需要可商用的稳定方案请改用 Azure AI Speech 官方接口——合成失败时插件会自动回退到浏览器 Web Speech API，功能不中断。
- 素材（贴图与试听音频）按 as-is 分发、不授予再许可、不声明为原创作品；逐项来源与元数据核查见 [PROVENANCE.md](https://github.com/ZJDqtjs/DSH_PlainRiceWhale/blob/main/PROVENANCE.md)。
- **权利主张（takedown）**：若您是素材的权利人，请通过 [GitHub DMCA](https://github.com/dmca/forms/dmca-takedown-notice)、[仓库安全通告](https://github.com/ZJDqtjs/DSH_PlainRiceWhale/security/advisories/new) 或邮件 <136884860+ZJDqtjs@users.noreply.github.com> 联系，注明权属与被指认的文件路径。承诺**收到有效通知 72 小时内先下架再沟通**（删除文件、移除引用条目、发布新版本，并从索引中撤掉该版本），无需先证明侵权成立。
- 语音合成需要联网；离线时自动走浏览器系统音。

## 自检

```bash
node --check index.js && node --check client.js
node ../tools/check_sticker_ext.mjs      # Host 清单 / Client 清单 / 磁盘文件 三方一致
python ../tools/meme_verify.py           # 贴图体检：尺寸、帧、透明占比、绿幕、体积
python ../tools/asset_metadata_audit.py  # 素材元数据核查
```
