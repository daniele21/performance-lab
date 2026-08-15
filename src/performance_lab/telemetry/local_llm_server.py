"""Runtime-native polling collector for daniele21/local-llm-server status evidence."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from performance_lab.domain import (
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
)
from performance_lab.plugins import TelemetryCollectorCapabilities

LOCAL_LLM_SERVER_STATUS_PROTOCOL_VERSION = "local-llm-server-status-v1"

_METRIC_NAMES = frozenset(
    {
        "status_sample_count",
        "status_sample_error_count",
        "status_observed_seconds",
        "peak_active_requests",
        "active_sample_ratio",
        "generating_sample_ratio",
        "prompt_eval_sample_ratio",
        "peak_chunks_per_second",
        "peak_request_output_chunks_observed",
        "peak_request_output_characters_observed",
        "max_concurrent_requests_reported",
    }
)


@dataclass(frozen=True, slots=True)
class _StatusSample:
    observed_at_monotonic: float
    active_requests: int
    max_concurrent_requests: int
    phase: str
    chunks_per_second: float
    output_chunks: int
    output_characters: int


class LocalLLMServerStatusCollector:
    """Poll the existing `/status` endpoint without requiring server-side instrumentation changes."""

    collector_id = "local-llm-server-status"
    protocol_version = LOCAL_LLM_SERVER_STATUS_PROTOCOL_VERSION

    def __init__(
        self,
        base_url: str,
        *,
        model_id: str | None = None,
        sample_interval_seconds: float = 0.05,
        timeout_seconds: float = 2.0,
    ) -> None:
        if sample_interval_seconds <= 0:
            raise ValueError("sample_interval_seconds must be positive")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._base_url = base_url.rstrip("/")
        self._configured_model_id = model_id
        self._selected_model_id: str | None = None
        self._sample_interval_seconds = sample_interval_seconds
        self._timeout_seconds = timeout_seconds
        self._client: httpx.AsyncClient | None = None
        self._samples: list[_StatusSample] = []
        self._sample_errors = 0
        self._run_id: str | None = None
        self._started_at_monotonic: float | None = None
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task[None] | None = None

    @property
    def selected_model_id(self) -> str | None:
        return self._selected_model_id

    def capabilities(self) -> TelemetryCollectorCapabilities:
        return TelemetryCollectorCapabilities(metric_names=_METRIC_NAMES, sampling=True)

    async def start(self, run_id: str) -> None:
        if self._run_id is not None:
            raise RuntimeError("local-llm-server status collector already started")
        self._client = httpx.AsyncClient(timeout=self._timeout_seconds)
        self._run_id = run_id
        self._started_at_monotonic = time.monotonic()
        self._samples = []
        self._sample_errors = 0
        self._stop_event = asyncio.Event()
        try:
            self._samples.append(await self._fetch_sample())
        except RuntimeError:
            await self._close_client()
            self._reset_state()
            raise
        self._task = asyncio.create_task(self._sample_loop())

    async def stop(self) -> tuple[Measurement, ...]:
        if self._run_id is None or self._started_at_monotonic is None:
            raise RuntimeError("local-llm-server status collector has not started")
        if self._stop_event is not None:
            self._stop_event.set()
        if self._task is not None:
            await self._task
        try:
            self._samples.append(await self._fetch_sample())
        except RuntimeError:
            self._sample_errors += 1
        observed_seconds = max(0.0, time.monotonic() - self._started_at_monotonic)
        measurements = _aggregate_samples(
            tuple(self._samples),
            sample_errors=self._sample_errors,
            observed_seconds=observed_seconds,
            protocol_version=self.protocol_version,
        )
        await self._close_client()
        self._reset_state()
        return measurements

    async def _sample_loop(self) -> None:
        stop_event = self._stop_event
        if stop_event is None:
            return
        while not stop_event.is_set():
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=self._sample_interval_seconds,
                )
            except TimeoutError:
                try:
                    self._samples.append(await self._fetch_sample())
                except RuntimeError:
                    self._sample_errors += 1

    async def _fetch_sample(self) -> _StatusSample:
        client = self._client
        if client is None:
            raise RuntimeError("status collector HTTP client is not initialized")
        try:
            response = await client.get(f"{self._base_url}/status")
            response.raise_for_status()
            payload: object = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("local-llm-server /status request failed") from exc
        status = self._select_status(payload)
        return _parse_status_sample(status)

    def _select_status(self, payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            raise RuntimeError("local-llm-server /status payload must be an object")
        models = payload.get("models")
        selected = self._configured_model_id
        if selected is None:
            default_model = payload.get("default_model")
            if isinstance(default_model, str) and default_model:
                selected = default_model
        if isinstance(models, dict):
            if selected is None and len(models) == 1:
                selected = next(iter(models))
            if selected is None:
                raise RuntimeError("cannot select local-llm-server runtime from /status")
            model_status = models.get(selected)
            if not isinstance(model_status, dict):
                raise RuntimeError(f"model is missing from local-llm-server /status: {selected}")
            self._selected_model_id = selected
            return model_status
        if selected is not None:
            self._selected_model_id = selected
        return payload

    async def _close_client(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _reset_state(self) -> None:
        self._run_id = None
        self._started_at_monotonic = None
        self._stop_event = None
        self._task = None


def _parse_status_sample(payload: dict[str, object]) -> _StatusSample:
    return _StatusSample(
        observed_at_monotonic=time.monotonic(),
        active_requests=_non_negative_int(payload.get("active_requests")),
        max_concurrent_requests=_non_negative_int(payload.get("max_concurrent_requests")),
        phase=str(payload.get("phase") or "unknown"),
        chunks_per_second=_non_negative_float(payload.get("chunks_per_second")),
        output_chunks=_non_negative_int(payload.get("output_chunks")),
        output_characters=_non_negative_int(payload.get("output_characters")),
    )


def _non_negative_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, float) and value >= 0:
        return int(value)
    return 0


def _non_negative_float(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return 0.0


def _aggregate_samples(
    samples: tuple[_StatusSample, ...],
    *,
    sample_errors: int,
    observed_seconds: float,
    protocol_version: str,
) -> tuple[Measurement, ...]:
    if not samples:
        raise RuntimeError("local-llm-server status collector produced no samples")
    sample_count = len(samples)
    active_count = sum(sample.active_requests > 0 for sample in samples)
    generating_count = sum(sample.phase == "generating" for sample in samples)
    prompt_eval_count = sum(sample.phase == "prompt_eval" for sample in samples)
    observed_at = datetime.now(UTC)

    values = (
        ("status_sample_count", float(sample_count), "count"),
        ("status_sample_error_count", float(sample_errors), "count"),
        ("status_observed_seconds", observed_seconds, "seconds"),
        ("peak_active_requests", float(max(sample.active_requests for sample in samples)), "count"),
        ("active_sample_ratio", active_count / sample_count, "ratio"),
        ("generating_sample_ratio", generating_count / sample_count, "ratio"),
        ("prompt_eval_sample_ratio", prompt_eval_count / sample_count, "ratio"),
        (
            "peak_chunks_per_second",
            max(sample.chunks_per_second for sample in samples),
            "chunks/s",
        ),
        (
            "peak_request_output_chunks_observed",
            float(max(sample.output_chunks for sample in samples)),
            "chunks",
        ),
        (
            "peak_request_output_characters_observed",
            float(max(sample.output_characters for sample in samples)),
            "characters",
        ),
        (
            "max_concurrent_requests_reported",
            float(max(sample.max_concurrent_requests for sample in samples)),
            "count",
        ),
    )
    return tuple(
        Measurement(
            name=name,
            value=value,
            unit=unit,
            scope=MeasurementScope.RUN,
            provenance=MeasurementProvenance.RUNTIME,
            protocol_version=protocol_version,
            observed_at=observed_at,
        )
        for name, value, unit in values
    )
