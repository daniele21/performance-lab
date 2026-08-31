#!/usr/bin/env python3
"""Combine browser-emulated and packaged-product E2E evidence into one readiness verdict."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pre_real_e2e import (
    collect_journey_evidence,
    contract_layer,
    execution_environment,
    load_gate_contract,
    load_report,
    write_json,
)


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
        "## Browser-emulated journeys",
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
            "This gate proves the declared automated pre-real layers only. Physical runtime/model/device evidence remains RUNTIME-1 and is never inferred from browser or packaged fixtures.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    try:
        contract = load_gate_contract()
        packaged_layer = contract_layer(contract, "packaged-product-journeys")
        environment_ref = str(packaged_layer["execution_environment_ref"])
        environment_contract = execution_environment(environment_ref)
        packaged_required = tuple(str(item) for item in packaged_layer["required_journeys"])
        browser = load_json(args.browser_manifest.resolve())
        packaged_report = load_report(args.packaged_report.resolve())
    except (KeyError, RuntimeError) as exc:
        print(f"pre-real readiness failed: {exc}", file=sys.stderr)
        return 1

    packaged_journeys = collect_journey_evidence(packaged_report, packaged_required)
    browser_pass = browser.get("status") == "PASS"
    packaged_pass = all(item["status"] == "PASS" for item in packaged_journeys.values())
    status = "PASS" if browser_pass and packaged_pass else "FAIL"

    manifest = {
        "schema_version": 1,
        "gate_id": contract["gate_id"],
        "status": status,
        "ready_for_real_environment": status == "PASS",
        "real_environment_gate": contract["real_environment_gate"],
        "browser_layer": browser,
        "packaged_layer": {
            "layer": packaged_layer["id"],
            "status": "PASS" if packaged_pass else "FAIL",
            "execution_environment_ref": environment_ref,
            "fidelity_class": environment_contract["fidelity_class"],
            "journeys": packaged_journeys,
        },
        "residual_real_environment_gaps": environment_contract.get("known_gaps", []),
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
