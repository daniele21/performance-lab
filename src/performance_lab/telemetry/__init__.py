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
from .local_llm_server import (
    LOCAL_LLM_SERVER_STATUS_PROTOCOL_VERSION,
    LocalLLMServerStatusCollector,
)
from .session import (
    CollectorOutcome,
    TelemetryAvailability,
    TelemetryRunResult,
    TelemetrySession,
)

__all__ = [
    "LOCAL_LLM_SERVER_STATUS_PROTOCOL_VERSION",
    "RUNTIME_TELEMETRY_PROTOCOL_VERSION",
    "CollectorOutcome",
    "InstrumentedEndpointCollector",
    "LocalLLMServerStatusCollector",
    "PortableHostCollector",
    "RuntimeTelemetryIdentity",
    "RuntimeTelemetryMeasurement",
    "RuntimeTelemetryStartResponse",
    "RuntimeTelemetryStopResponse",
    "TelemetryAvailability",
    "TelemetryRunResult",
    "TelemetrySession",
]
