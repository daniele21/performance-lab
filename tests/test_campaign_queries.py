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
    EvaluatorRef,
    ExecutionFingerprint,
    HardwareIdentity,
    LoadProfile,
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
    ModelIdentity,
    Run,
    RunStatus,
    RuntimeIdentity,
    Score,
)
from performance_lab.storage import SQLiteCampaignStore, SQLiteRunStore


def _run(
    model_id: str,
    value: float,
    *,
    measurements: tuple[Measurement, ...] = (),
) -> Run:
    bundle = build_general_starter_suite()
    evaluator = EvaluatorRef(evaluator_id="quality", version="1")
    now = datetime.now(UTC)
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
            prompt_template_version="direct-user-v1",
            dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
            evaluator_versions=(evaluator,),
            benchmark_protocol_version="starter-quality-v1",
            load_profile=LoadProfile(concurrency=1, request_count=23, streaming=False),
        ),
        suite=bundle.suite,
        created_at=now,
        completed_at=now,
        aggregate_scores=(
            Score(
                metric="quality",
                value=value,
                evaluator=evaluator,
                higher_is_better=True,
            ),
        ),
        aggregate_measurements=measurements,
    )


def _save_campaign(store: SQLiteCampaignStore, first: Run, second: Run) -> None:
    now = datetime.now(UTC)
    store.save(
        Campaign(
            campaign_id="campaign-a",
            plan_digest="a" * 64,
            use_case_id="general-capability",
            use_case_version="1",
            target_id="target-a",
            suite_id="general-diagnostic-starter",
            suite_version="2026-08-15-v1",
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


def test_campaign_results_show_policy_before_a_strict_dominance_recommendation(
    tmp_path: Path,
) -> None:
    run_store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    first = _run("model-a", 1.0)
    second = _run("model-b", 0.5)
    run_store.publish(first)
    run_store.publish(second)

    campaign_store = SQLiteCampaignStore(run_store.path)
    _save_campaign(campaign_store, first, second)
    run_queries = UIQueryService(run_store)

    result = CampaignQueryService(campaign_store, run_queries).get("campaign-a")

    assert result.results.state == "ready"
    assert result.results.decision_policy.policy_id == "strict-quality-dominance"
    capability = next(
        item for item in result.results.compatibility if item.dimension.value == "capability"
    )
    assert capability.comparable
    assert capability.evidence_available
    assert capability.evidence_note is None
    assert result.results.recommendation is not None
    assert result.results.recommendation.model_id == "model-a"


def test_campaign_does_not_promote_context_telemetry_to_resource_evidence(
    tmp_path: Path,
) -> None:
    host_context = Measurement(
        name="process_peak_rss_bytes",
        value=1024.0,
        unit="bytes",
        scope=MeasurementScope.RUN,
        provenance=MeasurementProvenance.HOST,
        protocol_version="host-stdlib-v1",
    )
    runtime_context = Measurement(
        name="peak_active_requests",
        value=1.0,
        unit="count",
        scope=MeasurementScope.RUN,
        provenance=MeasurementProvenance.RUNTIME,
        protocol_version="local-llm-server-status-v1",
    )
    run_store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    first = _run("model-a", 1.0, measurements=(host_context, runtime_context))
    second = _run("model-b", 0.5, measurements=(host_context, runtime_context))
    run_store.publish(first)
    run_store.publish(second)

    campaign_store = SQLiteCampaignStore(run_store.path)
    _save_campaign(campaign_store, first, second)

    result = CampaignQueryService(campaign_store, UIQueryService(run_store)).get("campaign-a")
    resource = next(
        item for item in result.results.compatibility if item.dimension.value == "resource"
    )

    assert resource.comparable
    assert not resource.evidence_available
    assert resource.evidence_note is not None
    assert "Contextual host/runtime telemetry is retained" in resource.evidence_note
