import asyncio
from datetime import UTC, datetime
from pathlib import Path

from performance_lab.application.campaign_jobs import (
    CampaignJobManager,
    CampaignLaunchPlan,
    CampaignRunSpec,
)
from performance_lab.application.evaluation_capacity import EvaluationCapacity
from performance_lab.datasets import build_general_starter_suite
from performance_lab.domain import (
    CampaignStatus,
    DecisionPolicyRef,
    ExecutionFingerprint,
    HardwareIdentity,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    RuntimeIdentity,
)
from performance_lab.run_config import StarterRunConfig
from performance_lab.runner import RunExecutionResult
from performance_lab.storage import SQLiteCampaignStore


def _config(tmp_path: Path, model_id: str) -> StarterRunConfig:
    from performance_lab.domain import EndpointProfile

    return StarterRunConfig(
        target_id="target-a",
        endpoint_identity="loopback:1234",
        endpoint=EndpointProfile(
            profile_id="endpoint-a",
            base_url="http://127.0.0.1:1234/v1",
        ),
        model_id=model_id,
        store_path=tmp_path / "runs.sqlite3",
    )


def _run(config: StarterRunConfig) -> Run:
    bundle = build_general_starter_suite()
    now = datetime.now(UTC)
    return Run(
        run_id=config.run_id or "missing-run-id",
        status=RunStatus.SUCCEEDED,
        fingerprint=ExecutionFingerprint(
            target_id=config.target_id,
            adapter_type="openai-compatible",
            endpoint_identity=config.endpoint_identity,
            model=ModelIdentity(model_id=config.model_id),
            runtime=RuntimeIdentity(),
            hardware=HardwareIdentity(),
            generation=bundle.suite.generation,
            prompt_template_version="direct-user-v1",
            dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
            evaluator_versions=tuple(dict.fromkeys(task.evaluator for task in bundle.suite.tasks)),
            benchmark_protocol_version="starter-quality-v1",
            load_profile=LoadProfile(concurrency=1, request_count=23, streaming=False),
        ),
        suite=bundle.suite,
        created_at=now,
        completed_at=now,
    )


def test_campaign_executes_bounded_run_specs_sequentially_and_persists_terminal_state(
    tmp_path: Path,
) -> None:
    calls: list[str] = []

    async def executor(config: StarterRunConfig, *, progress_sink=None) -> RunExecutionResult:
        calls.append(config.model_id)
        await asyncio.sleep(0)
        return RunExecutionResult(
            run=_run(config),
            store_path=config.store_path,
            bundle_path=config.store_path.parent / "artifact.plab.zip",
        )

    async def exercise() -> None:
        manager = CampaignJobManager(
            SQLiteCampaignStore(tmp_path / "runs.sqlite3"),
            capacity=EvaluationCapacity(),
            executor=executor,
        )
        campaign = await manager.launch(
            CampaignLaunchPlan(
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
                runs=(
                    CampaignRunSpec("candidate-a", "model-a", _config(tmp_path, "model-a")),
                    CampaignRunSpec("candidate-b", "model-b", _config(tmp_path, "model-b")),
                ),
            )
        )
        async for _ in manager.stream(campaign.campaign_id):
            pass
        completed = manager.get(campaign.campaign_id)
        assert completed.status == CampaignStatus.SUCCEEDED
        assert [entry.model_id for entry in completed.entries] == ["model-a", "model-b"]
        assert all(entry.run_id is not None for entry in completed.entries)

    asyncio.run(exercise())
    assert calls == ["model-a", "model-b"]
