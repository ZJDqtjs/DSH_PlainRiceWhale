# -*- coding: utf-8 -*-
"""Write whale-aside/assets/gifs/SOURCES.md from the download metadata."""
import json
import os

BASE = r"D:\code\DSH_PlainRiceWhale\whale-aside\assets\gifs"
META = os.path.join(BASE, "_raw", "meta_dl3.json")

SLOTS = {
    "tsun": ("傲娇：鼓腮 / 扭头 / 哼", "a40694985_004.gif"),
    "sweet": ("甜：比心 / 冒爱心", "a40694985_005.gif"),
    "lazy": ("懒：瘫倒 / 打哈欠", "a40694985_018.gif"),
    "shy": ("害羞：脸红 / 捂脸", "a40694985_019.gif"),
    "panic": ("慌张：震惊 / 乱挥手", "a40694985_014.gif"),
    "hungry": ("想吃米饭：盯着饭 / 干饭", "a40694985_020.gif"),
    "smug": ("得意：翘尾巴 / 得意脸", "a40694985_011.gif"),
}


def main():
    with open(META, "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    by_file = {row["file"]: row for row in rows}

    lines = [
        "# 鲸鱼娘小独白 GIF 素材来源",
        "",
        "这七个 GIF 来自 B 站用户发布的「表情包 / 动图」专栏，已按插件需要裁切、抽帧、"
        "重采样并压到 120KB 以内（宽 160–180px，12–14 帧，60–90ms/帧，循环播放，透明底、调色板 ≤128 色）。",
        "",
        "**版权**：原图版权归各位原始上传者 / 画师所有。此处仅作为主人本地个人使用而随插件打包，"
        "不再分发、不用于商业用途。若原作者要求下架，删掉对应文件即可，插件会回退到纯文字气泡。",
        "",
        "下载日期：2026-10-23（Asia/Shanghai）。",
        "",
        "| 槽位 | 情绪含义 | 文件 | 源专栏 | 原图直链 |",
        "| --- | --- | --- | --- | --- |",
    ]

    for slot, (meaning, src) in SLOTS.items():
        row = by_file.get(src)
        aid = row["aid"] if row else "40694985"
        url = row["url"] if row else ""
        page = "https://www.bilibili.com/read/cv" + aid
        lines.append(
            "| `%s` | %s | `%s.gif` | [cv%s](%s) | [原图](%s) |"
            % (slot, meaning, slot, aid, page, url)
        )

    lines += [
        "",
        "## 处理链",
        "",
        "1. 用 B 站专栏接口取正文里的 `native-image` GIF 直链（`i0.hdslb.com`），带 Referer 下载。",
        "2. 校验 `GIF8` magic 与 `n_frames > 1`，丢弃静态图和下载失败项。",
        "3. `Pillow` 抽帧到 12–14 帧、等比缩到 160–180px、全局调色板量化、末位色留作透明，"
        "`disposal=2` + `optimize=True` 重写，逐个试档位直到 ≤120KB。",
        "4. 每个槽位保证文件互不相同，且情绪语义对得上（见上表「情绪含义」）。",
        "",
        "> 说明：`_raw/` 是下载中间产物（原始大图、候选比对图、抓取脚本），不参与插件打包，"
        "可以随时删除；删掉后只剩七个 `*.gif` 也能正常工作。",
    ]

    out = os.path.join(BASE, "SOURCES.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
