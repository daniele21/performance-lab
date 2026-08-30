"""Run/sample evidence queries layered on top of Library definition projections."""

from __future__ import annotations

from performance_lab.domain import Run, SampleExecution, Score

from .evidence_models import (
    EvidenceContentReadModel,
    EvidenceContentState,
    ExplanationState,
    SampleEvidenceDetailReadModel,
    SampleMeasurementReadModel,
    SampleScoreReadModel,
    SampleSummaryReadModel,
)
from .library_queries import UIQueryService as LibraryUIQueryService
from .ui_models import BenchmarkCaseReadModel, EvaluatorDefinitionReadModel


class UIQueryService(LibraryUIQueryService):
    """Canonical UI queries plus immutable sample-evidence drill-down."""

    def list_run_samples(self, run_id: str) -> tuple[SampleSummaryReadModel, ...]:
        run = self.store.get_completed(run_id)
        if run is None:
            raise LookupError(f"completed run not found: {run_id}")
        return tuple(_sample_summary(run_id, sample) for sample in run.samples)

    def get_sample_evidence(
        self,
        run_id: str,
        task_id: str,
        sample_id: str,
        attempt: int,
    ) -> SampleEvidenceDetailReadModel:
        run = self.store.get_completed(run_id)
        if run is None:
            raise LookupError(f"completed run not found: {run_id}")
        sample = next(
            (
                item
                for item in run.samples
                if item.task_id == task_id
                and item.sample_id == sample_id
                and item.attempt == attempt
            ),
            None,
        )
        if sample is None:
            raise LookupError(
                "sample evidence not found: "
                f"{run_id}/{task_id}/{sample_id}/attempt-{attempt}"
            )

        benchmark_case, definition_issues = self._benchmark_case_for(run, sample)
        evaluators = {
            (item.evaluator_id, item.version): item for item in self.list_evaluators()
        }
        scores = tuple(
            _score_projection(
                score,
                evaluators.get((score.evaluator.evaluator_id, score.evaluator.version)),
            )
            for score in sample.scores
        )
        measurements = tuple(
            SampleMeasurementReadModel(
                name=item.name,
                value=item.value,
                unit=item.unit,
                scope=item.scope,
                provenance=item.provenance,
                protocol_version=item.protocol_version,
                observed_at=item.observed_at,
            )
            for item in sample.measurements
        )
        run_detail = self.get_run(run_id)
        not_retained = EvidenceContentReadModel(
            state=EvidenceContentState.NOT_RETAINED,
            reason="content_not_retained",
        )
        return SampleEvidenceDetailReadModel(
            run=run_detail.summary,
            fingerprint=run.fingerprint,
            sample=_sample_summary(run_id, sample),
            benchmark_case=benchmark_case,
            prompt=not_retained,
            response=not_retained,
            scores=scores,
            measurements=measurements,
            definition_issues=definition_issues,
        )

    def _benchmark_case_for(
        self,
        run: Run,
        sample: SampleExecution,
    ) -> tuple[BenchmarkCaseReadModel | None, tuple[str, ...]]:
        try:
            benchmark = self.get_benchmark(run.suite.suite_id, run.suite.suite_version)
        except LookupError:
            return None, ("Benchmark definition is not registered for this retained run.",)

        task = next((item for item in benchmark.tasks if item.task_id == sample.task_id), None)
        if task is None:
            return None, (f"Benchmark task definition is unavailable: {sample.task_id}",)
        if not task.case_content_available:
            return None, (
                "Benchmark case content is unavailable under the current dataset inspection policy.",
            )

        matches = tuple(
            item
            for item in benchmark.cases
            if item.task_id == sample.task_id and item.sample_id == sample.sample_id
        )
        if len(matches) == 1:
            return matches[0], ()
        if not matches:
            return None, (
                "Benchmark case definition is unavailable for this retained sample identity.",
            )
        return None, ("Benchmark case identity is ambiguous for this retained sample.",)


def _sample_summary(run_id: str, sample: SampleExecution) -> SampleSummaryReadModel:
    elapsed_ms = (sample.completed_at - sample.started_at).total_seconds() * 1000
    return SampleSummaryReadModel(
        run_id=run_id,
        task_id=sample.task_id,
        sample_id=sample.sample_id,
        attempt=sample.attempt,
        status=sample.status,
        started_at=sample.started_at,
        completed_at=sample.completed_at,
        elapsed_ms=elapsed_ms,
        input_tokens=sample.input_tokens,
        output_tokens=sample.output_tokens,
        score_count=len(sample.scores),
        measurement_count=len(sample.measurements),
        error=sample.error,
    )


def _score_projection(
    score: Score,
    evaluator: EvaluatorDefinitionReadModel | None,
) -> SampleScoreReadModel:
    return SampleScoreReadModel(
        metric=score.metric,
        value=score.value,
        evaluator_id=score.evaluator.evaluator_id,
        evaluator_version=score.evaluator.version,
        higher_is_better=score.higher_is_better,
        numerator=score.numerator,
        denominator=score.denominator,
        evaluator_rule_summary=evaluator.rule_summary if evaluator is not None else None,
        explanation_state=ExplanationState.UNAVAILABLE,
    )
