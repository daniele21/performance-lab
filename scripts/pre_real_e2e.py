#!/usr/bin/env python3
"""Run browser pre-real E2E and retain journey evidence for J0-J9."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "pre-real-e2e"
REQUIRED_JOURNEYS = tuple(f"J{index}" for index in range(10))
JOURNEY_PATTERN = re.compile(r"\bJ([0-9])\b")
PASS_STATUSES = {"expected", "passed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def _walk_specs(suites: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for suite in suites:
        for spec in suite.get("specs", []):
            if isinstance(spec, dict):
                yield spec
        nested = suite.get("suites", [])
        if isinstance(nested, list):
            yield from _walk_specs(item for item in nested if isinstance(item, dict))


def _test_passed(test: dict[str, Any]) -> bool:
    status = test.get("status")
    if status in PASS_STATUSES:
        return True
    results = test.get("results")
    if not isinstance(results, list) or not results:
        return False
    return all(isinstance(result, dict) and result.get("status") == "passed" for result in results)


def _attachments(test: dict[str, Any]) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    results = test.get("results")
    if not isinstance(results, list):
        return collected
    for result in results:
        if not isinstance(result, dict):
            continue
        attachments = result.get("attachments")
        if isinstance(attachments, list):
            collected.extend(item for item in attachments if isinstance(item, dict))
    return collected


def _has_screenshot(attachments: list[dict[str, Any]]) -> bool:
    return any(
        attachment.get("contentType") == "image/png"
        or str(attachment.get("name", "")).lower().startswith("screenshot")
        for attachment in attachments
    )


def _has_trace(attachments: list[dict[str, Any]]) -> bool:
    return any(str(attachment.get("name", "")).lower() == "trace" for attachment in attachments)


def collect_journey_evidence(report: dict[str, Any], required: Iterable[str]) -> dict[str, Any]:
    journey_specs: dict[str, list[dict[str, Any]]] = {journey: [] for journey in required}
    suites = report.get("suites")
    if not isinstance(suites, list):
        suites = []

    for spec in _walk_specs(item for item in suites if isinstance(item, dict)):
        title = str(spec.get("title", ""))
        journeys = {f"J{match}" for match in JOURNEY_PATTERN.findall(title)}
        if not journeys:
            continue
        tests = [item for item in spec.get("tests", []) if isinstance(item, dict)]
        spec_passed = bool(tests) and all(_test_passed(test) for test in tests)
        attachments = [attachment for test in tests for attachment in _attachments(test)]
        evidence = {
            "title": title,
            "passed": spec_passed,
            "screenshot": _has_screenshot(attachments),
            "trace": _has_trace(attachments),
            "attachments": [
                {
                    "name": attachment.get("name"),
                    "content_type": attachment.get("contentType"),
                    "path": attachment.get("path"),
                }
                for attachment in attachments
            ],
        }
        for journey in journeys:
            if journey in journey_specs:
                journey_specs[journey].append(evidence)

    result: dict[str, Any] = {}
    for journey in required:
        specs = journey_specs[journey]
        passed = bool(specs) and all(spec["passed"] for spec in specs)
        screenshot = bool(specs) and all(spec["screenshot"] for spec in specs)
        trace = bool(specs) and all(spec["trace"] for spec in specs)
        result[journey] = {
            "status": "PASS" if passed and screenshot and trace else "FAIL",
            "test_count": len(specs),
            "tests": specs,
            "required_evidence": {
                "final_screenshot": screenshot,
                "trace": trace,
            },
        }
    return result


def load_report(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid Playwright JSON report {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Playwright JSON report must be an object: {path}")
    return payload


def git_revision() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Pre-real browser E2E evidence",
        "",
        f"Status: **{manifest['status']}**",
        f"Environment: `{manifest['execution_environment_ref']}`",
        f"Browser context: `{manifest['browser_context']}`",
        "",
        "| Journey | Status | Screenshot | Trace |",
        "| --- | --- | --- | --- |",
    ]
    for journey, evidence in manifest["journeys"].items():
        required = evidence["required_evidence"]
        lines.append(
            f"| {journey} | {evidence['status']} | "
            f"{'PASS' if required['final_screenshot'] else 'FAIL'} | "
            f"{'PASS' if required['trace'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "This layer proves the complete browser journeys in an emulated desktop Chromium context. ",
            "The Performance Lab Python API/persistence are still mocked here; packaged-product evidence is a separate required layer before RUNTIME-1.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)
    artifacts = output_root / "artifacts"
    report_path = output_root / "playwright-report.json"

    environment = os.environ.copy()
    environment["PERFORMANCE_LAB_PRE_REAL_OUTPUT_DIR"] = str(artifacts)
    environment["PERFORMANCE_LAB_PRE_REAL_REPORT"] = str(report_path)

    completed = subprocess.run(
        ["npm", "--prefix", "frontend", "run", "test:e2e:pre-real"],
        cwd=ROOT,
        env=environment,
        check=False,
        text=True,
    )

    try:
        report = load_report(report_path)
        journeys = collect_journey_evidence(report, REQUIRED_JOURNEYS)
    except RuntimeError as exc:
        print(f"pre-real E2E failed: {exc}", file=sys.stderr)
        return 1

    journey_pass = all(item["status"] == "PASS" for item in journeys.values())
    status = "PASS" if completed.returncode == 0 and journey_pass else "FAIL"
    manifest = {
        "schema_version": 1,
        "gate_id": "PRE_REAL_E2E",
        "layer": "browser-emulated-journeys",
        "status": status,
        "source_revision": git_revision(),
        "execution_environment_ref": "browser-built-mocked-api",
        "fidelity_class": "host_or_fake",
        "browser_context": "desktop-standard-emulated",
        "viewport": {"width": 1280, "height": 900},
        "playwright_exit_code": completed.returncode,
        "journeys": journeys,
        "ready_for_real_environment": False,
        "next_required_layer": "packaged-product-journeys",
    }
    write_json(output_root / "browser-manifest.json", manifest)
    write_summary(output_root / "browser-summary.md", manifest)

    print("Pre-real browser E2E")
    for journey in REQUIRED_JOURNEYS:
        evidence = journeys[journey]
        print(
            f"{journey}: {evidence['status']} "
            f"screenshot={evidence['required_evidence']['final_screenshot']} "
            f"trace={evidence['required_evidence']['trace']}"
        )
    print(f"RESULT: {status}")
    if status != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
