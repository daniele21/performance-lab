"""Executable wiring for native Performance Lab evaluation suites."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from performance_lab.adapters import OpenAICompatibleAdapter
from performance_lab.datasets import (
    MaterializedDataset,
    available_workload_packs,
    build_general_starter_suite,
    build_workload_pack,
)
from performance_lab.domain import (
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    HardwareIdentity,
    LoadProfile,
    ModelIdentity,
    Run,
    RuntimeIdentity,
    TelemetryDescriptor,
    TelemetryLevel,
)
from performance_lab.engine import EvaluationOrchestrator, ProgressEvent
from performance_lab.integrations import (
    LocalLLMServerIdentityClient,
    LocalLLMServerIdentityError,
)
from performance_lab.plugins import Evaluator, TelemetryCollector
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


@dataclass(frozen=True, slots=True)
class _ResolvedExecutionIdentity:
    model: ModelIdentity
    runtime: RuntimeIdentity
    hardware: HardwareIdentity


@dataclass(frozen=True, slots=True)
class _ExecutionBundle:
    suite: EvaluationSuite
    datasets: Mapping[str, MaterializedDataset]
    evaluators: Mapping[str, Evaluator]
    benchmark_protocol_version: str


async def execute_starter_run(
    config: StarterRunConfig,
    *,
    progress_sink: Callable[[ProgressEvent], None] | None = None,
) -> RunExecutionResult:
    """Wire endpoint -> frozen native suite -> orchestrator -> immutable local evidence.

    The historical function name remains for compatibility. ``suite_id``/``suite_version`` now
    select either the general diagnostic suite or a registered versioned workload pack.
    """

    bundle = _resolve_execution_bundle(config)
    adapter = OpenAICompatibleAdapter(config.endpoint, model=config.model_id)
    try:
        probe = await adapter.probe()
        if not probe.healthy:
            error_code = probe.metadata.get("error_code", "unknown")
            raise RunExecutionError(f"endpoint probe failed: {error_code}")

        identity = await _resolve_execution_identity(config)
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
            model=identity.model,
            runtime=identity.runtime,
            hardware=identity.hardware,
            generation=bundle.suite.generation,
            prompt_template_version="direct-user-v1",
            dataset_snapshots=snapshots,
            evaluator_versions=evaluator_versions,
            benchmark_protocol_version=bundle.benchmark_protocol_version,
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
        return RunExecutionResult(run=run, store_path=config.store_path, bundle_path=bundle_path)
    finally:
        await adapter.aclose()


def _resolve_execution_bundle(config: StarterRunConfig) -> _ExecutionBundle:
    if config.suite_id == "general-diagnostic-starter":
        starter_bundle = build_general_starter_suite()
        if (
            config.suite_version is not None
            and config.suite_version != starter_bundle.suite.suite_version
        ):
            raise RunExecutionError(
                f"unsupported suite version: {config.suite_id}@{config.suite_version}"
            )
        return _ExecutionBundle(
            suite=starter_bundle.suite,
            datasets=starter_bundle.datasets,
            evaluators=starter_bundle.evaluators,
            benchmark_protocol_version="starter-quality-v1",
        )

    definition = next(
        (item for item in available_workload_packs() if item.suite_id == config.suite_id),
        None,
    )
    if definition is None:
        raise RunExecutionError(f"unsupported suite: {config.suite_id}")
    try:
        workload_bundle = build_workload_pack(definition.pack_id, version=config.suite_version)
    except KeyError as exc:
        raise RunExecutionError(
            f"unsupported suite version: {config.suite_id}@{config.suite_version}"
        ) from exc
    return _ExecutionBundle(
        suite=workload_bundle.suite,
        datasets=workload_bundle.datasets,
        evaluators=workload_bundle.evaluators,
        benchmark_protocol_version="workload-quality-v1",
    )


async def _resolve_execution_identity(config: StarterRunConfig) -> _ResolvedExecutionIdentity:
    fallback = _ResolvedExecutionIdentity(
        model=ModelIdentity(model_id=config.model_id),
        runtime=RuntimeIdentity(),
        hardware=config.hardware,
    )
    identity_config = config.local_llm_server_identity
    required = False
    if identity_config is not None:
        base_url = str(identity_config.base_url)
        model_id = identity_config.model_id or config.model_id
        timeout_seconds = identity_config.timeout_seconds
        required = identity_config.required
    elif config.local_llm_server_telemetry is not None:
        telemetry_config = config.local_llm_server_telemetry
        base_url = str(telemetry_config.base_url)
        model_id = telemetry_config.model_id or config.model_id
        timeout_seconds = telemetry_config.timeout_seconds
    else:
        return fallback

    try:
        discovered = await LocalLLMServerIdentityClient(
            base_url,
            timeout_seconds=timeout_seconds,
        ).resolve(model_id=model_id)
    except LocalLLMServerIdentityError as exc:
        if required:
            raise RunExecutionError("required local-llm-server identity is unavailable") from exc
        return fallback

    return _ResolvedExecutionIdentity(
        model=discovered.model,
        runtime=discovered.runtime,
        hardware=_merge_hardware_identity(config.hardware, discovered.hardware),
    )


def _merge_hardware_identity(
    configured: HardwareIdentity,
    discovered: HardwareIdentity,
) -> HardwareIdentity:
    values: dict[str, object | None] = {}
    for field_name in HardwareIdentity.model_fields:
        configured_value = getattr(configured, field_name)
        discovered_value = getattr(discovered, field_name)
        if (
            configured_value is not None
            and discovered_value is not None
            and configured_value != discovered_value
        ):
            raise RunExecutionError(
                f"configured hardware conflicts with local-llm-server identity: {field_name}"
            )
        values[field_name] = discovered_value if discovered_value is not None else configured_value
    return HardwareIdentity.model_validate(values)


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
            raise RunExecutionError("suite contains an invalid evaluator reference")
        key = (evaluator.evaluator_id, evaluator.version)
        if key not in seen:
            refs.append(evaluator)
            seen.add(key)
    return tuple(refs)
