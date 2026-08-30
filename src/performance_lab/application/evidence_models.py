"""Run/sample evidence projections for browser-facing drill-down surfaces."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from performance_lab.domain import (
    ErrorInfo,
    ExecutionFingerprint,
    MeasurementProvenance,
    MeasurementScope,
    SampleStatus,
)

from .ui_models import BenchmarkCaseReadModel, RunSummaryReadModel, UIModel


class EvidenceContentState(StrEnum):
    RETAINED = "retained"
    NOT_RETAINED = "not_retained"
    UNAVAILABLE = "unavailable"


class ExplanationState(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class EvidenceContentReadModel(UIModel):
    """Typed content state so absence is never rendered as an empty retained value."""

    state: EvidenceContentState
    content: object | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_content_state(self) -> EvidenceContentReadModel:
        if self.state == EvidenceContentState.RETAINED and self.content is None:
            raise ValueError("retained evidence content requires content")
        if self.state != EvidenceContentState.RETAINED and self.content is not None:
            raise ValueError("non-retained/unavailable evidence cannot contain content")
        return self


class SampleSummaryReadModel(UIModel):
    run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    attempt: int = Field(gt=0)
    status: SampleStatus
    started_at: datetime
    completed_at: datetime
    elapsed_ms: float = Field(ge=0)
    elapsed_provenance: Literal["sample_execution_timestamps"] = "sample_execution_timestamps"
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    score_count: int = Field(ge=0)
    measurement_count: int = Field(ge=0)
    error: ErrorInfo | None = None


class SampleScoreReadModel(UIModel):
    metric: str = Field(min_length=1)
    value: float
    evaluator_id: str = Field(min_length=1)
    evaluator_version: str = Field(min_length=1)
    higher_is_better: bool
    numerator: float | None = None
    denominator: float | None = None
    evaluator_rule_summary: str | None = None
    explanation_state: ExplanationState = ExplanationState.UNAVAILABLE
    explanation: str | None = None

    @model_validator(mode="after")
    def validate_explanation_state(self) -> SampleScoreReadModel:
        if self.explanation_state == ExplanationState.AVAILABLE and not self.explanation:
            raise ValueError("available evaluator explanation requires explanation content")
        if self.explanation_state == ExplanationState.UNAVAILABLE and self.explanation is not None:
            raise ValueError("unavailable evaluator explanation cannot contain explanation content")
        return self


class SampleMeasurementReadModel(UIModel):
    name: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    scope: MeasurementScope
    provenance: MeasurementProvenance
    protocol_version: str = Field(min_length=1)
    observed_at: datetime | None = None


class SampleEvidenceDetailReadModel(UIModel):
    """One immutable sample attempt plus all evidence truthfully available for it."""

    run: RunSummaryReadModel
    fingerprint: ExecutionFingerprint
    sample: SampleSummaryReadModel
    benchmark_case: BenchmarkCaseReadModel | None = None
    prompt: EvidenceContentReadModel
    response: EvidenceContentReadModel
    scores: tuple[SampleScoreReadModel, ...] = ()
    measurements: tuple[SampleMeasurementReadModel, ...] = ()
    definition_issues: tuple[str, ...] = ()
