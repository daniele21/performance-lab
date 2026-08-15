"""Optional runtime-native telemetry handshake for instrumented local endpoints."""

from __future__ import annotations

from datetime import datetime

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from performance_lab.domain import (
    HardwareIdentity,
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
    ModelIdentity,
    RuntimeIdentity,
)
from performance_lab.plugins import TelemetryCollectorCapabilities

RUNTIME_TELEMETRY_PROTOCOL_VERSION = "runtime-telemetry-v1"


class RuntimeTelemetryModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RuntimeTelemetryIdentity(RuntimeTelemetryModel):
    runtime: RuntimeIdentity = RuntimeIdentity()
    model: ModelIdentity | None = None
    hardware: HardwareIdentity = HardwareIdentity()


class RuntimeTelemetryStartResponse(RuntimeTelemetryModel):
    protocol_version: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    metric_names: tuple[str, ...] = ()
    identity: RuntimeTelemetryIdentity = RuntimeTelemetryIdentity()


class RuntimeTelemetryMeasurement(RuntimeTelemetryModel):
    name: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    scope: MeasurementScope = MeasurementScope.RUN
    observed_at: datetime | None = None


class RuntimeTelemetryStopResponse(RuntimeTelemetryModel):
    protocol_version: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    measurements: tuple[RuntimeTelemetryMeasurement, ...] = ()


class InstrumentedEndpointCollector:
    """Collect runtime-originated measurements without making telemetry mandatory."""

    collector_id = "instrumented-endpoint"
    protocol_version = RUNTIME_TELEMETRY_PROTOCOL_VERSION

    def __init__(self, base_url: str, *, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._run_id: str | None = None
        self._metric_names: frozenset[str] = frozenset()
        self._identity = RuntimeTelemetryIdentity()

    @property
    def identity(self) -> RuntimeTelemetryIdentity:
        return self._identity

    def capabilities(self) -> TelemetryCollectorCapabilities:
        return TelemetryCollectorCapabilities(metric_names=self._metric_names, sampling=False)

    async def start(self, run_id: str) -> None:
        if self._run_id is not None:
            raise RuntimeError("instrumented telemetry collector already started")
        payload = await self._post("telemetry/start", {"run_id": run_id})
        try:
            response = RuntimeTelemetryStartResponse.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("invalid runtime telemetry start response") from exc
        self._validate_response_identity(response.protocol_version, response.run_id, run_id)
        self._run_id = run_id
        self._metric_names = frozenset(response.metric_names)
        self._identity = response.identity

    async def stop(self) -> tuple[Measurement, ...]:
        run_id = self._run_id
        if run_id is None:
            raise RuntimeError("instrumented telemetry collector has not started")
        payload = await self._post("telemetry/stop", {"run_id": run_id})
        try:
            response = RuntimeTelemetryStopResponse.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("invalid runtime telemetry stop response") from exc
        self._validate_response_identity(response.protocol_version, response.run_id, run_id)
        self._run_id = None
        return tuple(
            Measurement(
                name=item.name,
                value=item.value,
                unit=item.unit,
                scope=item.scope,
                provenance=MeasurementProvenance.RUNTIME,
                protocol_version=self.protocol_version,
                observed_at=item.observed_at,
            )
            for item in response.measurements
        )

    async def _post(self, path: str, payload: dict[str, str]) -> object:
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(f"{self._base_url}/{path}", json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(f"runtime telemetry request failed: {path}") from exc

    def _validate_response_identity(
        self,
        protocol_version: str,
        response_run_id: str,
        expected_run_id: str,
    ) -> None:
        if protocol_version != self.protocol_version:
            raise RuntimeError(
                f"runtime telemetry protocol mismatch: {protocol_version!r} != "
                f"{self.protocol_version!r}"
            )
        if response_run_id != expected_run_id:
            raise RuntimeError("runtime telemetry response run_id mismatch")
