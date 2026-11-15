# 视频 BV1NtJB6TE19 的 DeepSeek 音源调查

> 结论先说：**这支视频自己没有标注配音来源**，简介、标签、置顶/热评、UP 动态都没有 credits。
> 但它的声音特征，加上「蓝色大肥鱼 / DS娘」这个圈子实际在用的方案，可以大概率定位到
> **DeepSeek 官方朗读音色（4 种内置音色）被采样 / 或在这基础上训练的音色模型**，
> 而不是某个第三方商用 TTS。下面把证据和可复刻路径写清楚。

## 1. 视频本身（B站 API 实测）

| 字段 | 值 |
|---|---|
| 标题 | 带我出逃吧，我的罗密欧~【bilibilionly同人扶持计划】 |
| UP | 彼岸花Channel（mid 13787349，4825 粉） |
| aid / cid | 117457020783315 / 42826662862 |
| 时长 | 257 秒 |
| 发布时间 | 2026-10-18 02:20 |
| 简介 | 只有剧情文案 + 「@我bilibilionly投了」，**无配音 / 音源标注** |
| 标签 | 罗密欧与朱丽叶、治愈、**DS娘**、**deepseek拟人**、claude娘、grok娘、AI娘、bilibilionly同人扶持计划 |
| 字幕 | 无（`subtitle.list` 为空） |
| 置顶评论 | 无（`upper.top` 为空） |
| 热评 | 3 条，均与配音无关（「视频最后的grok」「为何能像人…」） |

也就是说：**官方层面查不到 engine 归属**，只能从圈子惯例 + 音频特征推断。

## 2. 音频客观特征（从视频音轨抽取分析）

抽 16kHz 单声道后做了三件事：

| 指标 | 结果 | 含义 |
|---|---|---|
| 10 秒窗 RMS | 0.080–0.278，持续有能量 | 歌唱/对白贯穿，基本无长静音 |
| 静音间隙 | 94 段，中位 **20ms**，≥300ms 的只有 11 段 | 句间几乎无换气停顿 —— **典型 TTS 逐句拼接后贴 BGM**，真人录音会留下明显呼吸/换气空隙 |
| 浊音基频 F0 | 中位 **302 Hz**，p10 79 / p90 400 Hz | 女声，音高偏高，且低端有 79Hz 的异常点 —— 提示存在**转换/重采样痕迹**（RVC/SoVITS 类变声常见） |
| 帧间音高抖动 | 3.62 半音/帧 | 抖动偏大，不像纯端到端 TTS 那么平，更像**「TTS 出干声 + 变声/克隆」两段式** |

结论：**不是真人配音，是 TTS 管线产物**；而且大概率是「先用某个音色合成，再做音色转换/克隆」，这与 B 站大肥鱼圈的主流做法完全吻合（下面第 4 节）。

## 3. 圈子里的三种真实来源

按可查证据排序：

### A. DeepSeek 网页版自带朗读（最可能的「母带」）
- B 站有教程视频专门讲这件事：**「DeepSeek 网页版朗读功能上线！4种音色 + 音频导出教程」BV1u7ng6PEvx**（UP 十一君Jun），说明官方朗读是**4 种内置音色**，并能导出音频。
- 圈内把这段音频当音源二次使用：
  - **BV1BKYm6JEHf**「deepseek 大肥鱼有声带了！四种音色！两男两女！」——评论直接说「第2个女声好听」「豆姐别夹着嗓子了」，对应官方那 4 个音色；
  - **BV1ZGeG6HENH**「[UTAU 音源配布] Deepseek 想听你说月色真美！」——简介写明 `音源: DeepseekTTS-贝壳`，配布地址 bowlroll.net/file/360563，即**把官方 TTS 拆成 UTAU 音源**；
  - **BV1DvHP6nEJk**「关于Deepseek确实可以通过语音朗读来唱歌」——直接演示朗读引擎唱歌。
- 所以「DeepSeek 的音源」严格说不是某个开源模型，而是 **DeepSeek 自家网页端朗读引擎的 4 个内置音色**。

### B. 本地克隆：GPT-SoVITS / IndexTTS2 / RVC（想要「同一个嗓子」就得走这条）
- **whale-voice**（GitHub `2177302423qqcom-byte/whale-voice`，B站 BV1J2nA6cE9y 介绍）把整条链路打包好了：
  - 情感说话：**IndexTTS2**（10 种预设情绪，2–5s/句，离线）
  - 唱歌翻唱：**RVC**（音色转换，3–8 分钟/首）
  - 音色克隆（备选）：**GPT-SoVITS**
  - 自带 3 个 MIT 授权的 RVC 模型 + FAISS 索引 + 本地 HTTP 服务（:7864），实测 RTX 4060 Laptop 8GB 可跑
  - **重点：仓库不带任何音色样本，音色要自己录/自己截**，这正是「想要 DS娘 那个嗓子」的正确姿势
- 也有现成的 DSH 插件路线：**BV1Cenc6hEtR**「DSH-GPT-SoVITS 配音插件」，能从番剧/视频里抽训练集再一键训练。
- **BV1PPnr65EtU**「自从大肥鱼能发语音后，天天背台词」用的是 **IndexTTS 2.5** + 工作流决定情绪。

### C. 纯系统 TTS / 其他模型（效果差一档）
- 手机端桌宠用本地系统 TTS（BV18Dnb6WEk9）；也有接 Fish-Speech、ChatTTS 之类，但音色和「DS娘」不一致。

## 4. 为什么说这支视频大概是「官方音色 + 转换」

1. 音高 302Hz 中位、抖动大、有 79Hz 异常低点 —— 端到端 TTS 不会这样，**变声/克隆**才会。
2. 句间 20ms 停顿 —— TTS 逐句生成后拼接。
3. UP 彼岸花Channel 与 镜花Mirror 共同开发 deepseekchan.com（DS娘 抽卡/表情站），是这条 AI 娘内容线的主力，**用官方音色 + 本地克隆是圈内标准流程**。
4. 该视频标签明确是「DS娘 / deepseek拟人」，不是真·DeepSeek 官方账号（官方账号 `DeepSeek鲸鱼娘在运营` 在简介里也声明「非官方」）。

**诚实结论：无法从视频本身 100% 证明是哪个 engine。** 能证明的是：它是 TTS 管线（不是真人），且圈子里的「DeepSeek 音源」= 官方网页朗读的 4 个音色，二次创作时再用 SoVITS/IndexTTS/RVC 复刻。

## 5. 给你的 TTS 用上（落地路径）

你的插件现在是「方案 A：浏览器 `speechSynthesis`」，音色取决于系统。要贴 DS娘 的嗓子，按投入从低到高：

### 路线 1：官方音色采样（最快，1 天）
1. 用 DeepSeek 网页版朗读导出 4 段干净音频（BV1u7ng6PEvx 教的导出法）。
2. 选最像的那条，切成 5–15 秒参考音频。
3. 交给 GPT-SoVITS 或 IndexTTS2 做 zero-shot 克隆，得到可本地推理的模型。
4. 插件侧：Host 加 `/whale-aside/voice` 合成接口 + 客户端 `<audio>` 播放（上一轮方案 B 已经写好草图）。

### 路线 2：whale-voice 一把梭（推荐，有 GPU 最快）
- clone `2177302423qqcom-byte/whale-voice` → 按它的 README 起 `tts_daemon.py --port 7864`。
- 录/截 5–10 分钟目标音色，跑它的训练脚本得到 RVC 模型。
- DSH 插件里把 `/whale-aside/voice` 转发到 `http://127.0.0.1:7864`，客户端只换播放器。
- 优点：情感 10 档、能唱歌、全离线；代价：8GB 显存起步。

### 路线 3：edge-tts（无 GPU 的折中）
- 本机实测可直接访问微软 TTS 端点，**zh-CN 有 8 个音色**：`zh-CN-XiaoxiaoNeural`（Warm）、`zh-CN-XiaoyiNeural`（Lively）等。
- 插件 Host 用 subprocess 调 edge-tts 生成 mp3 → 同源路由给客户端播。音色比系统朗读好，但不是 DS娘。

### 路线 4：保持现在的 Web Speech（零成本）
- 只要在设置页挑中文女声 + 调 rate/pitch 就行；你现在这套已经是这个方案。

### 关于「合成模型怎么给插件」
- 模型文件**不进 `exports`**，只进 `files`（发布时）或用 Config 指向外部绝对目录；Host 用 Node `fs` 读，客户端只拿 URL。
- 建议 `Config` 加：`voice.mode`（browser/edge/local）、`voice.modelDir`、`voice.refAudio`、`voice.timeoutMs`、`voice.cacheDir`。
- 播放侧沿用现有约定：单例 `<audio>`、按 `callId` 去重、只在 settled 转变时播一次、静音开关持久化。

## 6. 复现与验证记录

- 视频元数据：`/x/web-interface/view?bvid=BV1NtJB6TE19`（aid/cid/desc/tags 均实测）
- 弹幕 / 置顶评论：`/x/v2/reply`、`/x/v2/dm/*` —— 无配音相关文本
- UP 动态 12 条 + 三期视频简介 —— 无配音 credits
- 音频：`ffmpeg` 抽 16kHz 单声道，分析 RMS / 静音间隙 / 自相关基频（`tools/voice_audio_probe.py`、`tools/voice_pitch.py`）
- edge-tts 端点连通性 + 中文音色清单：`speech.platform.bing.com/.../voices/list` 实测 200，zh-CN 8 个
- 相关仓库：`RVC-Boss/GPT-SoVITS`、`index-tts/index-tts`（IndexTTS 2.5）、`2177302423qqcom-byte/whale-voice` 均确认存在

> 调查脚本留在 `tools/`：`bili_voice_probe*.py`、`bili_voice_page.py`、`voice_audio_probe.py`、`voice_pitch.py`、`dsvoice_facts.py`、`voice_last_probe.py`。
