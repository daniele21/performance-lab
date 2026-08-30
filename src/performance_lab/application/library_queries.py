"""Library-facing query projections built on the core UI query service."""

from __future__ import annotations

from performance_lab.datasets import MaterializedDataset
from performance_lab.domain import (
    DatasetSnapshot,
    EndpointProfile,
    EvaluationSuite,
    EvaluatorRef,
    Target,
)
from performance_lab.evaluation import describe_evaluator
from performance_lab.plugins import Evaluator
from performance_lab.regression import BaselineBinding, RegressionPolicy
from performance_lab.run_config import StarterRunConfig

from .ui_models import (
    BenchmarkCaseReadModel,
    BenchmarkDetailReadModel,
    BenchmarkTaskReadModel,
    DatasetSummaryReadModel,
    EvaluatorDefinitionReadModel,
)
from .ui_queries import CompletedRunReader
from .ui_queries import UIQueryService as CoreUIQueryService


class UIQueryService(CoreUIQueryService):
    """Core UI projections plus inspectable Library definition read paths."""

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
        )
        self._inspectable_datasets = _unique_datasets(inspectable_datasets)
        self._evaluators = _unique_evaluators(evaluators)

    def list_evaluators(self) -> tuple[EvaluatorDefinitionReadModel, ...]:
        return tuple(
            _evaluator_definition(EvaluatorRef(evaluator_id=key[0], version=key[1]), evaluator)
            for key, evaluator in sorted(self._evaluators.items())
        )

    def get_benchmark(self, suite_id: str, suite_version: str) -> BenchmarkDetailReadModel:
        suite = next(
            (
                item
                for item in self.suites
                if item.suite_id == suite_id and item.suite_version == suite_version
            ),
            None,
        )
        if suite is None:
            raise LookupError(f"benchmark definition not found: {suite_id}@{suite_version}")
        summary = next(
            item
            for item in self.list_suites()
            if item.suite_id == suite_id and item.suite_version == suite_version
        )

        snapshots = {snapshot.dataset_id: snapshot for snapshot in self.dataset_snapshots}
        tasks: list[BenchmarkTaskReadModel] = []
        cases: list[BenchmarkCaseReadModel] = []
        issues: list[str] = []

        for task in suite.tasks:
            snapshot = snapshots.get(task.dataset_snapshot_id)
            dataset_summary = (
                DatasetSummaryReadModel.from_snapshot(snapshot) if snapshot is not None else None
            )
            if snapshot is None:
                issues.append(f"Dataset snapshot is not registered: {task.dataset_snapshot_id}")

            evaluator_impl = self._evaluators.get(
                (task.evaluator.evaluator_id, task.evaluator.version)
            )
            evaluator = _evaluator_definition(task.evaluator, evaluator_impl)
            if evaluator_impl is None:
                issues.append(
                    "Evaluator implementation is not registered: "
                    f"{task.evaluator.evaluator_id}@{task.evaluator.version}"
                )

            materialized = self._inspectable_datasets.get(task.dataset_snapshot_id)
            content_available = False
            if materialized is not None and snapshot is not None:
                if materialized.snapshot == snapshot:
                    content_available = True
                else:
                    issues.append(
                        "Inspectable dataset does not match registered snapshot: "
                        f"{task.dataset_snapshot_id}"
                    )

            case_count = _task_case_count(snapshot, task.sample_limit)
            tasks.append(
                BenchmarkTaskReadModel(
                    task_id=task.task_id,
                    dataset_snapshot_id=task.dataset_snapshot_id,
                    dataset=dataset_summary,
                    evaluator=evaluator,
                    metric_names=task.metric_names,
                    sample_limit=task.sample_limit,
                    case_count=case_count,
                    case_content_available=content_available,
                )
            )

            if not content_available or materialized is None:
                continue
            records = materialized.records[: task.sample_limit]
            cases.extend(
                BenchmarkCaseReadModel(
                    case_id=f"{task.task_id}:{record.sample_id}",
                    task_id=task.task_id,
                    sample_id=record.sample_id,
                    dataset_id=materialized.snapshot.dataset_id,
                    dataset_version=materialized.snapshot.dataset_version,
                    input=record.input,
                    expected=record.expected,
                    evaluator_id=task.evaluator.evaluator_id,
                    evaluator_version=task.evaluator.version,
                    metric_names=task.metric_names,
                )
                for record in records
            )

        return BenchmarkDetailReadModel(
            summary=summary,
            generation=suite.generation,
            tasks=tuple(tasks),
            cases=tuple(cases),
            definition_issues=tuple(dict.fromkeys(issues)),
        )


def _unique_datasets(
    datasets: tuple[MaterializedDataset, ...],
) -> dict[str, MaterializedDataset]:
    result: dict[str, MaterializedDataset] = {}
    for dataset in datasets:
        dataset_id = dataset.snapshot.dataset_id
        if dataset_id in result:
            raise ValueError(f"inspectable dataset ids must be unique: {dataset_id}")
        result[dataset_id] = dataset
    return result


def _unique_evaluators(evaluators: tuple[Evaluator, ...]) -> dict[tuple[str, str], Evaluator]:
    result: dict[tuple[str, str], Evaluator] = {}
    for evaluator in evaluators:
        key = (evaluator.evaluator_id, evaluator.version)
        if key in result:
            raise ValueError(
                "registered evaluator identity must be unique: "
                f"{evaluator.evaluator_id}@{evaluator.version}"
            )
        result[key] = evaluator
    return result


def _evaluator_definition(
    ref: EvaluatorRef,
    evaluator: Evaluator | None,
) -> EvaluatorDefinitionReadModel:
    if evaluator is None:
        return EvaluatorDefinitionReadModel(
            evaluator_id=ref.evaluator_id,
            version=ref.version,
            evaluator_type="unregistered",
        )
    descriptor = describe_evaluator(evaluator)
    return EvaluatorDefinitionReadModel(
        evaluator_id=descriptor.evaluator_id,
        version=descriptor.version,
        evaluator_type=descriptor.evaluator_type,
        deterministic=descriptor.deterministic,
        explanation_supported=descriptor.explanation_supported,
        rule_summary=descriptor.rule_summary,
        configuration=dict(descriptor.configuration),
    )


def _task_case_count(snapshot: DatasetSnapshot | None, sample_limit: int | None) -> int | None:
    if snapshot is None:
        return None
    if sample_limit is None:
        return snapshot.sample_count
    return min(snapshot.sample_count, sample_limit)
