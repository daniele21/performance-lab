"""Portable best-effort host telemetry using only Python/OS standard facilities."""

from __future__ import annotations

import os
import sys
from time import perf_counter_ns, process_time

from performance_lab.domain import (
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
)
from performance_lab.plugins import TelemetryCollectorCapabilities

try:
    import resource
except ImportError:  # pragma: no cover - platform dependent
    resource = None  # type: ignore[assignment]


class PortableHostCollector:
    """Collect attributable host/process evidence without requiring privileged sensors."""

    collector_id = "portable-host"
    protocol_version = "host-stdlib-v1"

    def __init__(self) -> None:
        self._run_id: str | None = None
        self._wall_started_ns: int | None = None
        self._process_cpu_started: float | None = None
        self._start_overhead_ns = 0

    def capabilities(self) -> TelemetryCollectorCapabilities:
        metrics = {
            "process_cpu_seconds",
            "process_cpu_cores",
            "process_cpu_percent_of_host",
            "collector_overhead_ms",
        }
        if resource is not None:
            metrics.add("process_peak_rss_bytes")
        if hasattr(os, "getloadavg"):
            metrics.update({"host_load_1m", "host_load_5m", "host_load_15m"})
        return TelemetryCollectorCapabilities(metric_names=frozenset(metrics), sampling=False)

    async def start(self, run_id: str) -> None:
        if self._run_id is not None:
            raise RuntimeError("host collector already started")
        overhead_started = perf_counter_ns()
        self._run_id = run_id
        self._process_cpu_started = process_time()
        self._wall_started_ns = perf_counter_ns()
        self._start_overhead_ns = perf_counter_ns() - overhead_started

    async def stop(self) -> tuple[Measurement, ...]:
        if (
            self._run_id is None
            or self._wall_started_ns is None
            or self._process_cpu_started is None
        ):
            raise RuntimeError("host collector has not started")
        overhead_started = perf_counter_ns()
        wall_completed_ns = perf_counter_ns()
        process_cpu_completed = process_time()
        wall_seconds = max((wall_completed_ns - self._wall_started_ns) / 1_000_000_000, 0.0)
        process_cpu_seconds = max(process_cpu_completed - self._process_cpu_started, 0.0)
        cpu_count = os.cpu_count() or 1
        cpu_cores = process_cpu_seconds / wall_seconds if wall_seconds > 0 else 0.0
        host_percent = min(100.0, cpu_cores / cpu_count * 100.0)

        measurements = [
            self._measurement("process_cpu_seconds", process_cpu_seconds, "s"),
            self._measurement("process_cpu_cores", cpu_cores, "cores"),
            self._measurement("process_cpu_percent_of_host", host_percent, "%"),
        ]
        peak_rss = self._peak_rss_bytes()
        if peak_rss is not None:
            measurements.append(self._measurement("process_peak_rss_bytes", peak_rss, "bytes"))
        if hasattr(os, "getloadavg"):
            load_1m, load_5m, load_15m = os.getloadavg()
            measurements.extend(
                [
                    self._measurement("host_load_1m", load_1m, "load"),
                    self._measurement("host_load_5m", load_5m, "load"),
                    self._measurement("host_load_15m", load_15m, "load"),
                ]
            )

        stop_overhead_ns = perf_counter_ns() - overhead_started
        measurements.append(
            self._measurement(
                "collector_overhead_ms",
                (self._start_overhead_ns + stop_overhead_ns) / 1_000_000,
                "ms",
            )
        )
        self._run_id = None
        self._wall_started_ns = None
        self._process_cpu_started = None
        return tuple(measurements)

    def _measurement(self, name: str, value: float | int, unit: str) -> Measurement:
        return Measurement(
            name=name,
            value=float(value),
            unit=unit,
            scope=MeasurementScope.RUN,
            provenance=MeasurementProvenance.HOST,
            protocol_version=self.protocol_version,
        )

    @staticmethod
    def _peak_rss_bytes() -> int | None:
        if resource is None:
            return None
        usage = resource.getrusage(resource.RUSAGE_SELF)
        maximum = int(usage.ru_maxrss)
        if sys.platform == "darwin":
            return maximum
        return maximum * 1024
