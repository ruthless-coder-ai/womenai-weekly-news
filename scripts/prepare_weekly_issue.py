#!/usr/bin/env python3
"""Choose the date range, issue number, and output directory for a weekly run."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


ISSUE_RE = re.compile(r"^vol(?P<vol>\d+)-(?P<start>\d{4})-(?P<end>\d{4})$")


def target_week(today: date) -> tuple[date, date]:
    """Return the latest complete Monday-Sunday range, including today on Sunday."""
    sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    return sunday - timedelta(days=6), sunday


def read_issue_dirs(cards_dir: Path) -> list[tuple[int, str, str, Path]]:
    issues = []
    if not cards_dir.exists():
        return issues
    for child in cards_dir.iterdir():
        if not child.is_dir():
            continue
        match = ISSUE_RE.match(child.name)
        if match:
            issues.append(
                (
                    int(match.group("vol")),
                    match.group("start"),
                    match.group("end"),
                    child,
                )
            )
    return issues


def append_github_output(path: str, values: dict[str, object]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards-dir", required=True)
    parser.add_argument(
        "--week-end",
        help="Override the target Sunday (YYYY-MM-DD); useful for manual backfills",
    )
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    parser.add_argument("--json-out", help="Optional path for a machine-readable state file")
    args = parser.parse_args()

    cards_dir = Path(args.cards_dir).expanduser().resolve()
    if args.week_end:
        sunday = date.fromisoformat(args.week_end)
        if sunday.weekday() != 6:
            raise SystemExit("--week-end must be a Sunday")
        monday = sunday - timedelta(days=6)
    else:
        today = datetime.now(ZoneInfo("Europe/Berlin")).date()
        monday, sunday = target_week(today)

    issues = read_issue_dirs(cards_dir)
    start_key, end_key = monday.strftime("%m%d"), sunday.strftime("%m%d")
    matching = [item for item in issues if item[1:] and item[1] == start_key and item[2] == end_key]
    if len(matching) > 1:
        raise SystemExit(f"Multiple issue folders match {start_key}-{end_key}")

    if matching:
        vol, _, _, issue_dir = matching[0]
        existing = True
    else:
        vol = max((item[0] for item in issues), default=0) + 1
        issue_dir = cards_dir / f"vol{vol:02d}-{start_key}-{end_key}"
        issue_dir.mkdir(parents=True, exist_ok=True)
        existing = False

    values: dict[str, object] = {
        "vol": vol,
        "vol_padded": f"{vol:02d}",
        "week_start": monday.isoformat(),
        "week_end": sunday.isoformat(),
        "date_range": f"{monday:%m.%d} — {sunday:%m.%d}",
        "commit_date_range": f"{monday:%m.%d}-{sunday:%m.%d}",
        "issue_dir": str(issue_dir),
        "issue_rel": issue_dir.relative_to(cards_dir).as_posix(),
        "existing": str(existing).lower(),
    }
    if args.github_output:
        append_github_output(args.github_output, values)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(values, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

