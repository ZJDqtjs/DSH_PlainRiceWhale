# 素材来源与权利主张说明 / Asset Provenance & Takedown

> 本项目代码基于 [MIT License](LICENSE) 开源。
>
> ⚠️ `assets/` 与 `samples/` 下的美术素材（图片 / 动图 / 音效）**不在 MIT 覆盖范围内**：它们由维护者提供或使用 AI 工具生成，按「原样（as-is）」随插件分发、仅供运行本插件使用，不授予再许可，也不声明为原创作品。逐项来源、元数据清理说明与权利主张（takedown）方式见本文。

## 1. 范围界定

| 内容 | 许可 |
| --- | --- |
| `whale-aside/*.js`、`whale-aside/*.json`、`whale-aside/*.yml`、`tools/`、`docs/`、`README.md` | **MIT**（见 [LICENSE](LICENSE)） |
| `whale-aside/assets/**`、`samples/**` | **不在 MIT 内**，按 as-is 分发，仅用于运行本插件 |

区分理由：代码是本项目的原创表达；美术与音频素材是**第三方作品或第三方服务的输出**，维护者不拥有可以转授给他人的权利。把它们写进 MIT 会构成超出自身权限的承诺，因此单独排除。

## 2. 逐项清单

### 2.1 `whale-aside/assets/gifs/meme2_clean.png` — 411.9 KB，850×807 PNG

| 字段 | 内容 |
| --- | --- |
| 类型 | 位图美术素材 |
| 来源 | **第三方社区流传的动漫贴纸**（B 站，蓝毛鲸鱼娘形象），由维护者提供给本项目 |
| 是否原创 | **否**，本项目不主张该形象的原创著作权 |
| 加工方式 | 见 [`tools/meme2_clean.py`](tools/meme2_clean.py)：对连通域分解后，**仅删除气泡内的文字笔画块**（28 块 / 8243 ink px，每块外扩 4px 消除 JPEG 振铃），气泡外框、思考小圈、人物与强调符号均未改动 |
| 与原图差异 | 原图气泡内印有一句辱骂性文字，**本仓库分发的版本已将该文字完全移除**；原始无标注图与带标注截图（`.work/meme_src.jpg`、`.work/meme2_src.png`）**不在仓库中**，也不随任何发行物分发 |
| 用途 | 插件 `meh`（无语）情绪的气泡贴图 |
| 可否移除 | **可以且不影响功能**：`MOOD_STICKERS` 为空时前端不再渲染 `<img>`，气泡自动退化为纯文字独白（见 §5） |

### 2.2 `whale-aside/icon.svg` — 0.6 KB，64×64 SVG

| 字段 | 内容 |
| --- | --- |
| 类型 | 矢量图标 |
| 来源 | 维护者提供，为本插件绘制的鲸鱼尾鳍图标 |
| 元数据 | 纯手写 `path` 数据；**不含** Inkscape / Sodipodi / RDF / Dublin Core 命名空间，也无 `generator` 属性或 XML 注释 |
| 可否替换 | 可以，图标仅是显示资源，替换不影响任何功能 |

### 2.3 `samples/*.mp3` — 8 个文件，共约 308 KB

| 文件 | 大小 | 按文件名标注的音色与音高 |
| --- | --- | --- |
| `audition-hsiaochen-p22.mp3` | 45.8 KB | `zh-TW-HsiaoChenNeural` +22 Hz |
| `audition-xiaobei-p22.mp3` | 43.6 KB | `zh-CN-XiaobeiNeural` +22 Hz |
| `audition-xiaoxiao-p22.mp3` | 40.2 KB | `zh-CN-XiaoxiaoNeural` +22 Hz |
| `audition-xiaoyi-p22.mp3` | 41.9 KB | `zh-CN-XiaoyiNeural` +22 Hz |
| `audition-yunxia-p22.mp3` | 42.6 KB | `zh-CN-YunxiaNeural` +22 Hz |
| `whale-voice-xiaoxiao-p30.mp3` | 30.1 KB | `zh-CN-XiaoxiaoNeural` +30 Hz |
| `whale-voice-xiaoyi-p22.mp3` | 32.2 KB | `zh-CN-XiaoyiNeural` +22 Hz |
| `whale-voice-xiaoyi-p45.mp3` | 32.2 KB | `zh-CN-XiaoyiNeural` +45 Hz |

| 字段 | 内容 |
| --- | --- |
| 类型 | 文本转语音（TTS）合成输出 |
| 生成方式 | 由 `edge-tts` 客户端调用 Microsoft Edge「大声朗读」的**消费者端点**合成，文本由维护者撰写 |
| 服务性质 | ⚠️ 该端点**不是** Azure AI Speech 官方 API。微软未公开声明允许再分发经此途径生成的音频，其官方口径是商用请使用 Azure AI Speech。相关说明见 §6 |
| 音色归属 | 神经语音模型及其名称为 Microsoft 所有；本项目不主张任何权利 |
| 用途 | 仅供试听，用于说明插件的音高/语速效果；**插件运行不依赖这些文件**，删除后功能完全不变 |

## 3. 元数据清理说明

隐私与来源核查由 [`tools/asset_metadata_audit.py`](tools/asset_metadata_audit.py) 自动完成，可随时复现：

```bash
python tools/asset_metadata_audit.py
```

最近一次审计结论（10 个素材文件）：

- **无** EXIF / APP1 块、**无** GPS 位置信息、**无** ICC 色彩配置档；
- `meme2_clean.png`：**无** PNG `tEXt` / `iTXt` 文本块——即不含作者字段、软件字段、时间戳；
- 8 个 MP3：**无** ID3v2 标签，即不含 `TIT2`（标题）、`TPE1`（艺术家）、`TALB`（专辑）、`COMM`（注释）、`TENC`（编码器）帧；
- **唯一残留标记**：MP3 字节中含编码器字符串 `LAME`。它不含任何个人信息，仅表明编码工具。如需彻底清除，可用 `ffmpeg -map_metadata -1 -write_xing 0 -id3v2_version 0` 重编码；
- `icon.svg`：无编辑器命名空间与注释。

原始截图与中间产物一律放在 `.work/`，该目录已被 `.gitignore` 排除，不进入任何提交或发行包。

## 4. 已退役素材（不在仓库中，此处仅保留署名）

以下素材已于 2026-11-15 从本仓库移除，不再随任何版本分发；此处保留记录与署名，以备历史版本核对：

| 素材 | 原来源 | 署名 |
| --- | --- | --- |
| `tsun/sweet/lazy/shy/panic/hungry/smug` 七张 GIF | 开源桌宠项目 **PC2005-cloud/dsh-pet** 预览素材库 | **MIT License, Copyright (c) 2026 PC2005-cloud** — <https://github.com/PC2005-cloud/dsh-pet> |
| `meh.jpg`（同一贴纸的人像裁切） | 同 §2.1 | 已被 `meme2_clean.png` 取代并移除 |

对应的抓取与合成脚本（`tools/pet_probe.py`、`tools/build_mood_gifs.py` 等）仍保留在仓库中作为可复现记录，其素材目录 `tools/pet_gifs/` 已被 `.gitignore` 排除，**不随仓库分发**。

## 5. 移除请求不会破坏插件

这是有意的设计，也是本项目的配合诚意：

- 情绪贴图与情绪词表**解耦**（`MOOD_STICKERS` / `STICKER_ASSETS`）。被要求移除某张贴图时，只需删文件并从两张表里去掉对应条目；没有贴图的情绪**不发起任何请求**，因此不会出现 404 闪烁，气泡退化为纯文字独白。
- 音频试听文件与运行时完全无关，可直接删除。
- 语音功能在合成失败时自动回退到浏览器系统语音，因此即便 `edge-tts` 端点被限制，插件仍可运行。

## 6. 关于 Edge TTS 的诚实说明

- 本插件**默认不打包** `edge-tts`，而是在首次使用时以 `pip install --target ~/.dsh/whale-tts/lib` 安装到私有目录，并以子进程调用。这样做的一个附带好处是：`edge-tts` 为 GPL-3.0，子进程调用不使本插件的 MIT 代码构成衍生作品。
- 该途径依赖微软未公开文档化的消费者端点，**可能随时变更、限流或停止**。本项目不承诺其可用性，也不为其商用合规性背书。
- 若使用者需要可商用的稳定方案，应改用 **Azure AI Speech** 的官方 Text-to-Speech API（自带密钥与配额），或浏览器内置的 Web Speech API——本插件在后两者上均已具备降级路径。

## 7. 权利主张 / Takedown

### 中文

若您是本仓库中任一美术或音频素材的权利人（含形象著作权人、配音演员、声音模型权利人），认为其分发侵犯了您的权利，请通过以下**任一**渠道联系，并附上：权属说明、被指认的具体文件路径、以及您希望的处置方式。

1. **GitHub 官方 DMCA 流程**：<https://github.com/dmca/forms/dmca-takedown-notice>（指向本仓库与相应文件路径）
2. **仓库安全通告**：<https://github.com/ZJDqtjs/DSH_PlainRiceWhale/security/advisories/new>
3. **邮件**（经 GitHub 路由至维护者）：<136884860+ZJDqtjs@users.noreply.github.com>

**承诺的处置方式**：收到有效通知后 **72 小时内**先下架（删除文件 + 移除引用条目 + 发布新版本），再就权属问题沟通；不需要先证明侵权成立才动手。若某版本已分发至插件索引，会同步从索引中移除该版本。

### English

If you hold rights in any artwork or audio distributed in this repository (including character artwork, voice talent, or voice-model rights), please contact me through **any** of:

1. **GitHub's DMCA process**: <https://github.com/dmca/forms/dmca-takedown-notice>, naming this repository and the specific file paths;
2. **A private security advisory**: <https://github.com/ZJDqtjs/DSH_PlainRiceWhale/security/advisories/new>;
3. **Email** (routed through GitHub): <136884860+ZJDqtjs@users.noreply.github.com>.

Please include a statement of ownership, the exact file paths at issue, and the remedy you seek. **Commitment**: on receipt of a plausible notice I will remove the material within **72 hours** — deleting the file, dropping its entry from the sticker list, and releasing a new version — and only then discuss ownership. No proof is required before removal. If a version was distributed through a plugin index, that version will be pulled from the index as well.

These assets are provided **as-is**, are not claimed as original works, carry no sublicensing, and exist only so that this plugin can run.
