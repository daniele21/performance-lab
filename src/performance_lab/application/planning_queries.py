"""Use-case-first campaign planning layered on retained evidence queries."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Literal

from performance_lab.datasets import MaterializedDataset, WorkloadPackBundle
from performance_lab.domain import DatasetSnapshot, EndpointProfile, EvaluationSuite, Target
from performance_lab.plugins import Evaluator
from performance_lab.regression import BaselineBinding, RegressionPolicy
from performance_lab.run_config import StarterRunConfig

from .evidence_queries import UIQueryService as EvidenceUIQueryService
from .planning_models import (
    BenchmarkPlanReadModel,
    CampaignEstimateReadModel,
    CampaignPlanIssueReadModel,
    CampaignPlanPreviewReadModel,
    CampaignPlanPreviewRequest,
    CampaignPlanningContextReadModel,
    CampaignSearchStrategy,
    CampaignTargetPlanningReadModel,
    CandidateModelReadModel,
    ConfigurationSearchOptionReadModel,
    ConfigurationSearchPlanReadModel,
    UseCaseReadModel,
)
from .ui_models import (
    DatasetSummaryReadModel,
    DiscoveredModelReadModel,
    EndpointConnectionInput,
    SuiteSummaryReadModel,
    TargetSummaryReadModel,
)
from .ui_queries import STARTER_SUITE_ID, CompletedRunReader

GENERAL_USE_CASE_ID = "general-capability"
GENERAL_USE_CASE_VERSION = "1"
_NO_BOUNDED_RANGE_REASON = (
    "The runtime reports parameter support but no bounded search ranges. "
    "Performance Lab will not invent sweep domains."
)


class UIQueryService(EvidenceUIQueryService):
    """Canonical UI queries plus bounded, frozen campaign planning."""

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
        inspectable_datasets: tuple[MaterializedDataset, ...] = (),
        evaluators: tuple[Evaluator, ...] = (),
        workload_packs: tuple[WorkloadPackBundle, ...] = (),
    ) -> None:
        super().__init__(
            store,
            targets=targets,
            endpoint_profiles=endpoint_profiles,
            suites=suites,
            dataset_snapshots=dataset_snapshots,
            baselines=baselines,
            policies=policies,
            starter_run_template=starter_run_template,
            inspectable_datasets=inspectable_datasets,
            evaluators=evaluators,
        )
        self._workload_packs = _unique_workload_packs(workload_packs)
        self._session_discovered_models: dict[str, tuple[DiscoveredModelReadModel, ...]] = {}
        self._session_generation_parameters: dict[str, tuple[str, ...]] = {}

    def register_session_connection(
        self,
        connection: EndpointConnectionInput,
        *,
        discovered_models: tuple[DiscoveredModelReadModel, ...] = (),
        supported_generation_parameters: tuple[str, ...] = (),
    ) -> TargetSummaryReadModel:
        target = super().register_session_connection(connection)
        self._session_discovered_models[target.target_id] = tuple(discovered_models)
        self._session_generation_parameters[target.target_id] = tuple(
            sorted(dict.fromkeys(supported_generation_parameters))
        )
        current_target_ids = {item.target_id for item in self.list_targets()}
        self._session_discovered_models = {
            target_id: models
            for target_id, models in self._session_discovered_models.items()
            if target_id in current_target_ids
        }
        self._session_generation_parameters = {
            target_id: parameters
            for target_id, parameters in self._session_generation_parameters.items()
            if target_id in current_target_ids
        }
        return target

    def campaign_planning_context(self) -> CampaignPlanningContextReadModel:
        use_cases = self._use_cases()
        configured_target_id = (
            self.starter_run_template.target_id if self.starter_run_template is not None else None
        )
        configured_model_id = (
            self.starter_run_template.model_id if self.starter_run_template is not None else None
        )
        hardware = (
            self.starter_run_template.hardware if self.starter_run_template is not None else None
        )
        targets: list[CampaignTargetPlanningReadModel] = []
        for target in self.list_targets():
            candidates: list[CandidateModelReadModel] = []
            if target.target_id == configured_target_id and configured_model_id:
                candidates.append(
                    _candidate(
                        target.target_id,
                        configured_model_id,
                        source="configured",
                    )
                )
            for model in self._session_discovered_models.get(target.target_id, ()):
                candidates.append(
                    _candidate(
                        target.target_id,
                        model.model_id,
                        source="discovered",
                    )
                )
            candidates = list({item.candidate_id: item for item in candidates}.values())
            supported_parameters = self._session_generation_parameters.get(target.target_id, ())
            targets.append(
                CampaignTargetPlanningReadModel(
                    target=target,
                    hardware_device_id=(
                        hardware.device_id
                        if target.target_id == configured_target_id and hardware
                        else None
                    ),
                    hardware_device_class=(
                        hardware.device_class
                        if target.target_id == configured_target_id and hardware
                        else None
                    ),
                    candidates=tuple(sorted(candidates, key=lambda item: item.model_id)),
                    supported_generation_parameters=supported_parameters,
                    bounded_generation_parameter_ranges=(),
                    configuration_search_options=_search_options(),
                )
            )
        return CampaignPlanningContextReadModel(
            use_cases=use_cases,
            targets=tuple(sorted(targets, key=lambda item: item.target.target_id)),
        )

    def preview_campaign_plan(
        self,
        request: CampaignPlanPreviewRequest,
    ) -> CampaignPlanPreviewReadModel:
        context = self.campaign_planning_context()
        use_case = next(
            (item for item in context.use_cases if item.use_case_id == request.use_case_id),
            None,
        )
        if use_case is None:
            return _blocked(
                "use_case_not_found", "use_case_id", "Selected use case is unavailable."
            )

        target_context = next(
            (item for item in context.targets if item.target.target_id == request.target_id),
            None,
        )
        if target_context is None:
            return _blocked("target_not_found", "target_id", "Selected target is unavailable.")

        candidates_by_id = {item.candidate_id: item for item in target_context.candidates}
        missing_candidates = [
            candidate_id
            for candidate_id in request.candidate_ids
            if candidate_id not in candidates_by_id
        ]
        if missing_candidates:
            return _blocked(
                "candidate_not_found",
                "candidate_ids",
                "One or more selected candidates are no longer available on this target.",
            )
        candidates = tuple(candidates_by_id[candidate_id] for candidate_id in request.candidate_ids)

        option = next(
            (
                item
                for item in target_context.configuration_search_options
                if item.strategy == request.configuration_strategy
            ),
            None,
        )
        if option is None or not option.available:
            return _blocked(
                "configuration_strategy_unavailable",
                "configuration_strategy",
                option.blocked_reason if option is not None else "Search strategy is unavailable.",
            )

        suite, snapshots = self._benchmark_source(use_case)
        snapshot_by_id = {item.dataset_id: item for item in snapshots}
        selected_snapshots: list[DatasetSnapshot] = []
        evaluator_ids: list[str] = []
        case_count = 0
        for task in suite.tasks:
            snapshot = snapshot_by_id.get(task.dataset_snapshot_id)
            if snapshot is None:
                return _blocked(
                    "dataset_not_found",
                    "use_case_id",
                    f"Benchmark dataset is unavailable: {task.dataset_snapshot_id}",
                )
            if snapshot not in selected_snapshots:
                selected_snapshots.append(snapshot)
            evaluator_identity = f"{task.evaluator.evaluator_id}@{task.evaluator.version}"
            if evaluator_identity not in evaluator_ids:
                evaluator_ids.append(evaluator_identity)
            case_count += (
                min(snapshot.sample_count, task.sample_limit)
                if task.sample_limit is not None
                else snapshot.sample_count
            )

        configuration = ConfigurationSearchPlanReadModel(
            strategy=CampaignSearchStrategy.FIXED,
            title="Fixed benchmark configuration",
            configuration_count_per_candidate=1,
            base_generation=suite.generation,
            bounded_parameter_ranges=(),
            note=(
                "Uses the benchmark suite generation configuration exactly as authored. "
                "No parameter sweep is inferred."
            ),
        )
        benchmark_plan = BenchmarkPlanReadModel(
            suite=_suite_summary(suite),
            datasets=tuple(
                DatasetSummaryReadModel.from_snapshot(item) for item in selected_snapshots
            ),
            evaluator_ids=tuple(evaluator_ids),
            case_count_per_run=case_count,
        )
        planned_run_count = len(candidates)
        estimate = CampaignEstimateReadModel(
            candidate_count=len(candidates),
            configuration_count_per_candidate=1,
            planned_run_count=planned_run_count,
            benchmark_case_count_per_run=case_count,
            estimated_request_count=planned_run_count * case_count,
            estimated_duration_seconds=None,
            duration_reason=(
                "Duration unavailable: no evidence-backed timing model exists for this target and plan."
            ),
        )
        digest = _plan_digest(
            use_case=use_case,
            target=target_context.target,
            candidates=candidates,
            configuration=configuration,
            benchmark=benchmark_plan,
            estimate=estimate,
        )
        return CampaignPlanPreviewReadModel(
            can_plan=True,
            plan_digest=digest,
            use_case=use_case,
            target=target_context.target,
            candidates=candidates,
            configuration_search=configuration,
            benchmark_plan=benchmark_plan,
            estimate=estimate,
        )

    def _use_cases(self) -> tuple[UseCaseReadModel, ...]:
        use_cases: list[UseCaseReadModel] = []
        starter = next((item for item in self.suites if item.suite_id == STARTER_SUITE_ID), None)
        if starter is not None:
            use_cases.append(
                UseCaseReadModel(
                    use_case_id=GENERAL_USE_CASE_ID,
                    version=GENERAL_USE_CASE_VERSION,
                    title="General capability",
                    description=(
                        "Balanced authored diagnostics across instruction following, factual QA, "
                        "reasoning, math, classification and structured output."
                    ),
                    task_family="general_capability",
                    suite_id=starter.suite_id,
                    suite_version=starter.suite_version,
                    source="starter",
                )
            )
        use_cases.extend(
            UseCaseReadModel(
                use_case_id=bundle.definition.pack_id,
                version=bundle.definition.version,
                title=bundle.definition.title,
                description=bundle.definition.description,
                task_family=bundle.definition.task_family,
                suite_id=bundle.suite.suite_id,
                suite_version=bundle.suite.suite_version,
                source="workload_pack",
            )
            for bundle in self._workload_packs.values()
        )
        return tuple(sorted(use_cases, key=lambda item: (item.source != "starter", item.title)))

    def _benchmark_source(
        self,
        use_case: UseCaseReadModel,
    ) -> tuple[EvaluationSuite, tuple[DatasetSnapshot, ...]]:
        if use_case.source == "starter":
            suite = next(
                item
                for item in self.suites
                if item.suite_id == use_case.suite_id
                and item.suite_version == use_case.suite_version
            )
            return suite, self.dataset_snapshots
        bundle = self._workload_packs[use_case.use_case_id]
        return bundle.suite, tuple(dataset.snapshot for dataset in bundle.datasets.values())


def _unique_workload_packs(
    bundles: tuple[WorkloadPackBundle, ...],
) -> dict[str, WorkloadPackBundle]:
    result: dict[str, WorkloadPackBundle] = {}
    for bundle in bundles:
        pack_id = bundle.definition.pack_id
        if pack_id in result:
            raise ValueError(f"workload pack ids must be unique: {pack_id}")
        result[pack_id] = bundle
    return result


def _candidate(
    target_id: str,
    model_id: str,
    *,
    source: Literal["configured", "discovered"],
) -> CandidateModelReadModel:
    payload = json.dumps(
        {"target_id": target_id, "model_id": model_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    candidate_id = sha256(payload.encode("utf-8")).hexdigest()
    return CandidateModelReadModel(
        candidate_id=candidate_id,
        target_id=target_id,
        model_id=model_id,
        source=source,
    )


def _search_options() -> tuple[ConfigurationSearchOptionReadModel, ...]:
    return (
        ConfigurationSearchOptionReadModel(
            strategy=CampaignSearchStrategy.FIXED,
            title="Fixed",
            description="Use the authored benchmark generation configuration without a sweep.",
            available=True,
        ),
        *tuple(
            ConfigurationSearchOptionReadModel(
                strategy=strategy,
                title=title,
                description="Search multiple request-level configurations within bounded domains.",
                available=False,
                blocked_reason=_NO_BOUNDED_RANGE_REASON,
            )
            for strategy, title in (
                (CampaignSearchStrategy.QUICK, "Quick"),
                (CampaignSearchStrategy.STANDARD, "Standard"),
                (CampaignSearchStrategy.THOROUGH, "Thorough"),
                (CampaignSearchStrategy.CUSTOM, "Custom"),
            )
        ),
    )


def _suite_summary(suite: EvaluationSuite) -> SuiteSummaryReadModel:
    return SuiteSummaryReadModel(
        suite_id=suite.suite_id,
        suite_version=suite.suite_version,
        task_count=len(suite.tasks),
        task_ids=tuple(task.task_id for task in suite.tasks),
    )


def _blocked(code: str, field: str, message: str) -> CampaignPlanPreviewReadModel:
    return CampaignPlanPreviewReadModel(
        can_plan=False,
        issues=(CampaignPlanIssueReadModel(code=code, field=field, message=message),),
    )


def _plan_digest(
    *,
    use_case: UseCaseReadModel,
    target: TargetSummaryReadModel,
    candidates: tuple[CandidateModelReadModel, ...],
    configuration: ConfigurationSearchPlanReadModel,
    benchmark: BenchmarkPlanReadModel,
    estimate: CampaignEstimateReadModel,
) -> str:
    payload = {
        "contract": "campaign-plan-v1",
        "use_case": use_case.model_dump(mode="json"),
        "target": target.model_dump(mode="json"),
        "candidates": [item.model_dump(mode="json") for item in candidates],
        "configuration": configuration.model_dump(mode="json"),
        "benchmark": benchmark.model_dump(mode="json"),
        "estimate": estimate.model_dump(mode="json"),
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
