#!/usr/bin/env python3
"""Validate a ChatGPT Routine issue payload and materialize its weekly issue files."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, timedelta
from pathlib import Path

from pydantic import BaseModel

from generate_weekly_issue import GeneratedIssue, validate_issue, write_outputs


START_MARKER = "<!-- WOMENAI_ROUTINE_PAYLOAD_START -->"
END_MARKER = "<!-- WOMENAI_ROUTINE_PAYLOAD_END -->"


class RoutineEnvelope(BaseModel):
    week_end: date
    publish: bool = False
    issue: GeneratedIssue


def parse_issue_event(path: Path) -> RoutineEnvelope:
    event = json.loads(path.read_text(encoding="utf-8"))
    issue = event.get("issue") or {}
    title = str(issue.get("title", ""))
    if not title.startswith("[weekly-news]"):
        raise ValueError("Routine issue title must start with [weekly-news]")
    body = str(issue.get("body", ""))
    if START_MARKER not in body or END_MARKER not in body:
        raise ValueError("Routine issue body is missing payload markers")
    raw = body.split(START_MARKER, 1)[1].split(END_MARKER, 1)[0].strip()
    return RoutineEnvelope.model_validate_json(raw)


def parse_payload(path: Path) -> RoutineEnvelope:
    return RoutineEnvelope.model_validate_json(path.read_text(encoding="utf-8"))


def validate_envelope(envelope: RoutineEnvelope) -> tuple[date, date]:
    if envelope.week_end.weekday() != 6:
        raise ValueError("week_end must be a Sunday")
    week_start = envelope.week_end - timedelta(days=6)
    validate_issue(envelope.issue, week_start, envelope.week_end)
    return week_start, envelope.week_end


def append_github_output(path: str, values: dict[str, object]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def extract(args: argparse.Namespace) -> None:
    envelope = parse_issue_event(Path(args.event))
    week_start, week_end = validate_envelope(envelope)
    Path(args.payload_out).write_text(
        envelope.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    values = {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "publish": str(envelope.publish).lower(),
    }
    github_output = args.github_output or os.environ.get("GITHUB_OUTPUT")
    if github_output:
        append_github_output(github_output, values)
    print(json.dumps(values, ensure_ascii=False, indent=2))


def materialize(args: argparse.Namespace) -> None:
    envelope = parse_payload(Path(args.payload))
    week_start, week_end = validate_envelope(envelope)
    expected_start = date.fromisoformat(args.week_start)
    expected_end = date.fromisoformat(args.week_end)
    if (week_start, week_end) != (expected_start, expected_end):
        raise ValueError("Routine payload week does not match the prepared issue folder")
    write_outputs(
        envelope.issue,
        Path(args.output_dir).resolve(),
        args.vol,
        week_start,
        week_end,
    )
    print(f"Materialized Routine copy for Vol.{args.vol:02d}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    extract_parser = sub.add_parser("extract")
    extract_parser.add_argument("--event", required=True)
    extract_parser.add_argument("--payload-out", required=True)
    extract_parser.add_argument("--github-output")
    extract_parser.set_defaults(func=extract)

    materialize_parser = sub.add_parser("materialize")
    materialize_parser.add_argument("--payload", required=True)
    materialize_parser.add_argument("--output-dir", required=True)
    materialize_parser.add_argument("--vol", required=True, type=int)
    materialize_parser.add_argument("--week-start", required=True)
    materialize_parser.add_argument("--week-end", required=True)
    materialize_parser.set_defaults(func=materialize)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

