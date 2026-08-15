"""Optional telemetry collector lifecycle and typed availability outcomes."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import Measurement
from performance_lab.plugins import TelemetryCollector, TelemetryCollectorCapabilities


class TelemetryModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TelemetryAvailability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    PERMISSION_DENIED = "permission_denied"
    ERROR = "error"


class CollectorOutcome(TelemetryModel):
    collector_id: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
    availability: TelemetryAvailability
    capabilities: TelemetryCollectorCapabilities = Field(
        default_factory=TelemetryCollectorCapabilities
    )
    measurements: tuple[Measurement, ...] = ()
    reason: str | None = None


class TelemetryRunResult(TelemetryModel):
    outcomes: tuple[CollectorOutcome, ...] = ()

    @property
    def measurements(self) -> tuple[Measurement, ...]:
        return tuple(
            measurement
            for outcome in self.outcomes
            for measurement in outcome.measurements
            if outcome.availability == TelemetryAvailability.AVAILABLE
        )


class TelemetrySession:
    """Run optional collectors without making telemetry a run prerequisite."""

    def __init__(self, collectors: Sequence[TelemetryCollector]) -> None:
        ids = [collector.collector_id for collector in collectors]
        if len(ids) != len(set(ids)):
            raise ValueError("telemetry collector ids must be unique")
        self._collectors = tuple(collectors)
        self._active: list[TelemetryCollector] = []
        self._start_failures: list[CollectorOutcome] = []
        self._started = False

    async def start(self, run_id: str) -> None:
        if self._started:
            raise RuntimeError("telemetry session already started")
        self._started = True
        for collector in self._collectors:
            try:
                collector.capabilities()
                await collector.start(run_id)
            except (OSError, RuntimeError) as exc:
                self._start_failures.append(
                    CollectorOutcome(
                        collector_id=collector.collector_id,
                        protocol_version=collector.protocol_version,
                        availability=TelemetryAvailability.ERROR,
                        reason=str(exc) or type(exc).__name__,
                    )
                )
                continue
            self._active.append(collector)

    async def stop(self) -> TelemetryRunResult:
        if not self._started:
            raise RuntimeError("telemetry session has not started")
        outcomes = list(self._start_failures)
        for collector in self._active:
            capabilities = collector.capabilities()
            try:
                measurements = await collector.stop()
            except (OSError, RuntimeError) as exc:
                outcomes.append(
                    CollectorOutcome(
                        collector_id=collector.collector_id,
                        protocol_version=collector.protocol_version,
                        availability=TelemetryAvailability.ERROR,
                        capabilities=capabilities,
                        reason=str(exc) or type(exc).__name__,
                    )
                )
                continue
            outcomes.append(
                CollectorOutcome(
                    collector_id=collector.collector_id,
                    protocol_version=collector.protocol_version,
                    availability=TelemetryAvailability.AVAILABLE,
                    capabilities=capabilities,
                    measurements=measurements,
                )
            )
        self._active.clear()
        return TelemetryRunResult(outcomes=tuple(outcomes))
