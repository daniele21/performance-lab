import asyncio
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from performance_lab.application import RunPreflightRequest, UIQueryService
from performance_lab.application.run_jobs import (
    FrozenConfigMismatchError,
    RunJobCapacityError,
    RunJobManager,
    RunJobState,
    starter_run_config_digest,
)
from performance_lab.datasets import build_general_starter_suite
from performance_lab.domain import (
    DatasetSnapshot,
    EndpointProfile,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    Target,
    TaskSpec,
)
from performance_lab.engine import ProgressEvent, ProgressPhase
from performance_lab.run_config import StarterRunConfig
from performance_lab.runner import RunExecutionResult
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app


def _endpoint() -> EndpointProfile:
    return EndpointProfile(
        profile_id="local",
        base_url="http://127.0.0.1:1234/v1",
        timeout_seconds=5,
    )


def _config(tmp_path) -> StarterRunConfig:
    return StarterRunConfig(
        target_id="local-target",
        endpoint_identity="loopback",
        endpoint=_endpoint(),
        model_id="model-a",
        store_path=tmp_path / "runs.sqlite3",
    )


def _dataset() -> DatasetSnapshot:
    return DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="builtin",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )


def _suite() -> EvaluationSuite:
    evaluator = EvaluatorRef(evaluator_id="exact-match", version="1")
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
        generation=GenerationConfig(max_output_tokens=16, temperature=0),
    )


def _run(status: RunStatus, *, run_id: str = "run-a") -> Run:
    suite = _suite()
    evaluator = suite.tasks[0].evaluator
    now = datetime.now(UTC)
    return Run(
        run_id=run_id,
        status=status,
        fingerprint=ExecutionFingerprint(
            target_id="local-target",
            adapter_type="openai-compatible",
            endpoint_identity="loopback",
            model=ModelIdentity(model_id="model-a"),
            generation=suite.generation,
            prompt_template_version="direct-user-v1",
            dataset_snapshots=(_dataset(),),
            evaluator_versions=(evaluator,),
            benchmark_protocol_version="starter-quality-v1",
            load_profile=LoadProfile(concurrency=1, request_count=1, streaming=False),
        ),
        suite=suite,
        created_at=now,
        completed_at=now if status != RunStatus.RUNNING else None,
    )


class ControlledExecutor:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.calls = 0

    async def __call__(self, config, *, progress_sink=None) -> RunExecutionResult:
        self.calls += 1
        run_id = f"run-{self.calls}"
        if progress_sink is not None:
            progress_sink(
                ProgressEvent(
                    phase=ProgressPhase.RUN_STARTED,
                    run_id=run_id,
                    completed_samples=0,
                    total_samples=1,
                )
            )
        self.started.set()
        await self.release.wait()
        run = _run(RunStatus.SUCCEEDED, run_id=run_id)
        return RunExecutionResult(
            run=run,
            store_path=config.store_path,
            bundle_path=config.store_path.parent / "artifacts" / f"{run_id}.plab.zip",
        )


def test_manager_rejects_capacity_then_allows_new_job_after_cancel(tmp_path) -> None:
    async def scenario() -> None:
        executor = ControlledExecutor()
        manager = RunJobManager(executor=executor, poll_interval_seconds=0.001)
        config = _config(tmp_path)
        digest = starter_run_config_digest(config)

        first = await manager.launch(config, config_digest=digest)
        await executor.started.wait()
        with pytest.raises(RunJobCapacityError):
            await manager.launch(config, config_digest=digest)

        cancelled = await manager.cancel(first.job_id)
        assert cancelled.state == RunJobState.CANCELLED

        second = await manager.launch(config, config_digest=digest)
        executor.release.set()
        completed = await manager.wait(second.job_id)
        assert completed.state == RunJobState.SUCCEEDED
        assert completed.run_id == "run-2"

    asyncio.run(scenario())


def test_manager_rejects_config_that_differs_from_reviewed_digest(tmp_path) -> None:
    async def scenario() -> None:
        manager = RunJobManager(executor=ControlledExecutor())
        config = _config(tmp_path)
        with pytest.raises(FrozenConfigMismatchError):
            await manager.launch(config, config_digest="0" * 64)

    asyncio.run(scenario())


def test_progress_stream_is_revision_based_and_bounded(tmp_path) -> None:
    async def scenario() -> None:
        executor = ControlledExecutor()
        manager = RunJobManager(executor=executor, poll_interval_seconds=0.001)
        config = _config(tmp_path)
        job = await manager.launch(config, config_digest=starter_run_config_digest(config))

        stream = manager.stream(job.job_id)
        initial = await anext(stream)
        assert initial.revision == 0
        await executor.started.wait()
        running = await anext(stream)
        assert running.revision > initial.revision
        assert running.state == RunJobState.RUNNING
        assert running.total_samples == 1

        executor.release.set()
        terminal = await manager.wait(job.job_id)
        assert terminal.state == RunJobState.SUCCEEDED
        await stream.aclose()

    asyncio.run(scenario())


def test_retained_working_run_is_recovered_as_interrupted_not_completed(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    working = _run(RunStatus.RUNNING, run_id="run-working")
    store.save_working(working)

    manager = RunJobManager(recovered_runs=store.list_working())
    jobs = manager.list_jobs()

    assert len(jobs) == 1
    assert jobs[0].state == RunJobState.INTERRUPTED
    assert jobs[0].run_id == "run-working"
    assert store.get_completed("run-working", required=False) is None
    assert store.get("run-working") == working


def test_http_launch_rechecks_server_preflight_and_enforces_capacity(tmp_path) -> None:
    bundle = build_general_starter_suite()
    endpoint = _endpoint()
    target = Target(
        target_id="local-target",
        display_name="Local target",
        adapter_type="openai-compatible",
        endpoint_profile_id=endpoint.profile_id,
        endpoint_identity="loopback",
    )
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    queries = UIQueryService(
        store,
        targets=(target,),
        endpoint_profiles=(endpoint,),
        suites=(bundle.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
    )
    preflight_request = RunPreflightRequest(
        target_id=target.target_id,
        model_id="model-a",
    )
    prepared = queries.preflight(preflight_request)
    assert prepared.preview is not None

    manager = RunJobManager(executor=ControlledExecutor(), poll_interval_seconds=0.001)
    with TestClient(create_ui_app(queries, run_jobs=manager)) as client:
        payload = {
            "preflight": preflight_request.model_dump(mode="json"),
            "config_digest": prepared.preview.config_digest,
        }
        first = client.post("/api/v1/run-jobs", json=payload)
        assert first.status_code == 202
        job_id = first.json()["job_id"]

        second = client.post("/api/v1/run-jobs", json=payload)
        assert second.status_code == 409

        stale = {**payload, "config_digest": "0" * 64}
        assert client.post("/api/v1/run-jobs", json=stale).status_code == 409

        cancelled = client.post(f"/api/v1/run-jobs/{job_id}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["state"] == "cancelled"
        assert client.get(f"/api/v1/run-jobs/{job_id}").json()["state"] == "cancelled"
        assert client.get("/api/v1/run-jobs/missing").status_code == 404
