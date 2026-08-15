"""Versioned evidence-retention policy applied before immutable publication."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from performance_lab.domain import Run, RunStatus, SampleExecution, SampleStatus

RETENTION_POLICY_VERSION: Literal[1] = 1
_TERMINAL_STATUSES = {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED}


class RetentionModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SampleEvidenceRetention(StrEnum):
    ALL = "all"
    FAILURES_ONLY = "failures_only"
    NONE = "none"


class RetentionPolicy(RetentionModel):
    """Control persisted diagnostic detail without ever permitting raw prompt/output content."""

    schema_version: Literal[1] = RETENTION_POLICY_VERSION
    raw_prompt_output: Literal["never"] = "never"
    sample_evidence: SampleEvidenceRetention = SampleEvidenceRetention.ALL
    retain_sample_measurements: bool = False
    retain_aggregate_measurements: bool = True


class RunPublicationSink(Protocol):
    def save_working(self, run: Run) -> None: ...

    def publish(self, run: Run) -> None: ...


def prepare_run_for_publication(
    run: Run,
    policy: RetentionPolicy | None = None,
) -> Run:
    """Return a retained copy for immutable storage; never mutate the execution result."""

    if run.status not in _TERMINAL_STATUSES:
        raise ValueError("retention policy can only prepare terminal runs for publication")
    active_policy = policy or RetentionPolicy()
    retained_samples = _retain_samples(run.samples, active_policy)
    aggregate_measurements = (
        run.aggregate_measurements if active_policy.retain_aggregate_measurements else ()
    )
    return run.model_copy(
        update={
            "samples": retained_samples,
            "aggregate_measurements": aggregate_measurements,
        }
    )


class RetentionRunSink:
    """Apply retention only at terminal publication while preserving mutable working state."""

    def __init__(
        self,
        sink: RunPublicationSink,
        policy: RetentionPolicy | None = None,
    ) -> None:
        self._sink = sink
        self.policy = policy or RetentionPolicy()

    def save_working(self, run: Run) -> None:
        self._sink.save_working(run)

    def publish(self, run: Run) -> None:
        self._sink.publish(prepare_run_for_publication(run, self.policy))


def _retain_samples(
    samples: tuple[SampleExecution, ...],
    policy: RetentionPolicy,
) -> tuple[SampleExecution, ...]:
    if policy.sample_evidence == SampleEvidenceRetention.NONE:
        return ()
    selected = samples
    if policy.sample_evidence == SampleEvidenceRetention.FAILURES_ONLY:
        selected = tuple(sample for sample in samples if sample.status != SampleStatus.SUCCEEDED)
    if policy.retain_sample_measurements:
        return selected
    return tuple(sample.model_copy(update={"measurements": ()}) for sample in selected)
