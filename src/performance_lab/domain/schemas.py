"""Canonical immutable domain schemas for AI Performance Lab.

The domain layer deliberately contains no transport, database, CLI, UI, or model-runtime
dependencies.  `None` means "unknown / not observed" for optional identity fields; known
empty strings are rejected by validation.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

SCHEMA_VERSION: Literal[1] = 1
NonEmptyStr = Annotated[str, Field(min_length=1)]


class FrozenModel(BaseModel):
    """Base for immutable, strict, serializable domain values."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class VersionedModel(FrozenModel):
    """Base for persisted/exported values using the current schema version."""

    schema_version: Literal[1] = SCHEMA_VERSION

    def canonical_json(self) -> str:
        """Return deterministic JSON suitable for hashing and fixture comparison."""
        return json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    def content_digest(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


class Capability(StrEnum):
    TEXT_GENERATION = "text_generation"
    STREAMING = "streaming"
    STRUCTURED_OUTPUT = "structured_output"
    TOKEN_USAGE = "token_usage"


class AuthStrategy(StrEnum):
    NONE = "none"
    BEARER_ENV = "bearer_env"
    API_KEY_ENV = "api_key_env"
    CUSTOM_HEADER_ENV = "custom_header_env"


class AuthConfig(FrozenModel):
    strategy: AuthStrategy = AuthStrategy.NONE
    credential_env: NonEmptyStr | None = None
    header_name: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_auth_shape(self) -> AuthConfig:
        if self.strategy == AuthStrategy.NONE:
            if self.credential_env is not None or self.header_name is not None:
                raise ValueError("auth strategy 'none' cannot reference credentials")
            return self
        if self.credential_env is None:
            raise ValueError("credential_env is required for non-none auth strategies")
        if self.strategy == AuthStrategy.CUSTOM_HEADER_ENV and self.header_name is None:
            raise ValueError("header_name is required for custom_header_env")
        if self.strategy != AuthStrategy.CUSTOM_HEADER_ENV and self.header_name is not None:
            raise ValueError("header_name is only valid for custom_header_env")
        return self


class EndpointProfile(VersionedModel):
    """Connection configuration.

    Raw credentials are intentionally not representable.  `credential_env` stores only
    the name of an environment variable resolved at execution time.
    """

    profile_id: NonEmptyStr
    base_url: HttpUrl
    auth: AuthConfig = AuthConfig()
    model_selector: NonEmptyStr | None = None
    timeout_seconds: float = Field(default=120.0, gt=0, le=3600)


class Target(VersionedModel):
    target_id: NonEmptyStr
    display_name: NonEmptyStr
    adapter_type: NonEmptyStr
    endpoint_profile_id: NonEmptyStr
    endpoint_identity: NonEmptyStr
    declared_capabilities: tuple[Capability, ...] = ()

    @field_validator("declared_capabilities")
    @classmethod
    def unique_capabilities(cls, value: tuple[Capability, ...]) -> tuple[Capability, ...]:
        if len(value) != len(set(value)):
            raise ValueError("declared_capabilities must be unique")
        return value


class ModelIdentity(FrozenModel):
    model_id: NonEmptyStr
    revision: NonEmptyStr | None = None
    artifact_digest: NonEmptyStr | None = None
    quantization: NonEmptyStr | None = None


class RuntimeIdentity(FrozenModel):
    name: NonEmptyStr | None = None
    version: NonEmptyStr | None = None


class HardwareIdentity(FrozenModel):
    device_id: NonEmptyStr | None = None
    device_class: NonEmptyStr | None = None
    cpu: NonEmptyStr | None = None
    accelerator: NonEmptyStr | None = None
    memory_bytes: int | None = Field(default=None, gt=0)
    os: NonEmptyStr | None = None


class GenerationConfig(FrozenModel):
    max_output_tokens: int = Field(gt=0)
    temperature: float | None = Field(default=None, ge=0)
    top_p: float | None = Field(default=None, gt=0, le=1)
    seed: int | None = None
    stop: tuple[NonEmptyStr, ...] = ()
    response_format: NonEmptyStr | None = None


class LoadProfile(FrozenModel):
    concurrency: int = Field(default=1, gt=0)
    request_count: int = Field(default=1, gt=0)
    warmup_requests: int = Field(default=0, ge=0)
    streaming: bool = True


class TelemetryLevel(StrEnum):
    BLACK_BOX = "black_box"
    HOST = "host"
    INSTRUMENTED = "instrumented"


class TelemetryDescriptor(FrozenModel):
    level: TelemetryLevel = TelemetryLevel.BLACK_BOX
    protocol_version: NonEmptyStr = "black-box-v1"
    collectors: tuple[NonEmptyStr, ...] = ()


class DatasetSnapshot(VersionedModel):
    dataset_id: NonEmptyStr
    dataset_version: NonEmptyStr
    source: NonEmptyStr
    split: NonEmptyStr
    content_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    selection_policy: NonEmptyStr
    sample_count: int = Field(gt=0)


class EvaluatorRef(FrozenModel):
    evaluator_id: NonEmptyStr
    version: NonEmptyStr


class TaskSpec(FrozenModel):
    task_id: NonEmptyStr
    dataset_snapshot_id: NonEmptyStr
    evaluator: EvaluatorRef
    metric_names: tuple[NonEmptyStr, ...]
    sample_limit: int | None = Field(default=None, gt=0)

    @field_validator("metric_names")
    @classmethod
    def require_metrics(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("metric_names cannot be empty")
        if len(value) != len(set(value)):
            raise ValueError("metric_names must be unique")
        return value


class EvaluationSuite(VersionedModel):
    suite_id: NonEmptyStr
    suite_version: NonEmptyStr
    tasks: tuple[TaskSpec, ...]
    generation: GenerationConfig

    @field_validator("tasks")
    @classmethod
    def require_unique_tasks(cls, value: tuple[TaskSpec, ...]) -> tuple[TaskSpec, ...]:
        if not value:
            raise ValueError("tasks cannot be empty")
        ids = [task.task_id for task in value]
        if len(ids) != len(set(ids)):
            raise ValueError("task ids must be unique")
        return value


class BenchmarkProtocol(FrozenModel):
    version: NonEmptyStr
    prompt_template_version: NonEmptyStr
    load_profile: LoadProfile
    telemetry: TelemetryDescriptor = TelemetryDescriptor()


class ExecutionFingerprint(VersionedModel):
    """Immutable identity of the evaluated configuration.

    Fields describing model/runtime/hardware may remain ``None`` when the endpoint
    cannot expose them.  Their absence is part of the fingerprint rather than guessed.
    """

    target_id: NonEmptyStr
    adapter_type: NonEmptyStr
    endpoint_identity: NonEmptyStr
    model: ModelIdentity
    runtime: RuntimeIdentity = RuntimeIdentity()
    hardware: HardwareIdentity = HardwareIdentity()
    generation: GenerationConfig
    prompt_template_version: NonEmptyStr
    dataset_snapshots: tuple[DatasetSnapshot, ...]
    evaluator_versions: tuple[EvaluatorRef, ...]
    benchmark_protocol_version: NonEmptyStr
    load_profile: LoadProfile
    telemetry: TelemetryDescriptor = TelemetryDescriptor()

    @field_validator("dataset_snapshots")
    @classmethod
    def require_datasets(cls, value: tuple[DatasetSnapshot, ...]) -> tuple[DatasetSnapshot, ...]:
        if not value:
            raise ValueError("dataset_snapshots cannot be empty")
        ids = [item.dataset_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("dataset snapshot ids must be unique")
        return value

    @field_validator("evaluator_versions")
    @classmethod
    def require_evaluators(cls, value: tuple[EvaluatorRef, ...]) -> tuple[EvaluatorRef, ...]:
        if not value:
            raise ValueError("evaluator_versions cannot be empty")
        ids = [item.evaluator_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("evaluator ids must be unique")
        return value

    @property
    def fingerprint_id(self) -> str:
        return self.content_digest()


class MeasurementScope(StrEnum):
    SAMPLE = "sample"
    RUN = "run"


class MeasurementProvenance(StrEnum):
    CLIENT = "client"
    HOST = "host"
    RUNTIME = "runtime"


class Measurement(FrozenModel):
    name: NonEmptyStr
    value: float
    unit: NonEmptyStr
    scope: MeasurementScope
    provenance: MeasurementProvenance
    protocol_version: NonEmptyStr
    observed_at: datetime | None = None

    @field_validator("observed_at")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        return value


class Score(FrozenModel):
    metric: NonEmptyStr
    value: float
    evaluator: EvaluatorRef
    higher_is_better: bool
    numerator: float | None = None
    denominator: float | None = None

    @model_validator(mode="after")
    def validate_fraction(self) -> Score:
        if (self.numerator is None) != (self.denominator is None):
            raise ValueError("numerator and denominator must be set together")
        if self.denominator is not None and self.denominator <= 0:
            raise ValueError("denominator must be > 0")
        return self


class SampleStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorInfo(FrozenModel):
    code: NonEmptyStr
    category: NonEmptyStr
    retryable: bool = False


class SampleExecution(VersionedModel):
    sample_id: NonEmptyStr
    task_id: NonEmptyStr
    attempt: int = Field(default=1, gt=0)
    status: SampleStatus
    started_at: datetime
    completed_at: datetime
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    measurements: tuple[Measurement, ...] = ()
    scores: tuple[Score, ...] = ()
    error: ErrorInfo | None = None

    @field_validator("started_at", "completed_at")
    @classmethod
    def aware_timestamps(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("run timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_status(self) -> SampleExecution:
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        if self.status == SampleStatus.SUCCEEDED and self.error is not None:
            raise ValueError("successful samples cannot contain an error")
        if self.status != SampleStatus.SUCCEEDED and self.error is None:
            raise ValueError("failed/cancelled samples require typed error info")
        return self


class RunStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Run(VersionedModel):
    run_id: NonEmptyStr
    status: RunStatus
    fingerprint: ExecutionFingerprint
    suite: EvaluationSuite
    created_at: datetime
    completed_at: datetime | None = None
    aggregate_scores: tuple[Score, ...] = ()
    aggregate_measurements: tuple[Measurement, ...] = ()
    samples: tuple[SampleExecution, ...] = ()

    @field_validator("created_at", "completed_at")
    @classmethod
    def aware_run_timestamps(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("run timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_lifecycle(self) -> Run:
        terminal = {
            RunStatus.SUCCEEDED,
            RunStatus.FAILED,
            RunStatus.CANCELLED,
        }
        if self.status in terminal and self.completed_at is None:
            raise ValueError("terminal runs require completed_at")
        if self.status not in terminal and self.completed_at is not None:
            raise ValueError("non-terminal runs cannot have completed_at")
        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("completed_at cannot precede created_at")
        return self
