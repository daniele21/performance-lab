import json
from datetime import UTC, datetime
from io import StringIO

from performance_lab.cli import main
from performance_lab.domain import (
    ComparisonDimension,
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    HardwareIdentity,
    LoadProfile,
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
    ModelIdentity,
    Run,
    RunStatus,
    TaskSpec,
    TelemetryDescriptor,
    TelemetryLevel,
)
from performance_lab.regression import MetricDirection, MetricThresholdRule, RegressionPolicy
from performance_lab.storage import SQLiteRunStore

RESOURCE_METRIC = "peak_rss_bytes|host|host-v1|bytes"


def evaluator() -> EvaluatorRef:
    return EvaluatorRef(evaluator_id="exact-match", version="1")


def suite() -> EvaluationSuite:
    generation = GenerationConfig(max_output_tokens=8, temperature=0.0)
    return EvaluationSuite(
        suite_id="suite",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="task",
                dataset_snapshot_id="demo",
                evaluator=evaluator(),
                metric_names=("accuracy",),
            ),
        ),
        generation=generation,
    )


def resource_run(run_id: str, *, peak_rss_bytes: float) -> Run:
    active_suite = suite()
    dataset = DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="fixture",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )
    fingerprint = ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="local",
        model=ModelIdentity(model_id=run_id),
        hardware=HardwareIdentity(device_id="runner-a", os="linux", accelerator="test-gpu"),
        generation=active_suite.generation,
        prompt_template_version="chat-v1",
        dataset_snapshots=(dataset,),
        evaluator_versions=(evaluator(),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(concurrency=1, request_count=1),
        telemetry=TelemetryDescriptor(
            level=TelemetryLevel.HOST,
            protocol_version="host-v1",
            collectors=("host",),
        ),
    )
    now = datetime.now(UTC)
    return Run(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=active_suite,
        created_at=now,
        completed_at=now,
        aggregate_measurements=(
            Measurement(
                name="peak_rss_bytes",
                value=peak_rss_bytes,
                unit="bytes",
                scope=MeasurementScope.RUN,
                provenance=MeasurementProvenance.HOST,
                protocol_version="host-v1",
            ),
        ),
    )


def write_resource_policy(path) -> None:
    policy = RegressionPolicy(
        policy_id="resource-gate",
        policy_version="1",
        rules=(
            MetricThresholdRule(
                rule_id="rss",
                dimension=ComparisonDimension.RESOURCE,
                metric=RESOURCE_METRIC,
                direction=MetricDirection.LOWER_IS_BETTER,
                max_relative_regression_pct=5.0,
            ),
        ),
    )
    path.write_text(policy.model_dump_json(indent=2), encoding="utf-8")


def invoke_ci(
    store_path,
    policy_path,
    artifact_path,
    *,
    controlled: bool,
) -> tuple[int, dict[str, object]]:
    args = [
        "regress-ci",
        "--store",
        str(store_path),
        "--baseline-run",
        "baseline",
        "--candidate-run",
        "candidate",
        "--policy",
        str(policy_path),
        "--artifact",
        str(artifact_path),
        "--json",
    ]
    if controlled:
        args.append("--runner-identity-controlled")
    output = StringIO()
    exit_code = main(args, stdout=output)
    return exit_code, json.loads(output.getvalue())


def test_uncontrolled_ci_runner_forces_resource_rule_not_comparable(tmp_path, monkeypatch) -> None:
    store_path = tmp_path / "runs.sqlite3"
    policy_path = tmp_path / "policy.json"
    artifact_path = tmp_path / "gate.json"
    summary_path = tmp_path / "summary.md"
    store = SQLiteRunStore(store_path)
    store.publish(resource_run("baseline", peak_rss_bytes=100.0))
    store.publish(resource_run("candidate", peak_rss_bytes=90.0))
    write_resource_policy(policy_path)
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))

    exit_code, report = invoke_ci(
        store_path,
        policy_path,
        artifact_path,
        controlled=False,
    )

    assert exit_code == 3
    assert report["decision"] == "not_comparable"
    assert report["resource_hardware_comparability_trusted"] is False
    assert report["rule_results"][0]["policy_state"] == "pass"
    assert report["rule_results"][0]["effective_state"] == "not_comparable"
    assert json.loads(artifact_path.read_text(encoding="utf-8"))["decision"] == "not_comparable"
    summary = summary_path.read_text(encoding="utf-8")
    assert "NOT_COMPARABLE" in summary
    assert "uncontrolled" in summary


def test_controlled_ci_runner_can_use_compatible_resource_rule(tmp_path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    policy_path = tmp_path / "policy.json"
    artifact_path = tmp_path / "gate.json"
    store = SQLiteRunStore(store_path)
    store.publish(resource_run("baseline", peak_rss_bytes=100.0))
    store.publish(resource_run("candidate", peak_rss_bytes=90.0))
    write_resource_policy(policy_path)

    exit_code, report = invoke_ci(
        store_path,
        policy_path,
        artifact_path,
        controlled=True,
    )

    assert exit_code == 0
    assert report["decision"] == "pass"
    assert report["resource_hardware_comparability_trusted"] is True
    assert report["rule_results"][0]["effective_state"] == "pass"
