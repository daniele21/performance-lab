"""Application query projections for browser-facing read paths."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Protocol

from performance_lab.domain import (
    Capability,
    DatasetSnapshot,
    EndpointProfile,
    EvaluationSuite,
    LoadProfile,
    Measurement,
    MeasurementProvenance,
    Run,
    Score,
    Target,
)
from performance_lab.regression import BaselineBinding, RegressionPolicy
from performance_lab.run_config import LocalLLMServerIdentityConfig, StarterRunConfig
from performance_lab.storage import RunComparisonService

from .endpoint_discovery import endpoint_identity, local_server_root
from .ui_models import (
    BaselineSummaryReadModel,
    ComparisonReadModel,
    CompatibilityReasonReadModel,
    DatasetSummaryReadModel,
    DimensionComparisonReadModel,
    EndpointConnectionInput,
    EvidenceAvailability,
    FrozenExecutionPreviewReadModel,
    IdentitySummary,
    MetricDimension,
    MetricReadModel,
    PolicySummaryReadModel,
    PreflightIssueReadModel,
    RunDetailReadModel,
    RunEvidenceReadModel,
    RunPreflightReadModel,
    RunPreflightRequest,
    RunSummaryReadModel,
    ScenarioKind,
    ScenarioSummaryReadModel,
    SuiteSummaryReadModel,
    TargetSummaryReadModel,
    TestedModelReadModel,
)

STARTER_SUITE_ID = "general-diagnostic-starter"
STARTER_PROMPT_TEMPLATE_VERSION = "direct-user-v1"
STARTER_BENCHMARK_PROTOCOL_VERSION = "starter-quality-v1"
SESSION_CONNECTION_LIMIT = 8


class CompletedRunReader(Protocol):
    def get_completed(self, run_id: str, *, required: bool = True) -> Run | None: ...

    def list_completed(self) -> tuple[Run, ...]: ...


class UIQueryService:
    """Project canonical evidence into stable UI-shaped read models."""

    def __init__(
        self,
        store: CompletedRunReader,
        *,
        targets: tuple[Target, ...] = (),
        endpoint_profiles: tuple[EndpointProfile, ...] = (),
        suites: tuple[EvaluationSuite, ...] = (),
        dataset_snapshots: tuple[DatasetSnapshot, ...] = (),
        baselines: tuple[BaselineBinding, ...] = (),
        policies: tuple[RegressionPolicy, ...] = (),
        starter_run_template: StarterRunConfig | None = None,
    ) -> None:
        self.store = store
        self.targets = targets
        self.endpoint_profiles = endpoint_profiles
        self.suites = suites
        self.dataset_snapshots = dataset_snapshots
        self.baselines = baselines
        self.policies = policies
        self.starter_run_template = starter_run_template
        self.comparisons = RunComparisonService(store)
        self._session_targets: dict[str, Target] = {}
        self._session_endpoint_profiles: dict[str, EndpointProfile] = {}
        self._session_connections: dict[str, EndpointConnectionInput] = {}

    def list_runs(self, *, offset: int = 0, limit: int = 50) -> tuple[RunSummaryReadModel, ...]:
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        runs = sorted(
            self.store.list_completed(),
            key=lambda item: (item.completed_at or item.created_at, item.run_id),
            reverse=True,
        )
        return tuple(_run_summary(run) for run in runs[offset : offset + limit])

    def get_run(self, run_id: str) -> RunDetailReadModel:
        run = self.store.get_completed(run_id)
        if run is None:
            raise LookupError(f"completed run not found: {run_id}")
        return RunDetailReadModel(
            summary=_run_summary(run),
            evidence=RunEvidenceReadModel(
                fingerprint=run.fingerprint,
                dataset_count=len(run.fingerprint.dataset_snapshots),
                evaluator_count=len(run.fingerprint.evaluator_versions),
                sample_count=len(run.samples),
            ),
        )

    def list_tested_models(self) -> tuple[TestedModelReadModel, ...]:
        grouped: dict[str, list[Run]] = {}
        for run in self.store.list_completed():
            grouped.setdefault(_cohort_key(run), []).append(run)

        models: list[TestedModelReadModel] = []
        for cohort_key, runs in grouped.items():
            latest = max(
                runs,
                key=lambda item: (item.completed_at or item.created_at, item.run_id),
            )
            models.append(
                TestedModelReadModel(
                    cohort_key=cohort_key,
                    identity=_identity(latest),
                    run_count=len(runs),
                    latest_run_id=latest.run_id,
                    latest_completed_at=latest.completed_at,
                    latest_metrics=_metrics(latest),
                )
            )
        epoch = datetime.min.replace(tzinfo=UTC)
        return tuple(
            sorted(
                models,
                key=lambda item: (item.latest_completed_at or epoch, item.latest_run_id),
                reverse=True,
            )
        )

    def list_targets(self) -> tuple[TargetSummaryReadModel, ...]:
        targets = (*self.targets, *self._session_targets.values())
        return tuple(
            _target_summary(target) for target in sorted(targets, key=lambda x: x.target_id)
        )

    def register_session_connection(
        self,
        connection: EndpointConnectionInput,
    ) -> TargetSummaryReadModel:
        """Register a bounded process-lifetime target after a successful endpoint probe."""
        digest = sha256(str(connection.base_url).encode("utf-8")).hexdigest()[:12]
        target_id = f"session-{digest}"
        profile_id = f"session-profile-{digest}"
        if (
            target_id not in self._session_targets
            and len(self._session_targets) >= SESSION_CONNECTION_LIMIT
        ):
            oldest_target_id = next(iter(self._session_targets))
            oldest_target = self._session_targets.pop(oldest_target_id)
            self._session_endpoint_profiles.pop(oldest_target.endpoint_profile_id, None)
            self._session_connections.pop(oldest_target_id, None)

        endpoint = EndpointProfile(
            profile_id=profile_id,
            base_url=connection.base_url,
            timeout_seconds=connection.timeout_seconds,
        )
        target = Target(
            target_id=target_id,
            display_name=connection.display_name,
            adapter_type="openai-compatible",
            endpoint_profile_id=profile_id,
            endpoint_identity=endpoint_identity(connection),
            declared_capabilities=(Capability.TEXT_GENERATION,),
        )
        self._session_endpoint_profiles[profile_id] = endpoint
        self._session_targets[target_id] = target
        self._session_connections[target_id] = connection
        return _target_summary(target)

    def list_suites(self) -> tuple[SuiteSummaryReadModel, ...]:
        return tuple(
            _suite_summary(suite)
            for suite in sorted(self.suites, key=lambda item: (item.suite_id, item.suite_version))
        )

    def list_datasets(self) -> tuple[DatasetSummaryReadModel, ...]:
        return tuple(
            DatasetSummaryReadModel.from_snapshot(snapshot)
            for snapshot in sorted(
                self.dataset_snapshots,
                key=lambda item: (item.dataset_id, item.dataset_version, item.content_sha256),
            )
        )

    def list_scenarios(self) -> tuple[ScenarioSummaryReadModel, ...]:
        return (
            ScenarioSummaryReadModel(
                scenario=ScenarioKind.GENERAL_CAPABILITY,
                title="General capability",
                description="Balanced authored diagnostic coverage across quality tasks.",
                supported=True,
                suite_id=STARTER_SUITE_ID,
            ),
            ScenarioSummaryReadModel(
                scenario=ScenarioKind.MY_WORKLOAD,
                title="My workload",
                description="Evaluate user-owned examples against an explicit workload contract.",
                supported=False,
                blocked_reason="Custom workload execution is not wired to the local product yet.",
            ),
            ScenarioSummaryReadModel(
                scenario=ScenarioKind.PERFORMANCE,
                title="Performance",
                description="Focus the run on latency, throughput and resource evidence.",
                supported=False,
                blocked_reason="Dedicated performance scenario presets are not wired yet.",
            ),
            ScenarioSummaryReadModel(
                scenario=ScenarioKind.REGRESSION,
                title="Regression",
                description="Evaluate against an explicit immutable baseline and policy.",
                supported=False,
                blocked_reason="Regression launch configuration is not wired yet.",
            ),
        )

    def preflight(self, request: RunPreflightRequest) -> RunPreflightReadModel:
        issues: list[PreflightIssueReadModel] = []
        if request.scenario != ScenarioKind.GENERAL_CAPABILITY:
            issues.append(
                PreflightIssueReadModel(
                    code="scenario_not_supported",
                    field="scenario",
                    message=f"scenario is not executable yet: {request.scenario.value}",
                )
            )
            return RunPreflightReadModel(can_run=False, issues=tuple(issues))

        targets = (*self.targets, *self._session_targets.values())
        target = next((item for item in targets if item.target_id == request.target_id), None)
        if target is None:
            issues.append(
                PreflightIssueReadModel(
                    code="target_not_found",
                    field="target_id",
                    message=f"target is not registered: {request.target_id}",
                )
            )
            return RunPreflightReadModel(can_run=False, issues=tuple(issues))
        if target.adapter_type != "openai-compatible":
            issues.append(
                PreflightIssueReadModel(
                    code="adapter_not_supported",
                    field="target_id",
                    message=(
                        "starter execution currently requires the openai-compatible adapter; "
                        f"target uses {target.adapter_type}"
                    ),
                )
            )

        endpoint_profiles = (*self.endpoint_profiles, *self._session_endpoint_profiles.values())
        endpoint = next(
            (item for item in endpoint_profiles if item.profile_id == target.endpoint_profile_id),
            None,
        )
        if endpoint is None:
            issues.append(
                PreflightIssueReadModel(
                    code="endpoint_profile_not_found",
                    field="target_id",
                    message=f"endpoint profile is not registered: {target.endpoint_profile_id}",
                )
            )

        suite = next((item for item in self.suites if item.suite_id == STARTER_SUITE_ID), None)
        if suite is None:
            issues.append(
                PreflightIssueReadModel(
                    code="suite_not_found",
                    field="scenario",
                    message=f"required suite is not registered: {STARTER_SUITE_ID}",
                )
            )

        snapshots = {item.dataset_id: item for item in self.dataset_snapshots}
        selected_snapshots: list[DatasetSnapshot] = []
        if suite is not None:
            for dataset_id in dict.fromkeys(task.dataset_snapshot_id for task in suite.tasks):
                snapshot = snapshots.get(dataset_id)
                if snapshot is None:
                    issues.append(
                        PreflightIssueReadModel(
                            code="dataset_not_found",
                            field="scenario",
                            message=f"required dataset snapshot is not registered: {dataset_id}",
                        )
                    )
                else:
                    selected_snapshots.append(snapshot)

        if issues or endpoint is None or suite is None:
            return RunPreflightReadModel(can_run=False, issues=tuple(issues))

        template = (
            self.starter_run_template.model_dump(mode="python")
            if self.starter_run_template is not None
            else {}
        )
        session_connection = self._session_connections.get(target.target_id)
        session_overrides: dict[str, object] = {}
        if session_connection is not None:
            session_overrides["local_llm_server_telemetry"] = None
            session_overrides["local_llm_server_identity"] = (
                LocalLLMServerIdentityConfig(
                    base_url=local_server_root(session_connection),
                    model_id=request.model_id,
                    required=False,
                )
                if session_connection.server_type == "local_llm_server"
                else None
            )

        config = StarterRunConfig.model_validate(
            {
                **template,
                **session_overrides,
                "target_id": target.target_id,
                "endpoint_identity": target.endpoint_identity,
                "endpoint": endpoint,
                "model_id": request.model_id,
                "run_id": None,
                "use_host_telemetry": request.use_host_telemetry,
                "suite_id": "general-diagnostic-starter",
            }
        )
        config_digest = _config_digest(config)
        evaluator_ids = tuple(
            dict.fromkeys(
                f"{task.evaluator.evaluator_id}@{task.evaluator.version}" for task in suite.tasks
            )
        )
        request_count = sum(
            min(snapshots[task.dataset_snapshot_id].sample_count, task.sample_limit)
            if task.sample_limit is not None
            else snapshots[task.dataset_snapshot_id].sample_count
            for task in suite.tasks
        )
        preview = FrozenExecutionPreviewReadModel(
            scenario=request.scenario,
            config=config,
            config_digest=config_digest,
            target=_target_summary(target),
            suite=_suite_summary(suite),
            datasets=tuple(
                DatasetSummaryReadModel.from_snapshot(item) for item in selected_snapshots
            ),
            evaluator_ids=evaluator_ids,
            generation=suite.generation,
            load_profile=LoadProfile(
                concurrency=1,
                request_count=request_count,
                streaming=False,
            ),
            prompt_template_version=STARTER_PROMPT_TEMPLATE_VERSION,
            benchmark_protocol_version=STARTER_BENCHMARK_PROTOCOL_VERSION,
        )
        return RunPreflightReadModel(can_run=True, preview=preview)

    def list_baselines(self) -> tuple[BaselineSummaryReadModel, ...]:
        return tuple(
            BaselineSummaryReadModel(
                baseline_id=baseline.baseline_id,
                run_id=baseline.run_id,
                fingerprint_id=baseline.fingerprint_id,
                selected_at=baseline.selected_at,
                label=baseline.label,
            )
            for baseline in sorted(self.baselines, key=lambda item: item.baseline_id)
        )

    def list_policies(self) -> tuple[PolicySummaryReadModel, ...]:
        return tuple(
            PolicySummaryReadModel(
                policy_id=policy.policy_id,
                policy_version=policy.policy_version,
                rule_count=len(policy.rules),
            )
            for policy in sorted(
                self.policies, key=lambda item: (item.policy_id, item.policy_version)
            )
        )

    def compare(self, baseline_run_id: str, candidate_run_id: str) -> ComparisonReadModel:
        comparison = self.comparisons.compare(baseline_run_id, candidate_run_id)
        return ComparisonReadModel(
            baseline_run_id=comparison.baseline_run_id,
            candidate_run_id=comparison.candidate_run_id,
            identity_differences=comparison.identity_differences,
            dimensions=tuple(
                DimensionComparisonReadModel(
                    dimension=dimension.dimension,
                    comparable=dimension.compatibility.comparable,
                    reasons=tuple(
                        CompatibilityReasonReadModel(
                            code=reason.code.value,
                            field=reason.field,
                            message=reason.message,
                            baseline=reason.baseline,
                            candidate=reason.candidate,
                        )
                        for reason in dimension.compatibility.reasons
                    ),
                    deltas=dimension.deltas if dimension.compatibility.comparable else (),
                    missing_in_baseline=dimension.missing_in_baseline,
                    missing_in_candidate=dimension.missing_in_candidate,
                )
                for dimension in comparison.dimensions
            ),
        )


def _target_summary(target: Target) -> TargetSummaryReadModel:
    return TargetSummaryReadModel(
        target_id=target.target_id,
        display_name=target.display_name,
        adapter_type=target.adapter_type,
        endpoint_profile_id=target.endpoint_profile_id,
        endpoint_identity=target.endpoint_identity,
        capabilities=tuple(capability.value for capability in target.declared_capabilities),
    )


def _suite_summary(suite: EvaluationSuite) -> SuiteSummaryReadModel:
    return SuiteSummaryReadModel(
        suite_id=suite.suite_id,
        suite_version=suite.suite_version,
        task_count=len(suite.tasks),
        task_ids=tuple(task.task_id for task in suite.tasks),
    )


def _config_digest(config: StarterRunConfig) -> str:
    canonical = json.dumps(
        config.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _identity(run: Run) -> IdentitySummary:
    fingerprint = run.fingerprint
    return IdentitySummary(
        model_id=fingerprint.model.model_id,
        revision=fingerprint.model.revision,
        quantization=fingerprint.model.quantization,
        artifact_digest=fingerprint.model.artifact_digest,
        target_id=fingerprint.target_id,
        endpoint_identity=fingerprint.endpoint_identity,
        runtime_name=fingerprint.runtime.name,
        runtime_version=fingerprint.runtime.version,
        hardware_device_id=fingerprint.hardware.device_id,
        hardware_device_class=fingerprint.hardware.device_class,
    )


def _cohort_key(run: Run) -> str:
    payload = {
        "model": run.fingerprint.model.model_dump(mode="json"),
        "runtime": run.fingerprint.runtime.model_dump(mode="json"),
        "hardware": run.fingerprint.hardware.model_dump(mode="json"),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _run_summary(run: Run) -> RunSummaryReadModel:
    return RunSummaryReadModel(
        run_id=run.run_id,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        suite_id=run.suite.suite_id,
        suite_version=run.suite.suite_version,
        fingerprint_id=run.fingerprint.fingerprint_id,
        identity=_identity(run),
        metrics=_metrics(run),
    )


def _metrics(run: Run) -> tuple[MetricReadModel, ...]:
    quality = tuple(
        sorted((_score_metric(score) for score in run.aggregate_scores), key=lambda x: x.metric_id)
    )
    measurements = tuple(
        sorted(
            (_measurement_metric(item) for item in run.aggregate_measurements),
            key=lambda x: (x.dimension.value, x.metric_id),
        )
    )
    return quality + measurements


def _score_metric(score: Score) -> MetricReadModel:
    return MetricReadModel(
        metric_id=f"{score.metric}|{score.evaluator.evaluator_id}@{score.evaluator.version}",
        label=score.metric,
        dimension=MetricDimension.QUALITY,
        availability=EvidenceAvailability.AVAILABLE,
        value=score.value,
        higher_is_better=score.higher_is_better,
        provenance=f"{score.evaluator.evaluator_id}@{score.evaluator.version}",
    )


def _measurement_metric(measurement: Measurement) -> MetricReadModel:
    dimension = (
        MetricDimension.PERFORMANCE
        if measurement.provenance == MeasurementProvenance.CLIENT
        else MetricDimension.RESOURCES
    )
    return MetricReadModel(
        metric_id=(
            f"{measurement.name}|{measurement.provenance.value}|"
            f"{measurement.protocol_version}|{measurement.unit}"
        ),
        label=measurement.name,
        dimension=dimension,
        availability=EvidenceAvailability.AVAILABLE,
        value=measurement.value,
        unit=measurement.unit,
        provenance=measurement.provenance.value,
        protocol_version=measurement.protocol_version,
    )
