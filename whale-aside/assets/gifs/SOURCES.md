# 鲸鱼娘小独白 贴图素材来源

## 当前出货的素材

只有一个文件：`meme2_clean.png`（850×807 PNG，411.9KB），给 `meh` 槽位用。

它是一张 **B 站蓝毛鲸鱼娘梗图**的清洗版：原图左上角画死了一个思考气泡，气泡里印着一句粗话。主人后来把那张图**重截了一遍并画了个红框**，框住的正是那两行字——所以清洗目标很明确：**留空气泡，只删字**。

产出脚本 `tools/meme2_clean.py`，两个输入各司其职：

| 输入 | 用途 |
| --- | --- |
| `.work/meme2_src.png` | 带标注的截图。**只用来量坐标**：顶部 y=42 的查看器工具栏、左右下的蓝色选框、以及红框本身的包围盒 |
| `.work/meme_src.jpg` | 无标注原图 850×807。**实际在它上面动刀** |

为什么不在截图上直接改，两个坑都踩过：

1. 截图被重新压缩过，**气泡描边和人物描边粘成了同一整块**（265439 px），「找最大包围盒认气泡」这类按连通域的规则当场失效；
2. 红线是**压在气泡描边上**画的，抹红线必然毁掉底下那段描边；断口还会变成小块，被「小笔画」规则二次误删，最后气泡右侧被啃出一个洞。

在原图上则干净得多：墨迹掩码（离白 > 28）做 4-连通分解，气泡环是独立的 18227 px 块（x 10..509 / y 34..355），两行字是 28 个独立小块（共 8243 ink px），全部落在红框范围内。删这 28 块、每块外扩 4px 吃掉 JPEG 振铃，气泡环和思考小圈一根毫毛都没动。

成品无透明通道（RGB PNG），因为原图本来就画在白底上。

## 已退役的素材（2026-11-15）

以下都**不在仓库里**，代码也不再引用；`tools/check_sticker_ext.mjs` 会把它们当成孤儿文件报错。

| 素材 | 退役原因 | 想恢复怎么办 |
| --- | --- | --- |
| `tsun/sweet/lazy/shy/panic/hungry/smug` 七张 GIF（128px 宽、120 帧、合计 3324KB） | 旧资源，主人决定下线 | 备份在 `.work/gifs-backup.zip`（不进仓库）；或用 `tools/pet_probe.py` + `tools/build_mood_gifs.py` 重新抓取与合成 |
| `meh.jpg`（256×233 人像裁切） | 被 `meme2_clean.png` 取代，留两份等于留两个真相 | 用 `tools/meme_components.py` 的几何结论重裁；原构建脚本 `tools/build_meme_jpg.py` 已随退役删除 |

七张 GIF 的原素材来自开源桌宠项目 **PC2005-cloud/dsh-pet** 的预览素材库，**MIT License（Copyright (c) 2026 PC2005-cloud）**，署名在此保留。仓库：<https://github.com/PC2005-cloud/dsh-pet>，素材目录 `dsh-pet/assets/preview/<拼音动作名>.gif`。槽位对应关系（`tsun`←`dianji-huiying-aojiao-shengqi-ceshen-zhanshi`、`sweet`←`dianji-huiying-kaixin-yuedong`、`lazy`←`haqian-liantian`、`shy`←`dianji-huiying-haixiu-jingya`、`panic`←`da-keshui-bei-jingxing`、`hungry`←`chi-baifan`、`smug`←`qian-dai-man-yi`）见 `tools/build_mood_gifs.py` 里的 `PICK` 表，那份脚本仍在仓库里作为可复现记录。

`meme2_clean.png` 用的梗图属社区流通素材，只取图像本身、不含任何第三方文案。

## 路由与白名单

`/whale-aside/assets/gifs/<file>` 由 `whale-aside/index.js` 的 `serveAsset` 提供。白名单从 **`MOOD_STICKERS`** 拼出——注意它**不是**从 `MOODS` 推出来的：

```js
const MOOD_STICKERS = { meh: 'gifs/meme2_clean.png' };
```

`MOODS`（8 个情绪）同时喂着 `whale_aside` 的选项枚举和 Edge TTS 的 8 条韵律表，把没贴图的情绪从 `MOODS` 里砍掉会连带废掉语音功能。所以这里解耦成两层：**情绪词表**（工具 + 语音）与 **贴图清单**（素材）。`client.js` 的 `STICKER_ASSETS` 是同一份清单的另一半，没有条目的情绪**直接不渲染 `<img>`**，不发请求、不制造 404。

`content-type` 按扩展名从 `ASSET_MIME` 取（gif/jpg/jpeg/png），`GET/HEAD` 之外返回 405，命中返回 `public, max-age=3600`。因为缓存一小时，素材变动后必须 bump `client.js` 的 `GIF_VERSION`（当前 `'6'`）。

## 工具

| 脚本 | 作用 |
| --- | --- |
| `tools/meme_probe.py` | 梗图静帧的墨迹密度图，用来定位气泡与人物边界 |
| `tools/meme_components.py` | 连通域分解，列出气泡框 / 思考小圈 / 文字笔画 / 人物各自的包围盒与均色 |
| `tools/meme2_clean.py` | **当前素材的构建脚本**：量红框 → 在原图上删文字块 → 直接写进 `whale-aside/assets/gifs/` |
| `tools/meme_verify.py` | 出货素材体检：尺寸、帧数、体积、透明占比、绿幕残留（清单在 `STICKERS`） |
| `tools/check_sticker_ext.mjs` | 三方一致性：Host 的 `MOOD_STICKERS`、Client 的 `STICKER_ASSETS`、磁盘上的实际文件必须完全吻合，孤儿与缺失都报错 |
| `tools/pet_probe.py` / `tools/build_mood_gifs.py` / `tools/verify_gifs.py` / `tools/gif_qa.py` | 已退役 GIF 路线的抓取与合成记录，保留以便复现 |

## 版权与回退

`meme2_clean.png` 不含第三方文字。若贴图被删掉，前端 `<img>` 的 `onError` 会隐藏它，气泡自动回退为纯文字独白，不会破图；而清单里本就没有贴图的情绪根本不会发起请求。
