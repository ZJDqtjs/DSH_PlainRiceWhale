# 鲸鱼娘的嗓子：现在的音色从哪来，想换怎么换

更新时间：2026-11-15。所有结论都在本机实测过（本机 = Windows，DSH Desktop，GUI 端口每次重启会变）。

## 一、发声链路

```
whale_aside 调用 → client.js 气泡
   → POST /whale-aside/voice  {text, mood, [voice], [basePitchHz], [baseRatePct], [enabled]}
        → index.js serveVoice → ensureClip → python -m edge_tts → ~/.dsh/whale-audio/<sha1>.mp3
        → 返回 {url, voice, pitch, rate} → <audio> 播放
   → 失败时（合成失败 / 路由不可达）→ 浏览器 Web Speech API（本机选中 Microsoft Huihui Desktop）
```

缓存 key 是 `sha1(voice|pitch|rate|text)`，所以**换音色或改音高会自动重新合成，不会播旧嗓子**。

## 二、2026-11-15 「听起来不是晓伊」的两个真凶

| 症状 | 根因 | 证据 | 现在的处理 |
|---|---|---|---|
| 所有独白都变成浏览器音（Huihui） | DSH 在 11:07 重新装配了 `dsh-runtimes/dsh-primary-runtime`，把 10/25 手工 `pip install` 进运行时的 `edge_tts` 抹掉了；子进程 0.1 秒退出码 1 | `python -m edge_tts --version` → `No module named edge_tts`；插件只回一句 `edge-tts exited with 1` | 1) 重装进运行时；2) **同时**装进不会被抹掉的 `~/.dsh/whale-tts/lib`，宿主自动把它加进 `PYTHONPATH`；3) 失败原因（含 stderr 尾巴）回给前端并显示在气泡徽章上；4) 引擎连续失败进 30 s 冷却，不再每条独白白试 3 次 |
| 只有害羞 / 慵懒 / 无语是浏览器音 | `--rate -3%` 被 argparse 当成选项，退出码 2（argparse 出错就是 2） | 重装后其余 mood 全部 200，`shy` 仍 500；改成 `--rate=-3%` 后同一条命令 exit 0 | 参数一律走 `--rate=-3%` / `--pitch=+35Hz` 等号形式；自检里 8 个 mood 全过 |

顺带修掉的第三个坑：`~/.dsh/whale-audio/` 里那个 0 字节 mp3。旧代码只判断文件存在，所以那句话永远播静音；现在 0 字节＝未命中，直接删掉重做，GET 到空文件也返回 404。

## 三、想自定义音色，三个层级

### 1）气泡上的选择器（只影响这个浏览器，改完立刻生效）
刷新页面后，每颗气泡标题右边多出一枚小徽章：`Edge·Xiaoyi` / `浏览器系统音` / `合成中…`。**点它**展开面板：

- 音色下拉（11 个中文 Neural 音色）或直接填任意 Babel 名（必须形如 `zh-CN-XiaoyiNeural`，非法名宿主会忽略并回落）
- 音高偏移 Hz（-100～100，留空＝跟随宿主）、语速偏移 %（-40～40）
- 「用 Edge TTS」勾选（取消＝只用浏览器音色）
- 「试听这句」用固定台词立刻试音，不用等下一条独白
- 「全部跟随宿主」清空覆盖

存在 `localStorage['dsh.whale-aside.voice']`，不发请求就能改，每次 `POST` 带上覆盖值。

### 2）全局配置文件 `~/.dsh/whale-voice.json`（影响所有会话）
已经写好一份默认值，直接改数字即可：

```json
{ "voice": "zh-CN-XiaoyiNeural", "basePitchHz": 22, "baseRatePct": 0, "enabled": true,
  "attempts": 3, "prosody": { "tsun": { "pitch": 8, "rate": 3 }, "shy": { "pitch": 13, "rate": -3 }, ... } }
```

按 mtime 热加载：改完**下一次合成就生效，不用重启**。JSON 写坏了不会炸，`GET /whale-aside/voice` 会在 `configProblems` 里告诉你哪一行读失败了。

### 3）代码默认值
`whale-aside/index.js` 的 `DEFAULT_VOICE` / `DEFAULT_BASE_PITCH_HZ` / `DEFAULT_PROSODY`（[L90-L105](../whale-aside/index.js#L90-L105)）只是前两层缺失时的兜底。

## 四、参数范围与试听基准

- Edge TTS 中文可用音色（`python -m edge_tts --list-voices`，全量 318 个）：
  `zh-CN` Xiaoxiao / Xiaoyi / Yunjian / Yunxi / Yunxia / Yunyang / liaoning-Xiaobei / shaanxi-Xiaoni；`zh-TW` HsiaoChen / HsiaoYu / YunJhe；`zh-HK` HiuGaai / HiuMaan / WanLung。
- 社区基准：晓伊 +22 Hz（实测 F0 中位 340 Hz 左右）。本机用自相关复测：晓伊+22 → 325 Hz，+45 → 379 Hz；缓存里各 mood 落在 332–378 Hz，正是「晓伊 + 情绪偏移」。
- 对照样片（同一句话、同 +22 Hz，只换音色）：`samples/audition-*.mp3`，脚本 [tools/make_voice_audition.py](../tools/make_voice_audition.py)。

## 五、自检与排查

| 目的 | 命令 |
|---|---|
| 看宿主认为的当前配置 / 最后一次失败 | `curl http://127.0.0.1:<当前端口>/whale-aside/voice` |
| 覆盖全部逻辑分支（负 rate、配置文件、覆盖、非法名、0 字节、穿越、冷却） | `node tools/voice_selftest.mjs`（15 项，跑在临时 `DSH_HOME` 里，不碰真实目录） |
| 对真实运行中的宿主打一遍 | `python tools/voice_live_check.py` |
| 量化某条 clip 到底是不是那个嗓子 | `python tools/clip_f0.py <mp3…>`（时长 / 浊音帧 / F0 中位数） |
| 引擎又被运行时重装抹掉了 | `"<runtime python>" -m pip install --target "%USERPROFILE%\.dsh\whale-tts\lib" edge-tts` |

浏览器控制台里也有线索：徽章变橙色＝正在用系统音兜底，鼠标悬停就是宿主给的原文错误；`~/.dsh/whale-audio/whale-voice.log` 留着每次子进程的 stderr（超 256 KB 自动截断）。

## 六、还想要「不是 Edge TTS」的嗓子？

Edge TTS 是在线合成，麦克风级克隆做不到那一步。真要自己的声线：拿 `tools/voice_release/DeepseekCVVCVV-Fixed.zip` 里的 28 段 44.1 kHz 单声道 WAV 当参考音频喂 GPT-SoVITS / IndexTTS2（本机无可用 GPU，得云端；该音源禁止二次配布，只能自用）。或者最省事的：把现成音频放进 `whale-aside/assets/voice/`，让 `serveVoice` 优先播本地样本、没有再回落合成——这条路要动代码，说一声我就加。
