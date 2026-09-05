#!/usr/bin/env python3
"""Verify integration and release environment-gate semantics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def expect(section: dict, key: str, value: object, errors: list[str], prefix: str) -> None:
    if section.get(key) != value:
        errors.append(f"{prefix}.{key} must be {value!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-mode", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    try:
        commands = json.loads((root / ".engineering/commands.json").read_text())
        e2e = json.loads((root / ".engineering/e2e.json").read_text())
    except Exception as exc:
        print(f"FAIL: invalid engineering JSON: {exc}")
        return 1

    velocity = commands.get("development_velocity", {})
    integration = velocity.get("integration", {})
    release = velocity.get("release", {})
    expect(
        integration,
        "automated_e2e_required_when_affected",
        True,
        errors,
        "development_velocity.integration",
    )
    expect(
        integration,
        "real_environment_blocking",
        False,
        errors,
        "development_velocity.integration",
    )
    expect(
        integration,
        "real_environment_deferred_to_release",
        True,
        errors,
        "development_velocity.integration",
    )
    expect(
        release,
        "required_real_environment_blocking",
        True,
        errors,
        "development_velocity.release",
    )

    policy = e2e.get("stage_policy", {})
    integration = policy.get("integration", {})
    release = policy.get("release", {})
    expect(
        integration,
        "automated_e2e_before_shared_integration",
        True,
        errors,
        "stage_policy.integration",
    )
    expect(
        integration,
        "real_environment_blocking",
        False,
        errors,
        "stage_policy.integration",
    )
    expect(
        integration,
        "real_environment_deferred_to_release",
        True,
        errors,
        "stage_policy.integration",
    )
    expect(
        integration,
        "material_ui_journey_minimum_evidence_mode",
        "full_media",
        errors,
        "stage_policy.integration",
    )
    expect(
        integration,
        "incidental_ui_may_use_assertions",
        True,
        errors,
        "stage_policy.integration",
    )
    expect(
        release,
        "full_validation_required",
        True,
        errors,
        "stage_policy.release",
    )
    expect(
        release,
        "release_critical_e2e_required",
        True,
        errors,
        "stage_policy.release",
    )
    expect(
        release,
        "required_real_environment_blocking",
        True,
        errors,
        "stage_policy.release",
    )

    print("Stage environment policy check")
    for error in errors:
        print("FAIL:", error)
    print("RESULT:", "FAIL" if errors else "PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
