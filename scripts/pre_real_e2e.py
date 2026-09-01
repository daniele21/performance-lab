#!/usr/bin/env python3
"""Run browser pre-real E2E and retain journey evidence for the declared gate."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "pre-real-e2e"
CONTRACT_PATH = ROOT / ".engineering" / "pre-real-e2e.json"
E2E_PATH = ROOT / ".engineering" / "e2e.json"
JOURNEY_PATTERN = re.compile(r"\bJ([0-9])\b")
PASS_STATUSES = {"expected", "passed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain an object: {path}")
    return payload


def load_gate_contract() -> dict[str, Any]:
    contract = load_json_object(CONTRACT_PATH, "pre-real E2E contract")
    if contract.get("schema_version") != 1 or contract.get("gate_id") != "PRE_REAL_E2E":
        raise RuntimeError(
            "pre-real E2E contract must declare schema_version=1 and gate_id=PRE_REAL_E2E"
        )
    if contract.get("source_of_truth") != ".engineering/e2e.json":
        raise RuntimeError("pre-real E2E contract source_of_truth must be .engineering/e2e.json")
    if contract.get("blocks_real_environment") is not True:
        raise RuntimeError("pre-real E2E contract must block real environment until PASS")
    required = contract.get("required_journeys")
    if (
        not isinstance(required, list)
        or not required
        or not all(isinstance(item, str) for item in required)
    ):
        raise RuntimeError(
            "pre-real E2E contract required_journeys must be a non-empty string list"
        )
    layers = contract.get("layers")
    if not isinstance(layers, list) or not layers:
        raise RuntimeError("pre-real E2E contract layers must be a non-empty list")
    return contract


def contract_layer(contract: dict[str, Any], layer_id: str) -> dict[str, Any]:
    for layer in contract.get("layers", []):
        if isinstance(layer, dict) and layer.get("id") == layer_id:
            return layer
    raise RuntimeError(f"pre-real E2E contract is missing layer: {layer_id}")


def execution_environment(environment_id: str) -> dict[str, Any]:
    e2e = load_json_object(E2E_PATH, "E2E fidelity contract")
    environments = e2e.get("execution_environments")
    if not isinstance(environments, list):
        raise RuntimeError("E2E fidelity contract execution_environments must be a list")
    for environment in environments:
        if isinstance(environment, dict) and environment.get("id") == environment_id:
            return environment
    raise RuntimeError(f"unknown execution environment ref: {environment_id}")


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
    required_tuple = tuple(required)
    journey_specs: dict[str, list[dict[str, Any]]] = {journey: [] for journey in required_tuple}
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
    for journey in required_tuple:
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
    return load_json_object(path, "Playwright JSON report")


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
        f"Fidelity: `{manifest['fidelity_class']}`",
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
            (
                "This layer runs every declared browser journey in an emulated desktop Chromium "
                "context. The Python API/persistence remain mocked, so the overall environment "
                "keeps its canonical host_or_fake fidelity. Packaged-product evidence is a "
                "separate required layer before RUNTIME-1."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        contract = load_gate_contract()
        layer = contract_layer(contract, "browser-emulated-journeys")
        environment_ref = str(layer["execution_environment_ref"])
        environment_contract = execution_environment(environment_ref)
        required = tuple(str(item) for item in layer["required_journeys"])
        viewport = layer.get("viewport")
        if not isinstance(viewport, dict):
            raise RuntimeError("browser-emulated-journeys viewport is required")
    except (KeyError, RuntimeError) as exc:
        print(f"pre-real E2E contract failed: {exc}", file=sys.stderr)
        return 1

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
        ["pnpm", "--dir", "frontend", "run", "test:e2e:pre-real"],
        cwd=ROOT,
        env=environment,
        check=False,
        text=True,
    )

    try:
        report = load_report(report_path)
        journeys = collect_journey_evidence(report, required)
    except RuntimeError as exc:
        print(f"pre-real E2E failed: {exc}", file=sys.stderr)
        return 1

    journey_pass = all(item["status"] == "PASS" for item in journeys.values())
    status = "PASS" if completed.returncode == 0 and journey_pass else "FAIL"
    manifest = {
        "schema_version": 1,
        "gate_id": contract["gate_id"],
        "layer": layer["id"],
        "status": status,
        "source_revision": git_revision(),
        "execution_environment_ref": environment_ref,
        "fidelity_class": environment_contract["fidelity_class"],
        "browser_context": layer["browser_context"],
        "viewport": viewport,
        "playwright_exit_code": completed.returncode,
        "journeys": journeys,
        "ready_for_real_environment": False,
        "next_required_layer": "packaged-product-journeys",
    }
    write_json(output_root / "browser-manifest.json", manifest)
    write_summary(output_root / "browser-summary.md", manifest)

    print("Pre-real browser E2E")
    for journey in required:
        evidence = journeys[journey]
        print(
            f"{journey}: {evidence['status']} "
            f"screenshot={evidence['required_evidence']['final_screenshot']} "
            f"trace={evidence['required_evidence']['trace']}"
        )
    print(f"RESULT: {status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
