#!/usr/bin/env python3
"""Validate Performance Lab's repo-template-sw 0.9.x operating contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COMMANDS = (
    "setup",
    "doctor",
    "dev",
    "check",
    "test",
    "e2e",
    "build",
    "smoke",
    "package",
    "stop",
    "clean",
)
STATUSES = {"required", "recommended", "optional", "n/a"}
PROFILES = {"lean", "scoped", "strong", "full"}
EVIDENCE = {"head", "source_tree", "target_base", "required_gates", "profile", "e2e_environment"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--template-mode", action="store_true")
    a = p.parse_args()
    errors = []
    try:
        data = json.loads((Path(a.root) / ".engineering/commands.json").read_text())
    except Exception as exc:
        print(f"FAIL: invalid commands.json: {exc}")
        return 1
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("contract_version") != "0.6.1":
        errors.append("contract_version must be 0.6.1")
    commands = data.get("commands", {})
    for n in COMMANDS:
        e = commands.get(n)
        if not isinstance(e, dict):
            errors.append(f"missing command intent: {n}")
            continue
        if e.get("status") not in STATUSES:
            errors.append(f"commands.{n}.status invalid")
        if e.get("status") != "n/a" and not str(e.get("run", "")).strip():
            errors.append(f"commands.{n}.run required")
    v = data.get("development_velocity", {})
    if v.get("stages") != ["iteration", "integration", "release"]:
        errors.append("development stages invalid")
    if v.get("default_stage") != "iteration":
        errors.append("default stage must be iteration")
    for k in (
        "parallel_development_prefers_early_convergence",
        "stacked_publication_exception_only",
    ):
        if v.get(k) is not True:
            errors.append(f"development_velocity.{k} must be true")
    integration = v.get("integration", {})
    if integration.get("exact_head_required") is not True:
        errors.append("integration exact-head required")
    if integration.get("automated_e2e_required_when_affected") is not True:
        errors.append("integration affected automated E2E required")
    if integration.get("real_environment_blocking") is not False:
        errors.append("integration real environment must not block")
    if integration.get("real_environment_deferred_to_release") is not True:
        errors.append("integration real environment must defer to release")
    release = v.get("release", {})
    if release.get("full_validation_required") is not True:
        errors.append("release full validation required")
    if release.get("required_real_environment_blocking") is not True:
        errors.append("release required real environment must block")
    pub = data.get("publication_gate", {})
    if pub.get("applies_from_stage") != "integration":
        errors.append("publication gate must start at integration")
    for k in (
        "agent_preflight_required",
        "target_base_freshness_required",
        "full_diff_review_required",
        "failure_root_cause_required",
        "execution_capability_classification_required",
        "automatable_gates_must_not_be_delegated_to_user",
        "exact_head_evidence_required",
    ):
        if pub.get(k) is not True:
            errors.append(f"publication_gate.{k} must be true")
    profiles = data.get("validation_profiles", {})
    if profiles.get("default") != "auto" or not PROFILES.issubset(
        set(profiles.get("profiles", []))
    ):
        errors.append("validation profiles incomplete")
    if profiles.get("selector_output") != "risk_dimensions_and_required_gates":
        errors.append("selector output must be risks and gates")
    for k in (
        "profiles_are_shorthand",
        "gate_selection_preferred_over_suite_selection",
        "selector_changes_force_full",
        "promotion_validation_full",
    ):
        if profiles.get(k) is not True:
            errors.append(f"validation_profiles.{k} must be true")
    r = data.get("remote_preflight", {})
    for k in (
        "exact_head_required",
        "reuse_successful_equivalent_evidence",
        "rerun_only_when_missing_stale_or_insufficient",
        "post_merge_tree_equivalent_reuse_allowed",
        "post_merge_tree_reuse_requires_same_target_base",
        "direct_push_without_equivalent_evidence_must_validate",
        "trusted_requesters_only",
        "same_repository_prs_only_by_default",
        "report_result_to_pr",
    ):
        if r.get(k) is not True:
            errors.append(f"remote_preflight.{k} must be true")
    if r.get("execution_job_write_credentials") is not False:
        errors.append("remote execution must be read-only")
    if not EVIDENCE.issubset(set(r.get("evidence_identity_fields", []))):
        errors.append("evidence identity fields incomplete")
    e2e = data.get("end_to_end", {})
    if e2e.get("ui_evidence_modes") != ["assertions", "screenshots", "full_media"]:
        errors.append("UI evidence modes invalid")
    if e2e.get("ui_evidence_selection") != "risk_based":
        errors.append("UI evidence selection must be risk_based")
    econ = data.get("validation_economics", {})
    if (
        econ.get("status") not in {"recommended", "required"}
        or econ.get("periodic_review") is not True
    ):
        errors.append("validation economics not enabled")
    for section in (
        "build_identity",
        "artifact_lifecycle",
        "build_delta",
        "local_runtime",
        "ephemeral_resources",
    ):
        if not isinstance(data.get(section), dict):
            errors.append(f"{section} must be an object")
    print("Project operating contract check")
    for x in errors:
        print("FAIL:", x)
    print("RESULT:", "FAIL" if errors else "PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
