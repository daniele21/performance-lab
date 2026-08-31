#!/usr/bin/env python3
"""Validate the pre-real E2E gate against canonical E2E and operating contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain an object")
    return payload


def main() -> int:
    errors: list[str] = []
    try:
        gate = load(ROOT / ".engineering" / "pre-real-e2e.json")
        e2e = load(ROOT / ".engineering" / "e2e.json")
        commands = load(ROOT / ".engineering" / "commands.json")
    except RuntimeError as exc:
        print("Pre-real E2E contract check")
        print(f"FAIL: {exc}")
        return 1

    journeys = {
        item.get("id"): item
        for item in e2e.get("critical_journeys", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    environments = {
        item.get("id"): item
        for item in e2e.get("execution_environments", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    if gate.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if gate.get("gate_id") != "PRE_REAL_E2E":
        errors.append("gate_id must be PRE_REAL_E2E")
    if gate.get("source_of_truth") != ".engineering/e2e.json":
        errors.append("source_of_truth must be .engineering/e2e.json")
    if gate.get("blocks_real_environment") is not True:
        errors.append("blocks_real_environment must be true")
    if gate.get("real_environment_gate") != "RUNTIME-1":
        errors.append("real_environment_gate must be RUNTIME-1")
    if "RUNTIME-1" not in journeys:
        errors.append("RUNTIME-1 must exist in .engineering/e2e.json")

    required = gate.get("required_journeys")
    expected = {f"J{index}" for index in range(10)}
    if not isinstance(required, list) or set(required) != expected:
        errors.append("required_journeys must contain exactly J0-J9")
    else:
        missing = sorted(set(required) - set(journeys))
        if missing:
            errors.append("required_journeys reference unknown journeys: " + ", ".join(missing))

    layers = gate.get("layers")
    layer_map = {
        item.get("id"): item
        for item in layers or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for layer_id in ("browser-emulated-journeys", "packaged-product-journeys"):
        if layer_id not in layer_map:
            errors.append(f"missing required layer: {layer_id}")

    browser = layer_map.get("browser-emulated-journeys", {})
    packaged = layer_map.get("packaged-product-journeys", {})
    for layer_id, layer in (("browser-emulated-journeys", browser), ("packaged-product-journeys", packaged)):
        environment_ref = layer.get("execution_environment_ref")
        environment = environments.get(environment_ref)
        if environment is None:
            errors.append(f"{layer_id} references unknown execution environment: {environment_ref}")
        elif environment.get("automation") != "automated":
            errors.append(f"{layer_id} must reference an automated execution environment")
        evidence = set(layer.get("required_evidence") or [])
        missing_evidence = {"playwright-json", "final-screenshot", "trace"} - evidence
        if missing_evidence:
            errors.append(f"{layer_id} missing evidence: {', '.join(sorted(missing_evidence))}")

    if isinstance(required, list) and set(browser.get("required_journeys") or []) != set(required):
        errors.append("browser-emulated-journeys must cover every required journey")

    packaged_required = set(packaged.get("required_journeys") or [])
    packaged_ref = packaged.get("execution_environment_ref")
    if "built-artifact" not in set(packaged.get("required_evidence") or []):
        errors.append("packaged-product-journeys must require built-artifact evidence")
    for journey_id in sorted(packaged_required):
        journey = journeys.get(journey_id)
        if journey is None:
            errors.append(f"packaged-product-journeys references unknown journey: {journey_id}")
            continue
        if packaged_ref not in set(journey.get("automated_environment_refs") or []):
            errors.append(
                f"{journey_id} does not declare {packaged_ref} in automated_environment_refs"
            )

    retention = gate.get("evidence_retention_days")
    configured_retention = commands.get("artifact_lifecycle", {}).get("ci_retention_days")
    if retention != configured_retention:
        errors.append("evidence_retention_days must match commands artifact_lifecycle.ci_retention_days")

    command = commands.get("commands", {}).get("pre_real_e2e")
    if not isinstance(command, dict) or command.get("status") != "required":
        errors.append("commands.pre_real_e2e must exist with status=required")

    print("Pre-real E2E contract check")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
