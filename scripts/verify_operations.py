#!/usr/bin/env python3
import json
import sys
from pathlib import Path

commands = json.loads(Path(".engineering/commands.json").read_text())
errors: list[str] = []

if commands.get("contract_version") != "0.7.0":
    errors.append("contract_version must be 0.7.0")

integration = commands.get("development_velocity", {}).get("integration", {})
release = commands.get("development_velocity", {}).get("release", {})
if (
    integration.get("automated_e2e_required_when_affected") is not True
    or integration.get("real_environment_blocking") is not False
    or integration.get("real_environment_deferred_to_release") is not True
):
    errors.append("invalid integration stage policy")
if release.get("required_real_environment_blocking") is not True:
    errors.append("invalid release environment policy")

reporting = commands.get("agent_reporting", {})
required_summary_fields = {
    "stage",
    "source_identity",
    "risks",
    "profile",
    "required_gates",
    "evidence",
    "remaining_gaps",
    "next_action",
}
if (
    reporting.get("schema_version") != 1
    or reporting.get("format") != "summary_with_evidence_references"
    or not required_summary_fields.issubset(set(reporting.get("required_summary_fields", [])))
):
    errors.append("invalid agent_reporting")

for field in (
    "bounded_output",
    "full_report_on_demand",
    "preserve_failed_pending_gates",
    "summary_is_not_evidence_verification",
):
    if reporting.get(field) is not True:
        errors.append(f"agent_reporting.{field} must be true")

print("Project operating contract check")
for error in errors:
    print("FAIL:", error)
print("RESULT:", "FAIL" if errors else "PASS")
sys.exit(bool(errors))
