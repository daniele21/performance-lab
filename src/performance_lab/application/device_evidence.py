"""Policy-eligibility classification for retained device/performance measurements.

Performance Lab retains more telemetry than it is allowed to use for a best-fit decision.
This module is the canonical application boundary that prevents contextual host/runtime
observations from silently becoming model-resource evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from performance_lab.domain import Measurement, MeasurementProvenance


class DecisionEvidenceRole(StrEnum):
    """Whether a retained measurement may participate in a decision after comparability."""

    DECISION_ELIGIBLE = "decision_eligible"
    CONTEXT_ONLY = "context_only"


@dataclass(frozen=True, slots=True)
class DecisionEvidenceClassification:
    role: DecisionEvidenceRole
    reason: str


# Resource measurements require explicit opt-in by the owning runtime/collector contract.
# The current host-stdlib collector measures the Performance Lab process/host, while
# local-llm-server-status-v1 reports runtime activity/concurrency rather than attributable
# model resource consumption. Therefore no current HOST/RUNTIME measurement is registered.
_RESOURCE_DECISION_KEYS: frozenset[tuple[str, str, str, str]] = frozenset()


def resource_metric_is_decision_eligible(
    *,
    provenance: MeasurementProvenance,
    protocol_version: str,
    name: str,
    unit: str,
) -> bool:
    """Check the owning resource contract from a stable metric identity.

    Aggregate and sample projections use the same owner. This avoids reclassifying browser-facing
    sample read models by convention or by metric name alone.
    """

    if provenance not in {
        MeasurementProvenance.HOST,
        MeasurementProvenance.RUNTIME,
    }:
        return False
    return (provenance.value, protocol_version, name, unit) in _RESOURCE_DECISION_KEYS


def classify_measurement(measurement: Measurement) -> DecisionEvidenceClassification:
    """Classify retained measurement truth without inferring missing ownership semantics."""

    if measurement.provenance == MeasurementProvenance.CLIENT:
        return DecisionEvidenceClassification(
            role=DecisionEvidenceRole.DECISION_ELIGIBLE,
            reason=(
                "Black-box request performance is observed by Performance Lab for the frozen "
                "execution and may participate after runtime comparability is established."
            ),
        )

    if resource_metric_is_decision_eligible(
        provenance=measurement.provenance,
        protocol_version=measurement.protocol_version,
        name=measurement.name,
        unit=measurement.unit,
    ):
        return DecisionEvidenceClassification(
            role=DecisionEvidenceRole.DECISION_ELIGIBLE,
            reason="The owning resource telemetry contract explicitly marks this metric eligible.",
        )

    if measurement.provenance == MeasurementProvenance.HOST:
        return DecisionEvidenceClassification(
            role=DecisionEvidenceRole.CONTEXT_ONLY,
            reason=(
                "Host telemetry is retained as execution context; the current collector does not "
                "establish attributable model-server resource consumption."
            ),
        )
    return DecisionEvidenceClassification(
        role=DecisionEvidenceRole.CONTEXT_ONLY,
        reason=(
            "Runtime telemetry is retained as context unless its owning versioned contract "
            "explicitly declares an attributable resource metric policy-eligible."
        ),
    )


def resource_measurement_is_decision_eligible(measurement: Measurement) -> bool:
    """Return true only for explicitly contracted HOST/RUNTIME model-resource evidence."""

    return resource_metric_is_decision_eligible(
        provenance=measurement.provenance,
        protocol_version=measurement.protocol_version,
        name=measurement.name,
        unit=measurement.unit,
    )
