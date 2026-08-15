"""Optional telemetry lifecycle and host/runtime-native collectors."""

from .host import PortableHostCollector
from .instrumented import (
    RUNTIME_TELEMETRY_PROTOCOL_VERSION,
    InstrumentedEndpointCollector,
    RuntimeTelemetryIdentity,
    RuntimeTelemetryMeasurement,
    RuntimeTelemetryStartResponse,
    RuntimeTelemetryStopResponse,
)
from .session import (
    CollectorOutcome,
    TelemetryAvailability,
    TelemetryRunResult,
    TelemetrySession,
)

__all__ = [
    "RUNTIME_TELEMETRY_PROTOCOL_VERSION",
    "CollectorOutcome",
    "InstrumentedEndpointCollector",
    "PortableHostCollector",
    "RuntimeTelemetryIdentity",
    "RuntimeTelemetryMeasurement",
    "RuntimeTelemetryStartResponse",
    "RuntimeTelemetryStopResponse",
    "TelemetryAvailability",
    "TelemetryRunResult",
    "TelemetrySession",
]
