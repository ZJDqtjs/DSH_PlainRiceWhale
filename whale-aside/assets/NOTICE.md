# 本目录素材的许可声明

本目录（`whale-aside/assets/`）下的美术素材**不受**仓库根目录 [MIT License](https://github.com/ZJDqtjs/DSH_PlainRiceWhale/blob/main/LICENSE) 覆盖。

它们由维护者提供或使用 AI 工具生成，按「原样（as-is）」随插件分发，**仅供运行本插件使用**：不授予再许可、不授予二次分发到其它项目的权利，也不声明为本项目原创作品。

> `LICENSE` 与 `PROVENANCE.md` 位于仓库根目录，**不在 npm 压缩包里**，因此本文件把关键条款与联系方式就地写全，装了包即可依。

- 逐项来源、加工方式与元数据核查：[PROVENANCE.md](https://github.com/ZJDqtjs/DSH_PlainRiceWhale/blob/main/PROVENANCE.md)
- 已退役动图素材的 MIT 署名记录：[gifs/SOURCES.md](gifs/SOURCES.md)（随本包分发）

## 权利主张（takedown）

若您是本目录任一素材的权利人（含形象著作权人、配音演员、声音模型权利人），请通过以下**任一**渠道联系，附上权属说明、被指认的具体文件路径、以及您希望的处置方式：

1. **GitHub 官方 DMCA 流程**：<https://github.com/dmca/forms/dmca-takedown-notice>
2. **仓库安全通告**：<https://github.com/ZJDqtjs/DSH_PlainRiceWhale/security/advisories/new>
3. **邮件**（经 GitHub 路由至维护者）：<136884860+ZJDqtjs@users.noreply.github.com>

**承诺**：收到有效通知后 **72 小时内先下架再沟通**——删除文件、从贴图清单移除条目、发布新版本，并从插件索引中撤销该版本。无需先证明侵权成立才动手。

## 移除不会影响插件

情绪贴图清单（`index.js` 的 `MOOD_STICKERS` 与 `client.js` 的 `STICKER_ASSETS`）与情绪词表是解耦的。删掉本目录任一素材，只需同时删掉对应条目：没有贴图的情绪**不渲染 `<img>`、不发起请求**，气泡自动退化为纯文字独白，因此不会出现 404 闪烁，插件其余功能（人设、工具、语音）完全不受影响。
