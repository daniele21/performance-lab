from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from performance_lab.domain import Run, RunStatus, TelemetryLevel
from performance_lab.storage import RunNotFoundError, SQLiteRunStore

VALUE02_EVIDENCE_GATE_ID = "VALUE-02C"
POLICY_ID = "strict-quality-dominance"
POLICY_VERSION = "1.0.0"
LOCAL_LLM_STATUS_COLLECTOR_ID = "local-llm-server-status"


def _check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    *,
    detail: str,
) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"cannot read {label} evidence") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} evidence is invalid JSON") from exc
    if not isinstance(raw, dict):
        raise RuntimeError(f"{label} evidence must contain an object")
    return raw


def _entry_run_ids(campaign: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
    entries = campaign.get("entries")
    if not isinstance(entries, list):
        return ()
    result: list[tuple[str, str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        candidate_id = entry.get("candidate_id")
        model_id = entry.get("model_id")
        run_id = entry.get("run_id")
        if all(isinstance(value, str) and value for value in (candidate_id, model_id, run_id)):
            result.append((str(candidate_id), str(model_id), str(run_id)))
    return tuple(result)


def _runtime_identity_complete(run: Run) -> bool:
    fingerprint = run.fingerprint
    return (
        fingerprint.runtime.name is not None
        and fingerprint.runtime.config_digest is not None
        and fingerprint.hardware.device_class is not None
        and fingerprint.hardware.os is not None
        and fingerprint.telemetry.level == TelemetryLevel.INSTRUMENTED
        and LOCAL_LLM_STATUS_COLLECTOR_ID in fingerprint.telemetry.collectors
    )


def _run_identity_summary(run: Run) -> dict[str, Any]:
    fingerprint = run.fingerprint
    return {
        "run_id": run.run_id,
        "fingerprint_id": fingerprint.fingerprint_id,
        "model_id": fingerprint.model.model_id,
        "quantization": fingerprint.model.quantization,
        "runtime_name": fingerprint.runtime.name,
        "runtime_version": fingerprint.runtime.version,
        "runtime_config_digest": fingerprint.runtime.config_digest,
        "hardware_device_id": fingerprint.hardware.device_id,
        "hardware_device_class": fingerprint.hardware.device_class,
        "hardware_os": fingerprint.hardware.os,
        "telemetry_level": fingerprint.telemetry.level.value,
        "suite_id": run.suite.suite_id,
        "suite_version": run.suite.suite_version,
        "benchmark_protocol_version": fingerprint.benchmark_protocol_version,
    }


def _verify_campaign_contract(
    checks: list[dict[str, Any]],
    campaign: dict[str, Any],
) -> tuple[tuple[str, str, str], ...]:
    entries = _entry_run_ids(campaign)
    _check(
        checks,
        "multi_candidate_campaign",
        campaign.get("status") == "succeeded" and len(entries) >= 2,
        detail=(
            "campaign succeeded with at least two retained candidate Run ids"
            if campaign.get("status") == "succeeded" and len(entries) >= 2
            else "campaign must succeed with at least two retained candidate Run ids"
        ),
    )

    results = campaign.get("results")
    if not isinstance(results, dict):
        _check(checks, "canonical_results", False, detail="campaign results read model is missing")
        return entries

    policy = results.get("decision_policy")
    policy_ok = (
        isinstance(policy, dict)
        and policy.get("policy_id") == POLICY_ID
        and policy.get("policy_version") == POLICY_VERSION
        and policy.get("no_hidden_weights") is True
    )
    _check(
        checks,
        "decision_policy",
        policy_ok,
        detail=(
            "canonical strict-quality-dominance@1.0.0 policy has no hidden weights"
            if policy_ok
            else "campaign does not retain the required versioned decision policy"
        ),
    )

    dimensions_raw = results.get("compatibility")
    dimensions = (
        {
            item.get("dimension"): item
            for item in dimensions_raw
            if isinstance(dimensions_raw, list) and isinstance(item, dict)
        }
        if isinstance(dimensions_raw, list)
        else {}
    )
    dimension_ok = {"capability", "runtime", "resource"}.issubset(dimensions)
    _check(
        checks,
        "separate_evidence_dimensions",
        dimension_ok,
        detail=(
            "capability, runtime and resource compatibility remain separate"
            if dimension_ok
            else "canonical results are missing one or more separate evidence dimensions"
        ),
    )

    recommendation = results.get("recommendation")
    reason = results.get("recommendation_reason")
    entry_by_run = {run_id: (candidate_id, model_id) for candidate_id, model_id, run_id in entries}
    if recommendation is None:
        no_rank_ok = (
            isinstance(reason, str) and bool(reason.strip()) and results.get("state") == "ready"
        )
        _check(
            checks,
            "recommendation_or_no_rank",
            no_rank_ok,
            detail=(
                "canonical results explicitly retain a no-rank reason"
                if no_rank_ok
                else "no recommendation was retained without a canonical ready-state reason"
            ),
        )
    else:
        capability = dimensions.get("capability")
        recommendation_ok = (
            isinstance(recommendation, dict)
            and isinstance(capability, dict)
            and capability.get("comparable") is True
            and capability.get("evidence_available") is True
            and recommendation.get("run_id") in entry_by_run
            and isinstance(reason, str)
            and bool(reason.strip())
        )
        if recommendation_ok:
            expected_candidate, expected_model = entry_by_run[str(recommendation["run_id"])]
            recommendation_ok = (
                recommendation.get("candidate_id") == expected_candidate
                and recommendation.get("model_id") == expected_model
            )
        _check(
            checks,
            "recommendation_or_no_rank",
            recommendation_ok,
            detail=(
                "recommendation points to retained compatible canonical Run evidence"
                if recommendation_ok
                else "recommendation is not backed by canonical comparable retained evidence"
            ),
        )
    return entries


def _verify_runs(
    checks: list[dict[str, Any]],
    *,
    store: SQLiteRunStore,
    campaign: dict[str, Any],
    entries: tuple[tuple[str, str, str], ...],
) -> tuple[Run, ...]:
    runs: list[Run] = []
    missing: list[str] = []
    mismatched_models: list[str] = []
    for _, model_id, run_id in entries:
        try:
            run = store.get_completed(run_id)
        except RunNotFoundError:
            run = None
        if run is None:
            missing.append(run_id)
            continue
        runs.append(run)
        if run.fingerprint.model.model_id != model_id:
            mismatched_models.append(run_id)

    _check(
        checks,
        "immutable_candidate_runs",
        len(runs) == len(entries)
        and len(runs) >= 2
        and all(run.status == RunStatus.SUCCEEDED for run in runs),
        detail=(
            "every candidate maps to an immutable completed SUCCEEDED Run"
            if len(runs) == len(entries)
            and len(runs) >= 2
            and all(run.status == RunStatus.SUCCEEDED for run in runs)
            else f"candidate Run evidence is missing or unsuccessful: {missing}"
        ),
    )
    _check(
        checks,
        "candidate_model_attribution",
        not mismatched_models,
        detail=(
            "each campaign entry model id matches its frozen Run fingerprint"
            if not mismatched_models
            else f"candidate model attribution differs for Run ids: {mismatched_models}"
        ),
    )

    if not runs:
        return ()
    reference = runs[0]
    target_id = campaign.get("target_id")
    same_context = all(
        run.fingerprint.target_id == target_id
        and run.fingerprint.hardware == reference.fingerprint.hardware
        and run.suite.suite_id == campaign.get("suite_id")
        and run.suite.suite_version == campaign.get("suite_version")
        and run.fingerprint.benchmark_protocol_version
        == reference.fingerprint.benchmark_protocol_version
        and run.fingerprint.dataset_snapshots == reference.fingerprint.dataset_snapshots
        and run.fingerprint.evaluator_versions == reference.fingerprint.evaluator_versions
        for run in runs
    )
    _check(
        checks,
        "shared_decision_context",
        len(runs) >= 2 and same_context,
        detail=(
            "candidate Runs share target/device and frozen benchmark protocol identity"
            if len(runs) >= 2 and same_context
            else "candidate Runs do not share the required target/device/benchmark context"
        ),
    )

    identity_ok = all(_runtime_identity_complete(run) for run in runs)
    _check(
        checks,
        "first_party_runtime_device_evidence",
        identity_ok,
        detail=(
            "all candidates retain instrumented Local LLM Server runtime/device identity"
            if identity_ok
            else "one or more candidates lack required first-party runtime/device evidence"
        ),
    )
    return tuple(runs)


def _verify_case_comparison(
    checks: list[dict[str, Any]],
    *,
    campaign: dict[str, Any],
    comparison: dict[str, Any],
    run_ids: set[str],
) -> None:
    candidates = comparison.get("candidates")
    comparable = (
        [
            item
            for item in candidates
            if isinstance(candidates, list)
            and isinstance(item, dict)
            and item.get("comparable_to_reference") is True
            and isinstance(item.get("evidence"), dict)
            and item.get("run_id") in run_ids
        ]
        if isinstance(candidates, list)
        else []
    )
    same_case_ok = (
        comparison.get("campaign_id") == campaign.get("campaign_id")
        and comparison.get("suite_id") == campaign.get("suite_id")
        and comparison.get("suite_version") == campaign.get("suite_version")
        and comparison.get("state") in {"ready", "partial"}
        and int(comparison.get("comparable_candidate_count") or 0) >= 2
        and len(comparable) >= 2
        and isinstance(comparison.get("task_id"), str)
        and isinstance(comparison.get("sample_id"), str)
    )
    _check(
        checks,
        "same_case_drilldown",
        same_case_ok,
        detail=(
            "one exact case retains evidence for at least two compatible campaign candidates"
            if same_case_ok
            else "same-case comparison does not retain two compatible candidate evidence records"
        ),
    )


def verify_value02_evidence(
    *,
    store_path: Path,
    campaign_path: Path,
    case_comparison_path: Path,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    campaign = _load_object(campaign_path, "campaign")
    comparison = _load_object(case_comparison_path, "same-case comparison")
    entries = _verify_campaign_contract(checks, campaign)
    runs = _verify_runs(
        checks,
        store=SQLiteRunStore(store_path),
        campaign=campaign,
        entries=entries,
    )
    _verify_case_comparison(
        checks,
        campaign=campaign,
        comparison=comparison,
        run_ids={run.run_id for run in runs},
    )
    passed = all(check["status"] == "PASS" for check in checks)
    return {
        "schema_version": 1,
        "gate_id": VALUE02_EVIDENCE_GATE_ID,
        "status": "PASS" if passed else "FAIL",
        "campaign_id": campaign.get("campaign_id"),
        "decision": {
            "policy_id": POLICY_ID,
            "policy_version": POLICY_VERSION,
            "recommendation_present": bool(
                isinstance(campaign.get("results"), dict)
                and campaign["results"].get("recommendation") is not None
            ),
        },
        "runs": [_run_identity_summary(run) for run in runs],
        "case": {
            "task_id": comparison.get("task_id"),
            "sample_id": comparison.get("sample_id"),
            "state": comparison.get("state"),
            "comparable_candidate_count": comparison.get("comparable_candidate_count"),
        },
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify retained VALUE-02 multi-model decision evidence."
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--case-comparison", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = verify_value02_evidence(
            store_path=args.store.expanduser().resolve(),
            campaign_path=args.campaign.expanduser().resolve(),
            case_comparison_path=args.case_comparison.expanduser().resolve(),
        )
    except RuntimeError as exc:
        manifest = {
            "schema_version": 1,
            "gate_id": VALUE02_EVIDENCE_GATE_ID,
            "status": "FAIL",
            "error": {"type": type(exc).__name__, "message": str(exc)[:500]},
            "checks": [],
        }
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if manifest["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
