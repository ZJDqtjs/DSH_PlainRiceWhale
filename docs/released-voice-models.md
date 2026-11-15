# 别人练好的「大肥鱼 / DS娘」音色，到底有没有公开发出来？

调查时间：2026-10-25。范围：B 站 API、BowlRoll、HuggingFace、ModelScope、GitHub（含 jsDelivr 文件级扫描）、以及各项目的 README/文档。

## 一句话结论

**没有公开发布的 GPT-SoVITS / IndexTTS2「大肥鱼」权重。** 能拿到手的只有三样东西：

1. **一个 UTAU 音源包**（真·配布，可下载，但是唱歌用、且禁止二次配布）；
2. **一段 Edge TTS 参考样例**（社区事实标准音色，参数写死在文档里）；
3. **一堆"教你怎么练"的仓库**（只有流程和脚本，不含模型）。

---

## 一、唯一真正配布的语音资产：UTAU 音源包

| 项 | 值 |
|---|---|
| 名称 | **UTAU Deepseek CVVC+VV v1.1**（歌手名 `DeepseekChan`） |
| 地址 | <https://bowlroll.net/file/360563> |
| 文件 | `DeepseekCVVCVV-Fixed.zip`，5.77 MB（实测 6,047,568 字节） |
| 作者 | アシオ。（<https://space.bilibili.com/1268702830>） |
| 发布 | 2026-10-01，1397 次下载 |
| 来源标注 | `音源: DeepseekTTS 贝壳` |
| 使用条件 | **「侵删。禁止二次配布。」**（README.txt 原文） |

**内容实测**：52 个条目 / 解压后 7,421,679 字节；28 个 WAV 全部是 **单声道 44.1 kHz 16-bit**，时长 0.79–5.37 s，配 `oto.ini`（CVVC 与 VV 两套标签）、`character.yaml`、`DeepseekChan.png` 立绘。

**两个关键限制**：

- 它是 **UTAU 音源（唱歌）**，不是 TTS 模型。想说话得靠 OpenUTAU 调（README 明说「应该不适配 UTAU，请使用 OpenUTAU」）。
- **不能二次配布** → 可以本地当参考音频喂给 GPT-SoVITS 做 zero-shot，但**不能打包进我们的插件**分发。

下载有个坑：BowlRoll 页面上没有任何 `<a href>` 直链。流程是读 `#initialize` 的 `data-csrf_token`，向 `/api/file/<id>/download-check` POST 表单（隐藏字段 `download_key=bowlroll_download_control_mischievous`），返回 JSON 里的 `download-execution/...?one_time_key=...` 才是真下载地址。脚本见 `tools/bowlroll_dl.py`。

## 二、社区事实标准音色：Edge TTS 晓伊 +22Hz

仓库 **`xxnb0/deepseek-chan-fanpack`**（鲸鱼娘可移植人格包）里带了唯一一段"官方口径"的语音样例，它的说明书写得非常明确：

```
原创演示台词，使用 Edge TTS 合成
声音：zh-CN-XiaoyiNeural（晓伊）
音高 +22Hz，语速 +0%，音量 +0%
MP3，24 kHz，单声道，约 9.4 秒
```

示例台词：*「我是鲸鱼娘，大肥鱼也行。难题先让我琢磨，没把握的就查清楚。事情做好，再安心摸鱼。」*

它的 `docs/voice.md` 明确写了立场：**优先复用宿主已有的 TTS，不建议克隆真人**；要原创声线可以走 Qwen3-TTS 的 VoiceDesign→Clone 或阿里云声音设计。也就是说，社区正经做角色包的这批人，自己也没在分发训练好的权重。

**这基本就是"大肥鱼该是什么声音"的公共答案**：晓伊音色 + 抬升音高。

## 三、其他仓库：全是空壳

用 jsDelivr 的 `flat` 接口做了文件级扫描（GitHub API 被限流时这条路仍然可用），逐个检查有没有 `.ckpt/.pth/.onnx/.safetensors/.index/.wav` 等模型与音频文件：

| 仓库 | 文件数 | 模型/音频文件 |
|---|---|---|
| `2167504470/cyber-dafeiyu` | 130 | **0** |
| `Fightingshine/astrbot_plugin_whale_voice` | 50 | **0** |
| `fulan0721/dafish-voice-system` | 11 | **0** |
| `Mentha-Azure/deepseek-chan-qqbot` | 170 | **0**（只有 `tts/GPT-SoVITS语音部署与训练指南.md` + `tts_server.py`，是教程不是模型） |
| `KWELLDO/dafeiyu` | 23 | **0** |

HuggingFace 上搜 `大肥鱼 / dafeiyu / ds娘 / deepseekchan / 鲸鱼娘 / sovits 大肥鱼 / sovits whale / dsc-voice` —— **全部 0 命中**。作为对照，泛搜 `sovits` 是能搜到真模型的（`Kree/so-vits-svc4.0-Tokai-Teio` 110 下载等），说明 API 正常，就是这个角色没人传。

ModelScope 的 `/api/v1/dolphin/models` 对所有查询返回 404，接口已废，不用再试。

B 站那边：`尹紫鹭幻想社` 在 BV1n3Hf6xERq / BV1c7eE6VEMD 声称「自制大肥鱼少女音模型（**数据集已开源**）」，但两期视频简介里**没有任何链接**（只有 CC BY-NC-SA 4.0 的角色设计声明），翻遍也没找到数据集地址。称它"已开源"但未给出入口，属于**待核实**。

## 四、还有一个现实约束：这台机器跑不动

| 项 | 实测 |
|---|---|
| GPU | `nvidia-smi` 直接崩溃（退出码 3221225477），**无可用 NVIDIA GPU** |
| 内存 | 8,553,160,704 字节 ≈ **8 GB** |
| CPU | Intel Core i5-9400F，6 核 6 线程 |

GPT-SoVITS / IndexTTS2 推理都要 ≥8 GB 显存，**本机这条路走不通**。就算有人放出权重，也得走云端或换机器。

## 五、所以给你的方案

按"今天就能用"排序：

### 方案 1（推荐，零模型、已验证可跑）：Edge TTS 晓伊 +22Hz
已经把 `edge-tts 7.3.1` 装进运行时 Python，并实测合成成功：

| 样例 | 音色 | 参数 | 实测 F0 中位 |
|---|---|---|---|
| `xiaoyi_p22.mp3` | zh-CN-XiaoyiNeural | pitch +22Hz | **340.4 Hz** |
| `xiaoyi_p45.mp3` | zh-CN-XiaoyiNeural | pitch +45Hz | **381.0 Hz** |
| `xiaoxiao_p30.mp3` | zh-CN-XiaoxiaoNeural | pitch +30Hz | 280.7 Hz |

冷启动一次 `python -m edge_tts` 子进程到落盘 mp3：**约 2.4 秒**（含 Python 启动）。样例在 `.work/tts_samples/`。

这跟社区标准参数完全一致，等于用别人调好的成品音色，只是不叫"模型"。缺点：要联网（微软端点，本机实测通）。

### 方案 2（想完全离线 / 想要"一模一样那个嗓子"）：拿 UTAU 包当参考音频自己练
- 参考音频现成：`DeepseekCVVCVV-Fixed.zip` 里 28 段干净单声道 44.1k WAV，挑 5–10 s 直接喂 GPT-SoVITS zero-shot。
- 但：**没 GPU 练不动**、且该包**禁止二次配布**（只能自用，不能进插件发布）。

### 方案 3（有显卡/云机器时）：whale-voice 一把梭
`2177302423qqcom-byte/whale-voice` 仍然是最完整的工程：IndexTTS2 情感说话 + RVC 翻唱 + GPT-SoVITS 备选 + `:7864` HTTP 服务，自带 3 个 MIT 授权 RVC 模型。它故意不带音色样本——现在你知道为什么了：社区里压根没有公共音色可带。

## 六、复现记录

- B 站元数据 / 搜索：`/x/web-interface/view`、`/x/web-interface/search/type`（后期限流返回 412）
- BowlRoll：`tools/bowlroll_dl.py`（csrf + download-check + one_time_key）
- 解包与 WAV 属性：`tools/_br8.py`、`_br9.py`、`_br10.py`
- HF/ModelScope/GitHub：`tools/_hf1.py`、`_gh1.py`、`_gh2.py`、`voice_hub_probe.py`
- 仓库文件级扫描：`tools/_jsd1.py`、`_fan2.py`（jsDelivr flat API）
- 音色试听与基频：`tools/_f0.py`（ffmpeg 抽 16k mono + 自相关测 F0）
