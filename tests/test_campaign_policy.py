from datetime import UTC, datetime

from performance_lab.application.campaign_policy import recommend_strict_quality_dominance
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
    Score,
)


def _run(model_id: str, values: tuple[float, float]) -> Run:
    bundle = build_general_starter_suite()
    fingerprint = ExecutionFingerprint(
        target_id="target-a",
        adapter_type="openai-compatible",
        endpoint_identity="loopback:1234",
        model=ModelIdentity(model_id=model_id),
        runtime=RuntimeIdentity(),
        hardware=HardwareIdentity(device_id="device-a"),
        generation=bundle.suite.generation,
        prompt_template_version="direct-user-v1",
        dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
        evaluator_versions=(
            EvaluatorRef(evaluator_id="metric-a-evaluator", version="1"),
            EvaluatorRef(evaluator_id="metric-b-evaluator", version="1"),
        ),
        benchmark_protocol_version="starter-quality-v1",
        load_profile=LoadProfile(concurrency=1, request_count=23, streaming=False),
    )
    scores = (
        Score(
            metric="metric-a",
            value=values[0],
            evaluator=EvaluatorRef(evaluator_id="metric-a-evaluator", version="1"),
            higher_is_better=True,
        ),
        Score(
            metric="metric-b",
            value=values[1],
            evaluator=EvaluatorRef(evaluator_id="metric-b-evaluator", version="1"),
            higher_is_better=True,
        ),
    )
    now = datetime.now(UTC)
    return Run(
        run_id=f"run-{model_id}",
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=bundle.suite,
        created_at=now,
        completed_at=now,
        aggregate_scores=scores,
    )


def test_policy_recommends_only_a_strict_quality_dominator() -> None:
    decision = recommend_strict_quality_dominance(
        (
            ("candidate-a", _run("model-a", (1.0, 0.9))),
            ("candidate-b", _run("model-b", (0.8, 0.9))),
        )
    )

    assert decision.candidate_id == "candidate-a"
    assert decision.run_id == "run-model-a"


def test_policy_does_not_hide_tradeoffs_in_a_weighted_score() -> None:
    decision = recommend_strict_quality_dominance(
        (
            ("candidate-a", _run("model-a", (1.0, 0.7))),
            ("candidate-b", _run("model-b", (0.8, 0.9))),
        )
    )

    assert decision.candidate_id is None
    assert "No single candidate strictly dominates" in decision.reason
