# 本目录音频的许可声明

本目录（`samples/`）下的 MP3 **不受**仓库根目录 [MIT License](../LICENSE) 覆盖。

它们是用 `edge-tts` 调用 Microsoft Edge「大声朗读」的**消费者端点**合成的试听样本，文本由维护者撰写。神经语音模型与语音名称归 Microsoft 所有；本项目不主张任何权利，也不为其商用合规性背书——微软未公开声明允许再分发生成的音频（详见 [PROVENANCE.md](../PROVENANCE.md) 第 6 节）。

- **插件运行不依赖本目录任何文件**，删除后功能完全不变。
- 元数据核查：本目录文件**不含 ID3v2 标签**（无标题 / 艺术家 / 专辑 / 注释帧），仅残留 `LAME` 编码器字符串；可用 `python tools/asset_metadata_audit.py` 复现。
- 权利主张（takedown）：见 PROVENANCE.md 第 7 节，承诺收到有效通知后 72 小时内先下架再沟通。
