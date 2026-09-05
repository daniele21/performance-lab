from performance_lab.application.device_evidence import (
    DecisionEvidenceRole,
    classify_measurement,
    resource_measurement_is_decision_eligible,
)
from performance_lab.domain import (
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
)


def _measurement(
    *,
    name: str,
    unit: str,
    provenance: MeasurementProvenance,
    protocol_version: str,
) -> Measurement:
    return Measurement(
        name=name,
        value=1.0,
        unit=unit,
        scope=MeasurementScope.RUN,
        provenance=provenance,
        protocol_version=protocol_version,
    )


def test_client_performance_is_attributable_decision_evidence() -> None:
    measurement = _measurement(
        name="request_latency_ms",
        unit="ms",
        provenance=MeasurementProvenance.CLIENT,
        protocol_version="openai-compatible-v1",
    )

    classification = classify_measurement(measurement)

    assert classification.role == DecisionEvidenceRole.DECISION_ELIGIBLE
    assert not resource_measurement_is_decision_eligible(measurement)


def test_host_process_telemetry_stays_context_only() -> None:
    measurement = _measurement(
        name="process_peak_rss_bytes",
        unit="bytes",
        provenance=MeasurementProvenance.HOST,
        protocol_version="host-stdlib-v1",
    )

    classification = classify_measurement(measurement)

    assert classification.role == DecisionEvidenceRole.CONTEXT_ONLY
    assert "attributable model-server" in classification.reason
    assert not resource_measurement_is_decision_eligible(measurement)


def test_local_llm_server_activity_telemetry_stays_context_only() -> None:
    measurement = _measurement(
        name="peak_active_requests",
        unit="count",
        provenance=MeasurementProvenance.RUNTIME,
        protocol_version="local-llm-server-status-v1",
    )

    classification = classify_measurement(measurement)

    assert classification.role == DecisionEvidenceRole.CONTEXT_ONLY
    assert "owning versioned contract" in classification.reason
    assert not resource_measurement_is_decision_eligible(measurement)
