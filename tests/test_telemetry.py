import asyncio

import pytest

from performance_lab.domain import (
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
)
from performance_lab.plugins import FakeTelemetryCollector, TelemetryCollectorCapabilities
from performance_lab.telemetry import TelemetryAvailability, TelemetrySession


class FailingCollector:
    collector_id = "failing"
    protocol_version = "fail-v1"

    def capabilities(self) -> TelemetryCollectorCapabilities:
        return TelemetryCollectorCapabilities(metric_names=frozenset({"memory_bytes"}))

    async def start(self, run_id: str) -> None:
        del run_id
        raise RuntimeError("collector unavailable")

    async def stop(self) -> tuple[Measurement, ...]:
        raise AssertionError("stop must not be called after failed start")


def measurement() -> Measurement:
    return Measurement(
        name="memory_bytes",
        value=1024.0,
        unit="bytes",
        scope=MeasurementScope.RUN,
        provenance=MeasurementProvenance.HOST,
        protocol_version="fake-v1",
    )


def test_successful_collector_returns_measurements() -> None:
    async def exercise():
        session = TelemetrySession([FakeTelemetryCollector((measurement(),))])
        await session.start("run-1")
        return await session.stop()

    result = asyncio.run(exercise())
    assert result.measurements == (measurement(),)
    assert result.outcomes[0].availability == TelemetryAvailability.AVAILABLE


def test_collector_failure_does_not_invalidate_session() -> None:
    async def exercise():
        session = TelemetrySession([FailingCollector(), FakeTelemetryCollector((measurement(),))])
        await session.start("run-1")
        return await session.stop()

    result = asyncio.run(exercise())
    assert len(result.outcomes) == 2
    assert result.outcomes[0].availability == TelemetryAvailability.ERROR
    assert result.outcomes[0].reason == "collector unavailable"
    assert result.measurements == (measurement(),)


def test_zero_collectors_is_valid_black_box_session() -> None:
    async def exercise():
        session = TelemetrySession([])
        await session.start("run-1")
        return await session.stop()

    result = asyncio.run(exercise())
    assert result.outcomes == ()
    assert result.measurements == ()


def test_duplicate_collector_ids_are_rejected() -> None:
    with pytest.raises(ValueError):
        TelemetrySession([FakeTelemetryCollector(), FakeTelemetryCollector()])
