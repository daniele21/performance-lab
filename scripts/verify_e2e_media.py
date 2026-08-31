#!/usr/bin/env python3
"""Verify screenshot and video evidence for passing Playwright critical journeys."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def attachment_exists(report_path: Path, attachment: dict) -> bool:
    raw = attachment.get("path")
    if not isinstance(raw, str) or not raw:
        return False
    path = Path(raw)
    candidates = (
        [path]
        if path.is_absolute()
        else [Path.cwd() / path, report_path.parent / path]
    )
    return any(candidate.is_file() for candidate in candidates)


def walk_specs(suite: dict, parents: tuple[str, ...] = ()) -> list[dict]:
    title = suite.get("title")
    next_parents = parents + ((title,) if isinstance(title, str) and title else ())
    specs: list[dict] = []
    for spec in suite.get("specs", []):
        if isinstance(spec, dict):
            spec = dict(spec)
            spec["full_title"] = " ".join(
                (*next_parents, str(spec.get("title") or ""))
            )
            specs.append(spec)
    for child in suite.get("suites", []):
        if isinstance(child, dict):
            specs.extend(walk_specs(child, next_parents))
    return specs


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "usage: verify_e2e_media.py <playwright-report.json> <journey-id>...",
            file=sys.stderr,
        )
        return 2

    report_path = Path(sys.argv[1]).resolve()
    required_journeys = sys.argv[2:]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    specs: list[dict] = []
    for suite in report.get("suites", []):
        if isinstance(suite, dict):
            specs.extend(walk_specs(suite))

    errors: list[str] = []
    for journey in required_journeys:
        candidates = [
            spec
            for spec in specs
            if journey.lower() in str(spec.get("full_title", "")).lower()
        ]
        passed_results: list[dict] = []
        for spec in candidates:
            for test in spec.get("tests", []):
                if not isinstance(test, dict):
                    continue
                for result in test.get("results", []):
                    if isinstance(result, dict) and result.get("status") == "passed":
                        passed_results.append(result)

        if not passed_results:
            errors.append(
                f"{journey}: no passing Playwright result mapped to this "
                "critical journey"
            )
            continue

        attachments = [
            attachment
            for result in passed_results
            for attachment in result.get("attachments", [])
            if isinstance(attachment, dict)
            and attachment_exists(report_path, attachment)
        ]
        has_screenshot = any(
            attachment.get("contentType") == "image/png"
            for attachment in attachments
        )
        has_video = any(
            str(attachment.get("contentType") or "").startswith("video/")
            for attachment in attachments
        )
        if not has_screenshot:
            errors.append(
                f"{journey}: missing screenshot artifact on passing E2E evidence"
            )
        if not has_video:
            errors.append(
                f"{journey}: missing video artifact on passing E2E evidence"
            )

    if errors:
        print("E2E media evidence check: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    joined = ", ".join(required_journeys)
    print(f"E2E media evidence check: PASS ({joined})")
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
