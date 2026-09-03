import json
from datetime import UTC, datetime
from pathlib import Path

from performance_lab.datasets import build_general_starter_suite
from performance_lab.domain import (
    EvaluatorRef,
    ExecutionFingerprint,
    HardwareIdentity,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    RuntimeIdentity,
    TelemetryDescriptor,
    TelemetryLevel,
)
from performance_lab.storage import SQLiteRunStore
from tests.real_runtime.verify_value02_evidence import verify_value02_evidence


def _run(model_id: str, run_id: str) -> Run:
    bundle = build_general_starter_suite()
    evaluators = tuple(
        EvaluatorRef(evaluator_id=evaluator_id, version=version)
        for evaluator_id, version in sorted(
            {
                task.evaluator.evaluator_id: task.evaluator.version for task in bundle.suite.tasks
            }.items()
        )
    )
    now = datetime.now(UTC)
    return Run(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        fingerprint=ExecutionFingerprint(
            target_id="local-llm-server-value02",
            adapter_type="openai-compatible",
            endpoint_identity="http://127.0.0.1:1235",
            model=ModelIdentity(model_id=model_id),
            runtime=RuntimeIdentity(
                name="llama.cpp",
                version="b7000",
                config_digest=f"config-{model_id}",
            ),
            hardware=HardwareIdentity(
                device_id="device-a",
                device_class="laptop",
                cpu="apple-silicon",
                accelerator="metal",
                memory_bytes=32 * 1024**3,
                os="macos",
            ),
            generation=bundle.suite.generation,
            prompt_template_version="direct-user-v1",
            dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
            evaluator_versions=evaluators,
            benchmark_protocol_version="starter-quality-v1",
            load_profile=LoadProfile(concurrency=1, request_count=23, streaming=False),
            telemetry=TelemetryDescriptor(
                level=TelemetryLevel.INSTRUMENTED,
                protocol_version="local-llm-server-status-v1",
                collectors=("local-llm-server-status",),
            ),
        ),
        suite=bundle.suite,
        created_at=now,
        completed_at=now,
    )


def _campaign(suite_version: str) -> dict[str, object]:
    return {
        "campaign_id": "campaign-value02",
        "target_id": "local-llm-server-value02",
        "suite_id": "general-diagnostic-starter",
        "suite_version": suite_version,
        "status": "succeeded",
        "entries": [
            {
                "candidate_id": "candidate-a",
                "model_id": "model-a",
                "run_id": "run-a",
            },
            {
                "candidate_id": "candidate-b",
                "model_id": "model-b",
                "run_id": "run-b",
            },
        ],
        "results": {
            "state": "ready",
            "decision_policy": {
                "policy_id": "strict-quality-dominance",
                "policy_version": "1.0.0",
                "no_hidden_weights": True,
            },
            "compatibility": [
                {
                    "dimension": "capability",
                    "comparable": True,
                    "evidence_available": True,
                },
                {
                    "dimension": "runtime",
                    "comparable": True,
                    "evidence_available": True,
                },
                {
                    "dimension": "resource",
                    "comparable": True,
                    "evidence_available": True,
                },
            ],
            "recommendation": {
                "candidate_id": "candidate-a",
                "model_id": "model-a",
                "run_id": "run-a",
            },
            "recommendation_reason": "candidate-a strictly dominates comparable quality evidence",
        },
    }


def _comparison(suite_version: str) -> dict[str, object]:
    return {
        "campaign_id": "campaign-value02",
        "suite_id": "general-diagnostic-starter",
        "suite_version": suite_version,
        "task_id": "instruction-following",
        "sample_id": "if-001",
        "state": "ready",
        "comparable_candidate_count": 2,
        "candidates": [
            {
                "candidate_id": "candidate-a",
                "model_id": "model-a",
                "run_id": "run-a",
                "comparable_to_reference": True,
                "evidence": {"run": {"run_id": "run-a"}},
            },
            {
                "candidate_id": "candidate-b",
                "model_id": "model-b",
                "run_id": "run-b",
                "comparable_to_reference": True,
                "evidence": {"run": {"run_id": "run-b"}},
            },
        ],
    }


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_value02_verifier_accepts_canonical_multi_model_decision(tmp_path: Path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    store = SQLiteRunStore(store_path)
    first = _run("model-a", "run-a")
    second = _run("model-b", "run-b")
    store.publish(first)
    store.publish(second)
    campaign_path = tmp_path / "campaign.json"
    comparison_path = tmp_path / "case.json"
    _write(campaign_path, _campaign(first.suite.suite_version))
    _write(comparison_path, _comparison(first.suite.suite_version))

    result = verify_value02_evidence(
        store_path=store_path,
        campaign_path=campaign_path,
        case_comparison_path=comparison_path,
    )

    assert result["status"] == "PASS"
    assert result["decision"] == {
        "policy_id": "strict-quality-dominance",
        "policy_version": "1.0.0",
        "recommendation_present": True,
    }
    assert [item["model_id"] for item in result["runs"]] == ["model-a", "model-b"]


def test_value02_verifier_rejects_unversioned_or_wrong_policy(tmp_path: Path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    store = SQLiteRunStore(store_path)
    first = _run("model-a", "run-a")
    second = _run("model-b", "run-b")
    store.publish(first)
    store.publish(second)
    campaign = _campaign(first.suite.suite_version)
    campaign["results"]["decision_policy"]["policy_version"] = "2.0.0"  # type: ignore[index]
    campaign_path = tmp_path / "campaign.json"
    comparison_path = tmp_path / "case.json"
    _write(campaign_path, campaign)
    _write(comparison_path, _comparison(first.suite.suite_version))

    result = verify_value02_evidence(
        store_path=store_path,
        campaign_path=campaign_path,
        case_comparison_path=comparison_path,
    )

    assert result["status"] == "FAIL"
    decision_check = next(item for item in result["checks"] if item["name"] == "decision_policy")
    assert decision_check["status"] == "FAIL"
