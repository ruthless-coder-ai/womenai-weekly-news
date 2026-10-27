#!/usr/bin/env python3
"""Restore a Xiaohongshu session and publish one image post via xhs-mcp."""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


XHS_MCP_VERSION = "0.8.13"


def run_json(command: list[str]) -> dict:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        raise SystemExit(f"Command failed with exit code {result.returncode}: {command[2]}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{command[2]} returned non-JSON output") from exc
    if payload.get("success") is False:
        raise SystemExit(payload.get("message", f"{command[2]} failed"))
    print(payload.get("message") or f"{command[2]} completed")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("issue_dir")
    parser.add_argument("--run-url", default="")
    args = parser.parse_args()

    encoded = os.environ.get("XHS_COOKIES_B64", "")
    if not encoded:
        raise SystemExit("XHS_COOKIES_B64 is not configured")
    cookie_dir = Path.home() / ".xhs-mcp"
    cookie_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    cookie_path = cookie_dir / "cookies.json"
    try:
        cookie_path.write_bytes(base64.b64decode(encoded, validate=True))
    except ValueError as exc:
        raise SystemExit("XHS_COOKIES_B64 is not valid base64") from exc
    cookie_path.chmod(0o600)

    issue_dir = Path(args.issue_dir).resolve()
    payload = json.loads((issue_dir / "news.json").read_text(encoding="utf-8"))
    post = payload["post"]
    images = sorted(issue_dir.glob("*.png"))
    if len(images) != 4:
        raise SystemExit(f"Expected 4 PNGs before publish, found {len(images)}")

    package = f"xhs-mcp@{XHS_MCP_VERSION}"
    run_json(["npx", "--yes", package, "browser"])
    status = run_json(["npx", "--yes", package, "status"])
    status_data = status.get("data", status)
    if not status_data.get("isLoggedIn"):
        raise SystemExit("Xiaohongshu cookies are expired or not logged in")
    run_json(
        [
            "npx",
            "--yes",
            package,
            "publish",
            "--type",
            "image",
            "--title",
            post["title"],
            "--content",
            post["body"],
            "-m",
            ",".join(str(path) for path in images),
            "--tags",
            ",".join(post["tags"]),
        ]
    )
    marker = {
        "published_at": datetime.now(timezone.utc).isoformat(),
        "title": post["title"],
        "image_count": len(images),
        "publisher": package,
        "github_run": args.run_url,
    }
    (issue_dir / ".xhs-published.json").write_text(
        json.dumps(marker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Published {issue_dir.name} to Xiaohongshu with 4 images")


if __name__ == "__main__":
    main()

