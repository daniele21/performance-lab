"""Optional telemetry lifecycle and host collectors."""

from .host import PortableHostCollector
from .session import (
    CollectorOutcome,
    TelemetryAvailability,
    TelemetryRunResult,
    TelemetrySession,
)

__all__ = [
    "CollectorOutcome",
    "PortableHostCollector",
    "TelemetryAvailability",
    "TelemetryRunResult",
    "TelemetrySession",
]
