import asyncio
import time

from performance_lab.domain import MeasurementProvenance, MeasurementScope
from performance_lab.telemetry import PortableHostCollector, TelemetrySession


def test_portable_host_collector_reports_attributable_metrics() -> None:
    async def exercise():
        collector = PortableHostCollector()
        session = TelemetrySession([collector])
        await session.start("run-1")
        total = 0
        for value in range(50_000):
            total += value * value
        time.sleep(0.001)
        result = await session.stop()
        return collector, result, total

    collector, result, total = asyncio.run(exercise())
    assert total > 0
    names = {measurement.name for measurement in result.measurements}
    assert "process_cpu_seconds" in names
    assert "process_cpu_cores" in names
    assert "collector_overhead_ms" in names
    assert names <= collector.capabilities().metric_names
    assert all(
        measurement.provenance == MeasurementProvenance.HOST
        and measurement.scope == MeasurementScope.RUN
        and measurement.protocol_version == collector.protocol_version
        for measurement in result.measurements
    )


def test_capabilities_only_claim_platform_observable_metrics() -> None:
    collector = PortableHostCollector()
    capabilities = collector.capabilities()
    assert "process_cpu_seconds" in capabilities.metric_names
    assert "process_cpu_percent_of_host" in capabilities.metric_names
    assert capabilities.sampling is False
