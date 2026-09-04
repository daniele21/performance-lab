from datetime import UTC, datetime
from pathlib import Path

from performance_lab.application import CampaignQueryService, UIQueryService
from performance_lab.datasets import build_general_starter_suite
from performance_lab.domain import (
    Campaign,
    CampaignEntry,
    CampaignEntryStatus,
    CampaignStatus,
    DecisionPolicyRef,
    ExecutionFingerprint,
    HardwareIdentity,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    RuntimeIdentity,
    SampleExecution,
    SampleStatus,
    Score,
)
from performance_lab.storage import SQLiteCampaignStore, SQLiteRunStore


def _run(
    model_id: str,
    *,
    score_value: float,
    prompt_template_version: str = "direct-user-v1",
) -> Run:
    bundle = build_general_starter_suite()
    task = bundle.suite.tasks[0]
    record = bundle.datasets[task.dataset_snapshot_id].records[0]
    now = datetime.now(UTC)
    evaluators = tuple(
        dict.fromkeys(
            (item.evaluator.evaluator_id, item.evaluator.version) for item in bundle.suite.tasks
        )
    )
    evaluator_refs = tuple(
        next(
            item.evaluator
            for item in bundle.suite.tasks
            if (item.evaluator.evaluator_id, item.evaluator.version) == identity
        )
        for identity in evaluators
    )
    sample = SampleExecution(
        sample_id=record.sample_id,
        task_id=task.task_id,
        status=SampleStatus.SUCCEEDED,
        started_at=now,
        completed_at=now,
        scores=(
            Score(
                metric=task.metric_names[0],
                value=score_value,
                evaluator=task.evaluator,
                higher_is_better=True,
            ),
        ),
    )
    return Run(
        run_id=f"run-{model_id}",
        status=RunStatus.SUCCEEDED,
        fingerprint=ExecutionFingerprint(
            target_id="target-a",
            adapter_type="openai-compatible",
            endpoint_identity="loopback:1234",
            model=ModelIdentity(model_id=model_id),
            runtime=RuntimeIdentity(),
            hardware=HardwareIdentity(device_id="device-a"),
            generation=bundle.suite.generation,
            prompt_template_version=prompt_template_version,
            dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
            evaluator_versions=evaluator_refs,
            benchmark_protocol_version="starter-quality-v1",
            load_profile=LoadProfile(concurrency=1, request_count=23, streaming=False),
        ),
        suite=bundle.suite,
        created_at=now,
        completed_at=now,
        aggregate_scores=sample.scores,
        samples=(sample,),
    )


def _service(
    tmp_path: Path, second_prompt_template: str = "direct-user-v1"
) -> CampaignQueryService:
    bundle = build_general_starter_suite()
    run_store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    first = _run("model-a", score_value=1.0)
    second = _run(
        "model-b",
        score_value=0.5,
        prompt_template_version=second_prompt_template,
    )
    run_store.publish(first)
    run_store.publish(second)

    now = datetime.now(UTC)
    campaign_store = SQLiteCampaignStore(run_store.path)
    campaign_store.save(
        Campaign(
            campaign_id="campaign-a",
            plan_digest="a" * 64,
            use_case_id="general-capability",
            use_case_version="1",
            target_id="target-a",
            suite_id=bundle.suite.suite_id,
            suite_version=bundle.suite.suite_version,
            decision_policy=DecisionPolicyRef(
                policy_id="strict-quality-dominance",
                policy_version="1.0.0",
            ),
            status=CampaignStatus.SUCCEEDED,
            created_at=now,
            updated_at=now,
            completed_at=now,
            entries=(
                CampaignEntry(
                    entry_id="entry-a",
                    candidate_id="candidate-a",
                    model_id="model-a",
                    config_digest="b" * 64,
                    status=CampaignEntryStatus.SUCCEEDED,
                    run_id=first.run_id,
                ),
                CampaignEntry(
                    entry_id="entry-b",
                    candidate_id="candidate-b",
                    model_id="model-b",
                    config_digest="c" * 64,
                    status=CampaignEntryStatus.SUCCEEDED,
                    run_id=second.run_id,
                ),
            ),
        )
    )
    run_queries = UIQueryService(
        run_store,
        suites=(bundle.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
        inspectable_datasets=tuple(bundle.datasets.values()),
        evaluators=tuple(bundle.evaluators.values()),
    )
    return CampaignQueryService(campaign_store, run_queries)


def test_campaign_case_comparison_projects_exact_retained_case_across_candidates(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)

    cases = service.list_cases("campaign-a")
    assert len(cases) == 1
    case = cases[0]
    assert case.candidate_count == 2
    assert case.available_candidate_count == 2
    assert case.case_id == f"{case.task_id}:{case.sample_id}"

    comparison = service.compare_case("campaign-a", case.task_id, case.sample_id)

    assert comparison.state == "ready"
    assert comparison.comparable_candidate_count == 2
    assert comparison.benchmark_case is not None
    assert comparison.reference_run_id == "run-model-a"
    assert [candidate.model_id for candidate in comparison.candidates] == ["model-a", "model-b"]
    assert all(candidate.comparable_to_reference for candidate in comparison.candidates)
    assert all(candidate.evidence is not None for candidate in comparison.candidates)
    assert all(candidate.resources.state == "unavailable" for candidate in comparison.candidates)
    assert all(not candidate.resources.measurements for candidate in comparison.candidates)
    assert all(
        candidate.evidence.response.state == "not_retained"
        for candidate in comparison.candidates
        if candidate.evidence is not None
    )
    assert all(
        candidate.evidence.scores
        for candidate in comparison.candidates
        if candidate.evidence is not None
    )


def test_campaign_case_comparison_explains_incompatible_protocol_without_a_conclusion(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path, second_prompt_template="other-template-v1")
    case = service.list_cases("campaign-a")[0]

    comparison = service.compare_case("campaign-a", case.task_id, case.sample_id)

    assert comparison.state == "not_comparable"
    assert comparison.comparable_candidate_count == 1
    candidate = next(item for item in comparison.candidates if item.model_id == "model-b")
    assert not candidate.comparable_to_reference
    assert candidate.evidence is not None
    assert candidate.resources.state == "unavailable"
    assert [reason.code for reason in candidate.compatibility_reasons] == [
        "prompt_template_mismatch"
    ]