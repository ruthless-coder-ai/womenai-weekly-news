---
name: womenai-weekly-news
description: >-
  Make the WoMen AI Lab 每周 AI 要闻 card set: search the web for last week's
  (Monday–Sunday) three most important AI news stories, write copy in the
  WoMen AI Lab voice, and render 4 小红书-ready PNGs (1 cover + 3 news cards,
  2160×2880) with the locked visual 母版. Use this whenever the user wants the
  weekly AI news cards / 周报 / 要闻卡片 — phrasings like "做这周的 AI 要闻",
  "出 Vol.05", "weekly AI news cards", "总结上周 AI 新闻做成图", or when they
  ask to swap one of the three stories, tweak the copy, or re-render an
  existing issue. Not for cohort member survey cards (use womenai-cohort-cards
  for those).
---

# WoMen AI Lab · 每周 AI 要闻卡片

每期从零跑出「1 封面 + 3 内容卡」：搜上一个完整自然周（周一到周日）的 AI 新闻，
写文案，套固定母版渲染成 4 张 2160×2880 PNG。

文案由你（Claude）来写——这是创意活；版式、配色、字体、页眉页脚、水印全部
锁死在脚本和 CSS 里，每期长得一样，只换字。

## 流程

### 1. 定参数（期号 + 日期范围）

- **日期范围**：最近一个完整的周一到周日。用 python 算，别心算：

  ```bash
  python3 -c "
  from datetime import date, timedelta
  today = date.today()
  # 最近一个已结束（或今天恰好是周日则含今天）的周日
  sun = today - timedelta(days=(today.weekday() + 1) % 7)
  mon = sun - timedelta(days=6)
  print(mon.isoformat(), sun.isoformat(), f'{mon:%m.%d} — {sun:%m.%d}')"
  ```

- **期号 Vol.**：上一期 +1。看输出根目录 `~/Claude working folder/womenai-weekly-news/`
  下已有的 `volNN-*` 文件夹取最大号 +1；一个都没有就问用户这期是 Vol 几。
- 本期输出目录：`~/Claude working folder/womenai-weekly-news/volNN-MMDD-MMDD/`。

### 2. 搜新闻

用 WebSearch 找该周内最重要的 3 条 AI 新闻。选稿标准（务必读
`references/editorial-guide.md` 的「选稿标准」一节）：三条分别覆盖
**钱/成本、人/工作/社会、工具/模型**三个角度，偏普通人有切身感的，
不选融资估值人事，对中文用户相关的加分，必须在本期日期范围内且有信源。

搜的时候按三个角度分别搜（如 "AI pricing news"、"AI jobs regulation news"、
"new AI model launch" + 当周日期），交叉核对报道日期确实落在范围内。

### 3. 写文案

按 `references/editorial-guide.md` 的「语言风格」写（最容易出错，务必读）：
标题带大厂名/产品名；正文客观陈述、不人格化；只有「对 WoMen 为什么重要」
用「我们」口吻；不用引号强调、不用破折号、不用「不是A而是B」；每张一处
`<g>薄荷绿高亮</g>`。

写进 `news.json`（schema 见下）。**只写内容**——页码、页眉、Vol/日期标签、
「对 WoMen 为什么重要」小标题都由脚本自动加。

### 4. 渲染

```bash
python3 "$SKILL_DIR/scripts/build_news_cards.py" <news.json> --out <输出目录>
```

（`$SKILL_DIR` = 这个 skill 的目录）。需要 Python + Playwright（chromium 已装）。
脚本渲染后会自动检查文字溢出并打 ⚠ 警告：**有警告就精简文案重渲染，
别改母版尺寸**。也可先 `--html-only` 预览结构。

### 5. 交付

产出 `01_cover.png / 02_*.png / 03_*.png / 04_*.png` 四张，发小红书时封面在前。
交付时把三条新闻的标题 + 信源 + 日期列给用户过目，方便用户说
「第 X 条换成 XX」或改某句文案——改完只需更新 news.json 重跑步骤 4。

## news.json schema

```json
{
  "vol": 4,
  "date_range": "06.22 — 06.28",
  "output_dir": "/绝对路径/vol04-0622-0628",
  "cards": [
    {
      "type": "cover",
      "name": "cover",
      "title": "本周 AI\n值得知道的<g>三件事</g>",
      "headlines": ["OpenAI 把 o4 价格砍半", "欧盟 AI 法案正式生效", "Google 发布 Gemini 3"]
    },
    {
      "type": "news",
      "name": "openai-price",
      "kicker": "钱 · 门槛",
      "title": "OpenAI 把 o4 API 价格<g>砍半</g>",
      "body": "正文 2–4 句，客观陈述。",
      "body2": "可选的背景补充，暗调。",
      "why": "我们口吻 1–2 句，<g>最关键一句标绿</g>。",
      "source": "TechCrunch · 06.24"
    }
  ]
}
```

- 文案里 `<g>...</g>` = 薄荷绿高亮（唯一的强调方式）；`\n` = 换行。
- `name` 决定输出文件名（如 `02_openai-price.png`）。
- 卡片顺序：cover + 3 张 news，news 顺序与封面 headlines 一致。

## 改版式

配色/间距/字号集中在 `assets/style.css`。字体栈是刻意锁死的
（以前每期字体不一样的根因），不要换。完整规范和常见问题速查见
`references/editorial-guide.md`。
