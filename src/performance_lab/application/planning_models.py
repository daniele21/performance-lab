"""Browser-facing use-case-first campaign planning contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from performance_lab.domain import GenerationConfig

from .ui_models import DatasetSummaryReadModel, SuiteSummaryReadModel, TargetSummaryReadModel, UIModel


class CampaignSearchStrategy(StrEnum):
    FIXED = "fixed"
    QUICK = "quick"
    STANDARD = "standard"
    THOROUGH = "thorough"
    CUSTOM = "custom"


class UseCaseReadModel(UIModel):
    use_case_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    task_family: str = Field(min_length=1)
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    source: Literal["starter", "workload_pack"]


class CandidateModelReadModel(UIModel):
    target_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    revision: str | None = None
    artifact_digest: str | None = None
    quantization: str | None = None
    source: Literal["configured", "discovered"]


class ConfigurationSearchOptionReadModel(UIModel):
    strategy: CampaignSearchStrategy
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    available: bool
    blocked_reason: str | None = None

    @model_validator(mode="after")
    def require_blocked_reason(self) -> ConfigurationSearchOptionReadModel:
        if self.available and self.blocked_reason is not None:
            raise ValueError("available search options cannot have a blocked reason")
        if not self.available and self.blocked_reason is None:
            raise ValueError("unavailable search options require a blocked reason")
        return self


class CampaignTargetPlanningReadModel(UIModel):
    target: TargetSummaryReadModel
    candidates: tuple[CandidateModelReadModel, ...] = ()
    configuration_search_options: tuple[ConfigurationSearchOptionReadModel, ...] = ()


class CampaignPlanningContextReadModel(UIModel):
    use_cases: tuple[UseCaseReadModel, ...] = ()
    targets: tuple[CampaignTargetPlanningReadModel, ...] = ()


class CampaignPlanPreviewRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    use_case_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    candidate_model_ids: tuple[str, ...]
    configuration_strategy: CampaignSearchStrategy = CampaignSearchStrategy.FIXED

    @model_validator(mode="after")
    def validate_candidates(self) -> CampaignPlanPreviewRequest:
        if not self.candidate_model_ids:
            raise ValueError("at least one candidate model is required")
        if len(self.candidate_model_ids) > 32:
            raise ValueError("candidate model count cannot exceed 32")
        if len(self.candidate_model_ids) != len(set(self.candidate_model_ids)):
            raise ValueError("candidate model ids must be unique")
        if any(not model_id for model_id in self.candidate_model_ids):
            raise ValueError("candidate model ids cannot be empty")
        return self


class CampaignPlanIssueReadModel(UIModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    field: str | None = None


class ConfigurationSearchPlanReadModel(UIModel):
    strategy: CampaignSearchStrategy
    title: str = Field(min_length=1)
    configuration_count_per_candidate: int = Field(gt=0)
    base_generation: GenerationConfig
    bounded_parameter_ranges: tuple[str, ...] = ()
    note: str = Field(min_length=1)


class BenchmarkPlanReadModel(UIModel):
    suite: SuiteSummaryReadModel
    datasets: tuple[DatasetSummaryReadModel, ...]
    evaluator_ids: tuple[str, ...]
    case_count_per_run: int = Field(gt=0)


class CampaignEstimateReadModel(UIModel):
    candidate_count: int = Field(gt=0)
    configuration_count_per_candidate: int = Field(gt=0)
    planned_run_count: int = Field(gt=0)
    benchmark_case_count_per_run: int = Field(gt=0)
    estimated_request_count: int = Field(gt=0)
    estimated_duration_seconds: float | None = Field(default=None, gt=0)
    duration_reason: str = Field(min_length=1)


class CampaignPlanPreviewReadModel(UIModel):
    can_plan: bool
    issues: tuple[CampaignPlanIssueReadModel, ...] = ()
    plan_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    use_case: UseCaseReadModel | None = None
    target: TargetSummaryReadModel | None = None
    candidates: tuple[CandidateModelReadModel, ...] = ()
    configuration_search: ConfigurationSearchPlanReadModel | None = None
    benchmark_plan: BenchmarkPlanReadModel | None = None
    estimate: CampaignEstimateReadModel | None = None
    execution_available: Literal[False] = False
    execution_blocked_reason: str = Field(
        default="Campaign execution is not implemented yet; this preview only freezes the intended plan.",
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_preview_shape(self) -> CampaignPlanPreviewReadModel:
        complete = all(
            value is not None
            for value in (
                self.plan_digest,
                self.use_case,
                self.target,
                self.configuration_search,
                self.benchmark_plan,
                self.estimate,
            )
        ) and bool(self.candidates)
        if self.can_plan and (self.issues or not complete):
            raise ValueError("executable planning previews require a complete frozen plan")
        if not self.can_plan and not self.issues:
            raise ValueError("blocked planning previews require at least one issue")
        return self
