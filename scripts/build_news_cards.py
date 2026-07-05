#!/usr/bin/env python3
"""
Build WoMen AI Lab 每周 AI 要闻 cards (1 cover + 3 news cards) from a content JSON.

Usage:
    python3 build_news_cards.py <news.json> [--out <dir>] [--html-only]

The JSON carries *content only*; the visual system (母版) lives in assets/style.css
and is locked — every issue looks the same, only the words change.
Page numbers, brand header, Vol/date label, the fixed 「对 WoMen 为什么重要」
section title and the corner watermark are injected automatically.

Content string conventions (apply to every text field):
    <g>...</g>   -> mint-green highlight (this is how we emphasise, NOT quotes)
    \n           -> line break

After rendering, the script checks every card for text overflow (文字溢出/压页脚)
and prints a warning per card. Fix by shortening copy, never by resizing the 母版.
"""
import argparse
import html as html_lib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
CSS_PATH = os.path.join(SKILL_DIR, "assets", "style.css")

WHY_TITLE = "对 WoMen 为什么重要"


def fmt(text):
    """Escape HTML, then re-enable our two markup conventions: <g> and \\n."""
    if text is None:
        return ""
    esc = html_lib.escape(str(text))
    esc = esc.replace("&lt;g&gt;", '<span class="g">').replace("&lt;/g&gt;", "</span>")
    esc = esc.replace("\n", "<br>")
    return esc


def header(vol, date_range):
    right = (
        f'每周 AI 要闻 · Vol.{int(vol):02d} · '
        f'<span class="date">{fmt(date_range)}</span>'
    )
    return (
        '<div class="top-bar"></div>'
        '<div class="header">'
        '<div class="brand">WoMen <span class="ai">AI</span> Lab</div>'
        f'<div class="header-right">{right}</div>'
        '</div>'
        '<div class="divider"></div>'
    )


def footer(page, total):
    return (
        '<div class="footer">'
        '<div class="footer-left"><span class="dot"></span> WoMen AI Lab</div>'
        f'<div class="footer-right">{page:02d} / {total:02d}</div>'
        '</div>'
    )


def watermark():
    # Brand watermark is always "AI" — keep the corner mark consistent on every card.
    return '<div class="wm">AI</div>'


def render_cover(c, vol, date_range, page, total):
    headlines = "".join(
        '<div class="hl-item">'
        f'<div class="hl-num">{i:02d}</div>'
        f'<div class="hl-text">{fmt(h)}</div>'
        '</div>'
        for i, h in enumerate(c.get("headlines", []), start=1)
    )
    swipe = c.get("swipe", "→ 滑动看本周三条")
    return (
        '<div class="card">'
        + header(vol, date_range)
        + '<div class="body cover-body">'
        + f'<div class="tag">{fmt(c.get("tag", "— 每周 AI 要闻 —"))}</div>'
        + f'<div class="cover-vol">Vol.<span class="g">{int(vol):02d}</span> · {fmt(date_range)}</div>'
        + f'<div class="cover-title">{fmt(c.get("title", ""))}</div>'
        + (f'<div class="headlines">{headlines}</div>' if headlines else "")
        + (f'<div class="swipe">{fmt(swipe)}</div>' if swipe else "")
        + '</div>'
        + footer(page, total)
        + watermark()
        + '</div>'
    )


def render_news(c, vol, date_range, page, total):
    parts = [
        '<div class="card">',
        header(vol, date_range),
        '<div class="body">',
        '<div class="kicker">'
        f'<div class="k-num">{page - 1:02d}</div>'
        f'<div class="k-label">{fmt(c.get("kicker", ""))}</div>'
        '</div>',
        f'<div class="news-title">{fmt(c.get("title", ""))}</div>',
    ]
    if c.get("body"):
        parts.append(f'<div class="news-body">{fmt(c["body"])}</div>')
    if c.get("body2"):
        parts.append(f'<div class="news-body-2">{fmt(c["body2"])}</div>')
    parts.append('<div class="short-line"></div>')
    parts.append(f'<div class="why-title">{WHY_TITLE}</div>')
    parts.append(f'<div class="why-body">{fmt(c.get("why", ""))}</div>')
    if c.get("source"):
        parts.append(f'<div class="source">信源：{fmt(c["source"])}</div>')
    parts += ['</div>', footer(page, total), watermark(), '</div>']
    return "".join(parts)


RENDERERS = {"cover": render_cover, "news": render_news}


def build_html(data):
    with open(CSS_PATH, encoding="utf-8") as f:
        css = f.read()
    vol = data["vol"]
    date_range = data["date_range"]
    cards = data["cards"]
    total = len(cards)
    blocks = []
    for i, c in enumerate(cards, start=1):
        ctype = c.get("type", "news")
        if ctype not in RENDERERS:
            raise SystemExit(f"Unknown card type '{ctype}' on card {i}")
        blocks.append(RENDERERS[ctype](c, vol, date_range, i, total))
    body = "\n".join(blocks)
    return (
        "<!DOCTYPE html><html lang='zh'><head><meta charset='UTF-8'>"
        f"<style>{css}</style></head><body>{body}</body></html>"
    )


def slugify(card, idx):
    base = card.get("name") or card.get("type") or "card"
    base = re.sub(r"[^0-9a-zA-Z_-]+", "-", str(base)).strip("-").lower() or "card"
    return f"{idx:02d}_{base}"


def render_pngs(html, cards, out_dir):
    from playwright.sync_api import sync_playwright

    html_path = os.path.join(out_dir, "_cards.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    saved, warnings = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=2,
                                viewport={"width": 1160, "height": 1520})
        page.goto("file://" + html_path)
        page.wait_for_timeout(600)
        overflow = page.evaluate(
            """() => Array.from(document.querySelectorAll('.card')).map(card => {
                const b = card.querySelector('.body');
                return b ? Math.max(0, b.scrollHeight - b.clientHeight) : 0;
            })"""
        )
        els = page.query_selector_all(".card")
        for idx, (el, card) in enumerate(zip(els, cards), start=1):
            fname = slugify(card, idx) + ".png"
            el.screenshot(path=os.path.join(out_dir, fname))
            saved.append(fname)
            if overflow[idx - 1] > 0:
                warnings.append(
                    f"  ⚠ card {idx} ({fname}) overflows by ~{overflow[idx - 1]}px — "
                    "精简文案后重渲染，别改母版尺寸"
                )
        browser.close()
    return saved, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json", help="path to news.json")
    ap.add_argument("--out", help="output dir (default: output_dir from JSON, else ./out)")
    ap.add_argument("--html-only", action="store_true", help="write HTML, skip PNG render")
    args = ap.parse_args()

    with open(args.json, encoding="utf-8") as f:
        data = json.load(f)

    out_dir = args.out or data.get("output_dir") or os.path.join(os.getcwd(), "out")
    out_dir = os.path.abspath(os.path.expanduser(out_dir))
    os.makedirs(out_dir, exist_ok=True)

    html = build_html(data)
    with open(os.path.join(out_dir, "_cards.html"), "w", encoding="utf-8") as f:
        f.write(html)

    if args.html_only:
        print(f"HTML written to {out_dir}/_cards.html ({len(data['cards'])} cards)")
        return

    saved, warnings = render_pngs(html, data["cards"], out_dir)
    print(f"Rendered {len(saved)} cards (2160x2880) to {out_dir}:")
    for s in saved:
        print("  " + s)
    if warnings:
        print("Overflow warnings:")
        for w in warnings:
            print(w)


if __name__ == "__main__":
    main()
