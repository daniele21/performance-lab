from datetime import UTC, datetime

from fastapi.testclient import TestClient

from performance_lab.application import UIQueryService
from performance_lab.domain import (
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    Score,
    TaskSpec,
)
from performance_lab.regression import MetricThresholdRule, RegressionPolicy
from performance_lab.regression_api import attach_regression_api
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app


def _evaluator() -> EvaluatorRef:
    return EvaluatorRef(evaluator_id="exact-match", version="1")


def _dataset(version: str = "1", digest: str = "a") -> DatasetSnapshot:
    return DatasetSnapshot(
        dataset_id="demo",
        dataset_version=version,
        source="fixture",
        split="test",
        content_sha256=digest * 64,
        selection_policy="all",
        sample_count=1,
    )


def _suite() -> EvaluationSuite:
    evaluator = _evaluator()
    generation = GenerationConfig(max_output_tokens=8, temperature=0.0)
    return EvaluationSuite(
        suite_id="suite",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="task",
                dataset_snapshot_id="demo",
                evaluator=evaluator,
                metric_names=("accuracy",),
            ),
        ),
        generation=generation,
    )


def _run(
    run_id: str,
    *,
    accuracy: float,
    snapshot: DatasetSnapshot | None = None,
) -> Run:
    suite = _suite()
    dataset = snapshot or _dataset()
    fingerprint = ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="local",
        model=ModelIdentity(model_id=run_id),
        generation=suite.generation,
        prompt_template_version="chat-v1",
        dataset_snapshots=(dataset,),
        evaluator_versions=(_evaluator(),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(concurrency=1, request_count=1),
    )
    now = datetime.now(UTC)
    return Run(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=suite,
        created_at=now,
        completed_at=now,
        aggregate_scores=(
            Score(
                metric="accuracy",
                value=accuracy,
                evaluator=_evaluator(),
                higher_is_better=True,
            ),
        ),
    )


def _policy() -> RegressionPolicy:
    return RegressionPolicy(
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


def _queries(tmp_path) -> UIQueryService:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(_run("baseline", accuracy=0.80))
    store.publish(_run("passing", accuracy=0.79))
    store.publish(_run("failing", accuracy=0.70))
    store.publish(
        _run(
            "incompatible",
            accuracy=0.90,
            snapshot=_dataset(version="2", digest="b"),
        )
    )
    return UIQueryService(store, policies=(_policy(),))


def test_regression_projection_reuses_policy_owner_for_all_typed_decisions(tmp_path) -> None:
    queries = _queries(tmp_path)

    passing = queries.evaluate_regression(
        baseline_run_id="baseline",
        candidate_run_id="passing",
        policy_id="release-gate",
        policy_version="1",
    )
    failing = queries.evaluate_regression(
        baseline_run_id="baseline",
        candidate_run_id="failing",
        policy_id="release-gate",
        policy_version="1",
    )
    incompatible = queries.evaluate_regression(
        baseline_run_id="baseline",
        candidate_run_id="incompatible",
        policy_id="release-gate",
        policy_version="1",
    )

    assert passing.decision.value == "pass"
    assert passing.rule_results[0].state.value == "pass"
    assert failing.decision.value == "fail"
    assert failing.rule_results[0].state.value == "fail"
    assert incompatible.decision.value == "not_comparable"
    assert incompatible.rule_results[0].state.value == "not_comparable"
    capability = next(
        item for item in incompatible.comparison.dimensions if item.dimension.value == "capability"
    )
    assert capability.comparable is False
    assert capability.deltas == ()
    assert capability.reasons


def test_regression_api_requires_exact_configured_policy_and_distinct_runs(tmp_path) -> None:
    queries = _queries(tmp_path)
    app = create_ui_app(queries)
    attach_regression_api(app, queries)
    client = TestClient(app)

    response = client.get(
        "/api/v1/regression-evaluations",
        params={
            "baseline_run_id": "baseline",
            "candidate_run_id": "passing",
            "policy_id": "release-gate",
            "policy_version": "1",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "pass"
    assert payload["policy_id"] == "release-gate"
    assert payload["policy_version"] == "1"
    assert payload["baseline_fingerprint_id"]
    assert payload["candidate_fingerprint_id"]

    missing_policy = client.get(
        "/api/v1/regression-evaluations",
        params={
            "baseline_run_id": "baseline",
            "candidate_run_id": "passing",
            "policy_id": "missing",
            "policy_version": "1",
        },
    )
    assert missing_policy.status_code == 404

    same_run = client.get(
        "/api/v1/regression-evaluations",
        params={
            "baseline_run_id": "baseline",
            "candidate_run_id": "baseline",
            "policy_id": "release-gate",
            "policy_version": "1",
        },
    )
    assert same_run.status_code == 422
