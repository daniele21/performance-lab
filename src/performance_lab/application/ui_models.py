"""Stable UI-shaped read models.

These models are projections for the local browser product. They deliberately reference
canonical domain/storage values instead of redefining benchmark or compatibility semantics.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from ipaddress import ip_address
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from performance_lab.domain import (
    ComparisonDimension,
    DatasetSnapshot,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    RunStatus,
)
from performance_lab.run_config import StarterRunConfig
from performance_lab.storage import IdentityDifference, MetricDelta

UI_READ_MODEL_VERSION: Literal[1] = 1


class UIModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    api_version: Literal["v1"] = "v1"
    read_model_version: Literal[1] = UI_READ_MODEL_VERSION


class EvidenceAvailability(StrEnum):
    AVAILABLE = "available"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    NOT_EVALUATED = "not_evaluated"


class MetricDimension(StrEnum):
    QUALITY = "quality"
    PERFORMANCE = "performance"
    RESOURCES = "resources"


class ScenarioKind(StrEnum):
    GENERAL_CAPABILITY = "general_capability"
    MY_WORKLOAD = "my_workload"
    PERFORMANCE = "performance"
    REGRESSION = "regression"


class MetricReadModel(UIModel):
    metric_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    dimension: MetricDimension
    availability: EvidenceAvailability
    value: float | None = None
    unit: str | None = None
    higher_is_better: bool | None = None
    provenance: str | None = None
    protocol_version: str | None = None


class IdentitySummary(UIModel):
    model_id: str = Field(min_length=1)
    revision: str | None = None
    quantization: str | None = None
    artifact_digest: str | None = None
    target_id: str = Field(min_length=1)
    endpoint_identity: str = Field(min_length=1)
    runtime_name: str | None = None
    runtime_version: str | None = None
    hardware_device_id: str | None = None
    hardware_device_class: str | None = None


class RunSummaryReadModel(UIModel):
    run_id: str = Field(min_length=1)
    status: RunStatus
    created_at: datetime
    completed_at: datetime | None = None
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    fingerprint_id: str = Field(min_length=1)
    identity: IdentitySummary
    metrics: tuple[MetricReadModel, ...] = ()


class RunEvidenceReadModel(UIModel):
    fingerprint: ExecutionFingerprint
    dataset_count: int = Field(ge=0)
    evaluator_count: int = Field(ge=0)
    sample_count: int = Field(ge=0)


class RunDetailReadModel(UIModel):
    summary: RunSummaryReadModel
    evidence: RunEvidenceReadModel


class TestedModelReadModel(UIModel):
    cohort_key: str = Field(min_length=1)
    identity: IdentitySummary
    run_count: int = Field(gt=0)
    latest_run_id: str = Field(min_length=1)
    latest_completed_at: datetime | None = None
    latest_metrics: tuple[MetricReadModel, ...] = ()


class TargetSummaryReadModel(UIModel):
    target_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    adapter_type: str = Field(min_length=1)
    endpoint_profile_id: str = Field(min_length=1)
    endpoint_identity: str = Field(min_length=1)
    capabilities: tuple[str, ...] = ()


class EndpointConnectionInput(BaseModel):
    """Ephemeral user-entered local inference connection.

    The browser may request a probe, but the Performance Lab backend owns the network call.
    The first UI slice is deliberately loopback-only so a local browser cannot turn the
    product into a general server-side request proxy.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    display_name: str = Field(default="Local model server", min_length=1, max_length=80)
    base_url: HttpUrl
    server_type: Literal["openai_compatible", "local_llm_server"] = "local_llm_server"
    timeout_seconds: float = Field(default=5.0, gt=0, le=120)

    @model_validator(mode="after")
    def require_loopback_host(self) -> EndpointConnectionInput:
        host = self.base_url.host
        if host is None:
            raise ValueError("base_url must include a host")
        if host.lower() == "localhost":
            return self
        try:
            address = ip_address(host)
        except ValueError as exc:
            raise ValueError("UI endpoint discovery is currently limited to localhost") from exc
        if not address.is_loopback:
            raise ValueError("UI endpoint discovery is currently limited to loopback addresses")
        return self


class CapabilitySupportReadModel(UIModel):
    name: str = Field(min_length=1)
    state: Literal["supported", "unsupported", "unknown"]
    source: Literal["declared", "observed", "none"]
    detail: str | None = None


class GenerationParameterDomainReadModel(UIModel):
    """Validated projection of a backend-declared request-generation domain."""

    name: str = Field(min_length=1)
    kind: Literal["float", "integer", "boolean"]
    scope: Literal["request_generation"] = "request_generation"
    source: Literal["local_llm_server"] = "local_llm_server"
    provenance: Literal["registry_declared"] = "registry_declared"
    minimum: int | float | None = None
    maximum: int | float | None = None
    step: int | float | None = None
    values: tuple[bool, ...] = ()

    @model_validator(mode="after")
    def validate_domain_shape(self) -> GenerationParameterDomainReadModel:
        if self.kind == "boolean":
            if self.minimum is not None or self.maximum is not None or self.step is not None:
                raise ValueError("boolean generation domains cannot declare numeric bounds")
            if len(self.values) != 2 or set(self.values) != {False, True}:
                raise ValueError("boolean generation domains must contain false and true")
            return self

        if self.values:
            raise ValueError("numeric generation domains cannot declare boolean values")
        if self.minimum is None or self.maximum is None:
            raise ValueError("numeric generation domains require minimum and maximum")
        if isinstance(self.minimum, bool) or isinstance(self.maximum, bool):
            raise ValueError("numeric generation domains require numeric bounds")
        if self.minimum >= self.maximum:
            raise ValueError("numeric generation domains require minimum < maximum")
        if self.kind == "integer" and (
            not isinstance(self.minimum, int)
            or not isinstance(self.maximum, int)
            or isinstance(self.minimum, bool)
            or isinstance(self.maximum, bool)
        ):
            raise ValueError("integer generation domains require integer bounds")
        if self.step is not None:
            if (
                isinstance(self.step, bool)
                or self.step <= 0
                or self.step > self.maximum - self.minimum
            ):
                raise ValueError("generation domain step must be positive and within the span")
            if self.kind == "integer" and not isinstance(self.step, int):
                raise ValueError("integer generation domains require an integer step")
        return self


class RuntimeParameterReadModel(UIModel):
    name: str = Field(min_length=1)
    scope: Literal["runtime_load"] = "runtime_load"
    current_value: object | None = None
    editable: Literal[False] = False
    provenance: Literal["local_llm_server"] = "local_llm_server"


class DiscoveredModelReadModel(UIModel):
    model_id: str = Field(min_length=1)
    runtime_parameters: tuple[RuntimeParameterReadModel, ...] = ()
    generation_parameter_domains: tuple[GenerationParameterDomainReadModel, ...] = ()


class EndpointProbeReadModel(UIModel):
    healthy: bool
    endpoint_identity: str = Field(min_length=1)
    target: TargetSummaryReadModel | None = None
    models: tuple[DiscoveredModelReadModel, ...] = ()
    capabilities: tuple[CapabilitySupportReadModel, ...] = ()
    supported_generation_parameters: tuple[str, ...] = ()
    warning: str | None = None


class SuiteSummaryReadModel(UIModel):
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    task_count: int = Field(gt=0)
    task_ids: tuple[str, ...]


class DatasetSummaryReadModel(UIModel):
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    source: str = Field(min_length=1)
    split: str = Field(min_length=1)
    sample_count: int = Field(gt=0)
    selection_policy: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def from_snapshot(cls, snapshot: DatasetSnapshot) -> DatasetSummaryReadModel:
        return cls(
            dataset_id=snapshot.dataset_id,
            dataset_version=snapshot.dataset_version,
            source=snapshot.source,
            split=snapshot.split,
            sample_count=snapshot.sample_count,
            selection_policy=snapshot.selection_policy,
            content_sha256=snapshot.content_sha256,
        )


class EvaluatorDefinitionReadModel(UIModel):
    evaluator_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    evaluator_type: str = Field(min_length=1)
    deterministic: bool | None = None
    explanation_supported: bool | None = None
    rule_summary: str | None = None
    configuration: dict[str, object] = Field(default_factory=dict)


class BenchmarkTaskReadModel(UIModel):
    task_id: str = Field(min_length=1)
    dataset_snapshot_id: str = Field(min_length=1)
    dataset: DatasetSummaryReadModel | None = None
    evaluator: EvaluatorDefinitionReadModel
    metric_names: tuple[str, ...]
    sample_limit: int | None = Field(default=None, gt=0)
    case_count: int | None = Field(default=None, ge=0)
    case_content_available: bool = False


class BenchmarkCaseReadModel(UIModel):
    case_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    input: object
    expected: object
    evaluator_id: str = Field(min_length=1)
    evaluator_version: str = Field(min_length=1)
    metric_names: tuple[str, ...]


class BenchmarkDetailReadModel(UIModel):
    summary: SuiteSummaryReadModel
    generation: GenerationConfig
    tasks: tuple[BenchmarkTaskReadModel, ...]
    cases: tuple[BenchmarkCaseReadModel, ...]
    definition_issues: tuple[str, ...] = ()


class ScenarioSummaryReadModel(UIModel):
    scenario: ScenarioKind
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    supported: bool
    blocked_reason: str | None = None
    suite_id: str | None = None


class RunPreflightRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    target_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    scenario: ScenarioKind = ScenarioKind.GENERAL_CAPABILITY
    use_host_telemetry: bool = False


class PreflightIssueReadModel(UIModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    field: str | None = None


class FrozenExecutionPreviewReadModel(UIModel):
    scenario: ScenarioKind
    config: StarterRunConfig
    config_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    target: TargetSummaryReadModel
    suite: SuiteSummaryReadModel
    datasets: tuple[DatasetSummaryReadModel, ...]
    evaluator_ids: tuple[str, ...]
    generation: GenerationConfig
    load_profile: LoadProfile
    prompt_template_version: str = Field(min_length=1)
    benchmark_protocol_version: str = Field(min_length=1)
    identity_resolution: Literal["resolved_at_launch"] = "resolved_at_launch"


class RunPreflightReadModel(UIModel):
    can_run: bool
    issues: tuple[PreflightIssueReadModel, ...] = ()
    preview: FrozenExecutionPreviewReadModel | None = None


class BaselineSummaryReadModel(UIModel):
    baseline_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    fingerprint_id: str = Field(min_length=1)
    selected_at: datetime
    label: str | None = None


class PolicySummaryReadModel(UIModel):
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    rule_count: int = Field(gt=0)


class CompatibilityReasonReadModel(UIModel):
    code: str = Field(min_length=1)
    field: str = Field(min_length=1)
    message: str = Field(min_length=1)
    baseline: object | None = None
    candidate: object | None = None


class DimensionComparisonReadModel(UIModel):
    dimension: ComparisonDimension
    comparable: bool
    reasons: tuple[CompatibilityReasonReadModel, ...] = ()
    deltas: tuple[MetricDelta, ...] = ()
    missing_in_baseline: tuple[str, ...] = ()
    missing_in_candidate: tuple[str, ...] = ()


class ComparisonReadModel(UIModel):
    baseline_run_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    identity_differences: tuple[IdentityDifference, ...]
    dimensions: tuple[DimensionComparisonReadModel, ...]
