import json
from datetime import UTC, datetime
from io import StringIO

from performance_lab.cli import main
from performance_lab.domain import (
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    HardwareIdentity,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    Score,
    TaskSpec,
)
from performance_lab.regression import MetricThresholdRule, RegressionPolicy
from performance_lab.storage import SQLiteRunStore


def evaluator() -> EvaluatorRef:
    return EvaluatorRef(evaluator_id="exact-match", version="1")


def dataset(version: str = "1", digest: str = "a") -> DatasetSnapshot:
    return DatasetSnapshot(
        dataset_id="demo",
        dataset_version=version,
        source="fixture",
        split="test",
        content_sha256=digest * 64,
        selection_policy="all",
        sample_count=1,
    )


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


def completed_run(
    run_id: str,
    *,
    accuracy: float,
    snapshot: DatasetSnapshot | None = None,
) -> Run:
    active_suite = suite()
    active_dataset = snapshot or dataset()
    fingerprint = ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="local",
        model=ModelIdentity(model_id=run_id),
        hardware=HardwareIdentity(device_id="device-a", os="linux"),
        generation=active_suite.generation,
        prompt_template_version="chat-v1",
        dataset_snapshots=(active_dataset,),
        evaluator_versions=(evaluator(),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(concurrency=1, request_count=1),
    )
    now = datetime.now(UTC)
    return Run(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=active_suite,
        created_at=now,
        completed_at=now,
        aggregate_scores=(
            Score(
                metric="accuracy",
                value=accuracy,
                evaluator=evaluator(),
                higher_is_better=True,
            ),
        ),
    )


def write_policy(path) -> None:
    policy = RegressionPolicy(
        policy_id="release-gate",
        policy_version="1",
        rules=(
            MetricThresholdRule(
                rule_id="accuracy",
                dimension="capability",
                metric="accuracy|exact-match@1",
                max_absolute_regression=0.02,
            ),
        ),
    )
    path.write_text(policy.model_dump_json(indent=2), encoding="utf-8")


def invoke_regress(store_path, policy_path, candidate_run: str) -> tuple[int, dict[str, object]]:
    output = StringIO()
    exit_code = main(
        [
            "regress",
            "--store",
            str(store_path),
            "--baseline-run",
            "baseline",
            "--candidate-run",
            candidate_run,
            "--policy",
            str(policy_path),
            "--json",
        ],
        stdout=output,
    )
    return exit_code, json.loads(output.getvalue())


def test_regress_command_emits_stable_pass_and_fail_json_with_exit_codes(tmp_path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    policy_path = tmp_path / "policy.json"
    store = SQLiteRunStore(store_path)
    store.publish(completed_run("baseline", accuracy=0.80))
    store.publish(completed_run("passing", accuracy=0.79))
    store.publish(completed_run("failing", accuracy=0.70))
    write_policy(policy_path)

    pass_code, pass_report = invoke_regress(store_path, policy_path, "passing")
    fail_code, fail_report = invoke_regress(store_path, policy_path, "failing")

    assert pass_code == 0
    assert pass_report["schema_version"] == 1
    assert pass_report["decision"] == "pass"
    assert pass_report["baseline_run_id"] == "baseline"
    assert pass_report["candidate_run_id"] == "passing"
    assert pass_report["policy_id"] == "release-gate"
    assert fail_code == 1
    assert fail_report["decision"] == "fail"


def test_regress_command_returns_not_comparable_for_dataset_identity_change(tmp_path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    policy_path = tmp_path / "policy.json"
    store = SQLiteRunStore(store_path)
    store.publish(completed_run("baseline", accuracy=0.80))
    store.publish(
        completed_run(
            "incompatible",
            accuracy=0.90,
            snapshot=dataset(version="2", digest="b"),
        )
    )
    write_policy(policy_path)

    exit_code, report = invoke_regress(store_path, policy_path, "incompatible")

    assert exit_code == 3
    assert report["decision"] == "not_comparable"
    evaluation = report["evaluation"]
    assert isinstance(evaluation, dict)
    assert evaluation["rule_results"][0]["state"] == "not_comparable"


def test_regress_command_emits_machine_readable_error_for_missing_run(tmp_path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    policy_path = tmp_path / "policy.json"
    SQLiteRunStore(store_path)
    write_policy(policy_path)

    exit_code, report = invoke_regress(store_path, policy_path, "missing")

    assert exit_code == 2
    assert report["schema_version"] == 1
    assert report["decision"] == "error"
    assert report["error_type"]
    assert report["message"]
