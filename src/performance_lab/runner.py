"""Executable wiring for the first complete starter-suite evaluation path."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from performance_lab.adapters import OpenAICompatibleAdapter
from performance_lab.datasets import build_general_starter_suite
from performance_lab.domain import (
    EvaluatorRef,
    ExecutionFingerprint,
    LoadProfile,
    ModelIdentity,
    Run,
    TelemetryDescriptor,
    TelemetryLevel,
)
from performance_lab.engine import EvaluationOrchestrator, ProgressEvent
from performance_lab.plugins import TelemetryCollector
from performance_lab.run_config import StarterRunConfig
from performance_lab.storage import SQLiteRunStore
from performance_lab.telemetry import (
    LocalLLMServerStatusCollector,
    PortableHostCollector,
    TelemetrySession,
)


class RunExecutionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RunExecutionResult:
    run: Run
    store_path: Path
    bundle_path: Path


async def execute_starter_run(
    config: StarterRunConfig,
    *,
    progress_sink: Callable[[ProgressEvent], None] | None = None,
) -> RunExecutionResult:
    """Wire endpoint -> frozen starter suite -> orchestrator -> immutable local evidence."""

    bundle = build_general_starter_suite()
    adapter = OpenAICompatibleAdapter(config.endpoint, model=config.model_id)
    try:
        probe = await adapter.probe()
        if not probe.healthy:
            error_code = probe.metadata.get("error_code", "unknown")
            raise RunExecutionError(f"endpoint probe failed: {error_code}")

        telemetry_descriptor, telemetry_session = _build_telemetry(config)

        evaluator_versions = _unique_evaluators(bundle.suite.tasks)
        snapshots = tuple(
            bundle.datasets[dataset_id].snapshot for dataset_id in sorted(bundle.datasets)
        )
        total_samples = sum(
            min(len(bundle.datasets[task.dataset_snapshot_id].records), task.sample_limit)
            if task.sample_limit is not None
            else len(bundle.datasets[task.dataset_snapshot_id].records)
            for task in bundle.suite.tasks
        )
        fingerprint = ExecutionFingerprint(
            target_id=config.target_id,
            adapter_type=adapter.adapter_id,
            endpoint_identity=config.endpoint_identity,
            model=ModelIdentity(model_id=config.model_id),
            hardware=config.hardware,
            generation=bundle.suite.generation,
            prompt_template_version="direct-user-v1",
            dataset_snapshots=snapshots,
            evaluator_versions=evaluator_versions,
            benchmark_protocol_version="starter-quality-v1",
            load_profile=LoadProfile(
                concurrency=1,
                request_count=total_samples,
                streaming=False,
            ),
            telemetry=telemetry_descriptor,
        )
        run_id = config.run_id or f"run-{uuid4()}"
        store = SQLiteRunStore(config.store_path)
        orchestrator = EvaluationOrchestrator(
            adapter,
            bundle.evaluators,
            telemetry=telemetry_session,
            run_sink=store,
            progress_sink=progress_sink,
        )
        run = await orchestrator.run(
            run_id=run_id,
            fingerprint=fingerprint,
            suite=bundle.suite,
            datasets=bundle.datasets,
        )
        bundle_path = config.store_path.parent / "artifacts" / f"{run_id}.plab.zip"
        store.export_bundle(run_id, bundle_path)
        return RunExecutionResult(
            run=run,
            store_path=config.store_path,
            bundle_path=bundle_path,
        )
    finally:
        await adapter.aclose()


def _build_telemetry(
    config: StarterRunConfig,
) -> tuple[TelemetryDescriptor, TelemetrySession | None]:
    collectors: list[TelemetryCollector] = []
    if config.use_host_telemetry:
        collectors.append(PortableHostCollector())
    if config.local_llm_server_telemetry is not None:
        runtime = config.local_llm_server_telemetry
        collectors.append(
            LocalLLMServerStatusCollector(
                str(runtime.base_url),
                model_id=runtime.model_id or config.model_id,
                sample_interval_seconds=runtime.sample_interval_seconds,
                timeout_seconds=runtime.timeout_seconds,
            )
        )
    if not collectors:
        return TelemetryDescriptor(), None

    has_runtime_collector = config.local_llm_server_telemetry is not None
    level = TelemetryLevel.INSTRUMENTED if has_runtime_collector else TelemetryLevel.HOST
    protocol_version = (
        collectors[0].protocol_version if len(collectors) == 1 else "telemetry-session-v1"
    )
    descriptor = TelemetryDescriptor(
        level=level,
        protocol_version=protocol_version,
        collectors=tuple(collector.collector_id for collector in collectors),
    )
    return descriptor, TelemetrySession(collectors)


def _unique_evaluators(tasks: tuple[object, ...]) -> tuple[EvaluatorRef, ...]:
    refs: list[EvaluatorRef] = []
    seen: set[tuple[str, str]] = set()
    for task in tasks:
        evaluator = getattr(task, "evaluator", None)
        if not isinstance(evaluator, EvaluatorRef):
            raise RunExecutionError("starter suite contains an invalid evaluator reference")
        key = (evaluator.evaluator_id, evaluator.version)
        if key not in seen:
            refs.append(evaluator)
            seen.add(key)
    return tuple(refs)
