#!/usr/bin/env python3
"""Validate the four rendered card files and Xiaohongshu copy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("issue_dir")
    args = parser.parse_args()
    issue_dir = Path(args.issue_dir).resolve()
    payload = json.loads((issue_dir / "news.json").read_text(encoding="utf-8"))
    pngs = sorted(issue_dir.glob("*.png"))
    if len(pngs) != 4:
        raise SystemExit(f"Expected 4 PNGs, found {len(pngs)}")
    for png in pngs:
        with Image.open(png) as image:
            if image.size != (2160, 2880):
                raise SystemExit(f"{png.name}: expected 2160x2880, got {image.size}")
    post = payload.get("post", {})
    if not post.get("title") or not post.get("body") or not post.get("tags"):
        raise SystemExit("news.json is missing complete post copy")
    if not (issue_dir / "xhs-post.txt").is_file():
        raise SystemExit("xhs-post.txt is missing")
    print(f"Validated {issue_dir.name}: 4 PNGs at 2160x2880 and complete post copy")


if __name__ == "__main__":
    main()

