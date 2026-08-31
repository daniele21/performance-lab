#!/usr/bin/env python3
"""Combine browser-emulated and packaged-product E2E evidence into one readiness verdict."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pre_real_e2e import collect_journey_evidence, load_report, write_json

PACKAGED_REQUIRED = ("J0", "J1", "J8", "J9")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser-manifest", type=Path, required=True)
    parser.add_argument("--packaged-report", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON must contain an object: {path}")
    return payload


def write_summary(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Pre-real E2E readiness",
        "",
        f"Overall: **{manifest['status']}**",
        f"Ready for REAL_ENVIRONMENT: **{'YES' if manifest['ready_for_real_environment'] else 'NO'}**",
        "",
        "## Browser-emulated J0-J9",
        "",
        "| Journey | Status | Screenshot | Trace |",
        "| --- | --- | --- | --- |",
    ]
    for journey, evidence in manifest["browser_layer"]["journeys"].items():
        required = evidence["required_evidence"]
        lines.append(
            f"| {journey} | {evidence['status']} | "
            f"{'PASS' if required['final_screenshot'] else 'FAIL'} | "
            f"{'PASS' if required['trace'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Packaged-product journeys",
            "",
            "| Journey | Status | Screenshot | Trace |",
            "| --- | --- | --- | --- |",
        ]
    )
    for journey, evidence in manifest["packaged_layer"]["journeys"].items():
        required = evidence["required_evidence"]
        lines.append(
            f"| {journey} | {evidence['status']} | "
            f"{'PASS' if required['final_screenshot'] else 'FAIL'} | "
            f"{'PASS' if required['trace'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "The browser-emulated layer covers every declared product journey J0-J9. The packaged layer proves the journeys whose current E2E contract requires representative-virtual assembled-product fidelity. Physical runtime/model/device evidence is still RUNTIME-1 and is not claimed here.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    try:
        browser = load_json(args.browser_manifest.resolve())
        packaged_report = load_report(args.packaged_report.resolve())
    except RuntimeError as exc:
        print(f"pre-real readiness failed: {exc}", file=sys.stderr)
        return 1

    packaged_journeys = collect_journey_evidence(packaged_report, PACKAGED_REQUIRED)
    browser_pass = browser.get("status") == "PASS"
    packaged_pass = all(item["status"] == "PASS" for item in packaged_journeys.values())
    status = "PASS" if browser_pass and packaged_pass else "FAIL"

    manifest = {
        "schema_version": 1,
        "gate_id": "PRE_REAL_E2E",
        "status": status,
        "ready_for_real_environment": status == "PASS",
        "real_environment_gate": "RUNTIME-1",
        "browser_layer": browser,
        "packaged_layer": {
            "layer": "packaged-product-journeys",
            "status": "PASS" if packaged_pass else "FAIL",
            "execution_environment_ref": "packaged-product-fixture",
            "fidelity_class": "representative_virtual",
            "journeys": packaged_journeys,
        },
        "residual_real_environment_gaps": [
            "real external runtime/model identity and effective backend behavior",
            "physical-device memory/resource behavior",
            "telemetry sensor availability and provenance",
            "thermal and repeated-load characteristics",
        ],
    }
    write_json(output_root / "manifest.json", manifest)
    write_summary(output_root / "summary.md", manifest)

    print("Pre-real E2E readiness")
    print(f"browser layer: {'PASS' if browser_pass else 'FAIL'}")
    print(f"packaged layer: {'PASS' if packaged_pass else 'FAIL'}")
    print(f"READY_FOR_REAL_ENVIRONMENT: {'YES' if status == 'PASS' else 'NO'}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
