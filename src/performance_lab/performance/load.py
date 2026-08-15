"""Fixed-count and bounded-duration concurrency/load protocol."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from enum import StrEnum
from time import perf_counter_ns

from pydantic import BaseModel, ConfigDict, Field, model_validator

from performance_lab.plugins import (
    InferenceAdapter,
    InferenceAdapterError,
    InferenceErrorCode,
    InferenceRequest,
)

from .single_request import MetricAvailability, benchmark_single_request


class LoadModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class LoadAttemptStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMEOUT = "timeout"


class LoadProfileSpec(LoadModel):
    concurrency: int = Field(default=1, gt=0)
    request_count: int | None = Field(default=None, gt=0)
    duration_seconds: float | None = Field(default=None, gt=0)
    streaming: bool = True

    @model_validator(mode="after")
    def exactly_one_termination_mode(self) -> LoadProfileSpec:
        if (self.request_count is None) == (self.duration_seconds is None):
            raise ValueError("set exactly one of request_count or duration_seconds")
        return self


class LoadAttempt(LoadModel):
    sequence: int = Field(ge=0)
    request_id: str = Field(min_length=1)
    status: LoadAttemptStatus
    latency_ms: float | None = Field(default=None, ge=0)
    queue_delay_ms: float = Field(ge=0)
    error_code: str | None = None


class LoadTestResult(LoadModel):
    protocol_version: str = "load-v1"
    profile: LoadProfileSpec
    duration_ms: float = Field(ge=0)
    attempts: tuple[LoadAttempt, ...]
    success_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    timeout_count: int = Field(ge=0)
    requests_per_second: float = Field(ge=0)
    latency_ms: tuple[float, ...]
    queue_delay_ms: tuple[float, ...]

    @property
    def success_rate(self) -> float:
        return self.success_count / len(self.attempts) if self.attempts else 0.0


RequestFactory = Callable[[int], InferenceRequest]


async def run_load_profile(
    adapter: InferenceAdapter,
    request_factory: RequestFactory,
    profile: LoadProfileSpec,
) -> LoadTestResult:
    """Execute one bounded load profile and preserve raw latency/backpressure samples."""

    started_ns = perf_counter_ns()
    attempts: list[LoadAttempt] = []
    lock = asyncio.Lock()
    next_sequence = 0
    deadline_ns = (
        started_ns + int(profile.duration_seconds * 1_000_000_000)
        if profile.duration_seconds is not None
        else None
    )

    async def record(attempt: LoadAttempt) -> None:
        async with lock:
            attempts.append(attempt)

    async def execute(sequence: int, queued_ns: int) -> None:
        started_request_ns = perf_counter_ns()
        request = request_factory(sequence)
        queue_delay_ms = max(0.0, (started_request_ns - queued_ns) / 1_000_000)
        try:
            benchmark = await benchmark_single_request(
                adapter,
                request,
                streaming=profile.streaming,
            )
        except InferenceAdapterError as exc:
            status = (
                LoadAttemptStatus.TIMEOUT
                if exc.code == InferenceErrorCode.TIMEOUT
                else LoadAttemptStatus.FAILED
            )
            await record(
                LoadAttempt(
                    sequence=sequence,
                    request_id=request.request_id,
                    status=status,
                    queue_delay_ms=queue_delay_ms,
                    error_code=exc.code.value,
                )
            )
            return
        latency_metric = benchmark.metric("total_latency_ms")
        latency = (
            latency_metric.measurement.value
            if latency_metric.availability == MetricAvailability.AVAILABLE
            and latency_metric.measurement is not None
            else None
        )
        await record(
            LoadAttempt(
                sequence=sequence,
                request_id=request.request_id,
                status=LoadAttemptStatus.SUCCEEDED,
                latency_ms=latency,
                queue_delay_ms=queue_delay_ms,
            )
        )

    if profile.request_count is not None:
        queue: asyncio.Queue[tuple[int, int] | None] = asyncio.Queue()
        for sequence in range(profile.request_count):
            queue.put_nowait((sequence, perf_counter_ns()))
        for _ in range(profile.concurrency):
            queue.put_nowait(None)

        async def count_worker() -> None:
            while True:
                item = await queue.get()
                try:
                    if item is None:
                        return
                    sequence, queued_ns = item
                    await execute(sequence, queued_ns)
                finally:
                    queue.task_done()

        workers = [asyncio.create_task(count_worker()) for _ in range(profile.concurrency)]
        await queue.join()
        await asyncio.gather(*workers)
    else:
        assert deadline_ns is not None

        async def duration_worker() -> None:
            nonlocal next_sequence
            while perf_counter_ns() < deadline_ns:
                async with lock:
                    sequence = next_sequence
                    next_sequence += 1
                await execute(sequence, perf_counter_ns())

        workers = [asyncio.create_task(duration_worker()) for _ in range(profile.concurrency)]
        await asyncio.gather(*workers)

    completed_ns = perf_counter_ns()
    duration_ms = max(0.0, (completed_ns - started_ns) / 1_000_000)
    ordered = tuple(sorted(attempts, key=lambda attempt: attempt.sequence))
    success_count = sum(attempt.status == LoadAttemptStatus.SUCCEEDED for attempt in ordered)
    timeout_count = sum(attempt.status == LoadAttemptStatus.TIMEOUT for attempt in ordered)
    error_count = sum(attempt.status == LoadAttemptStatus.FAILED for attempt in ordered)
    seconds = duration_ms / 1000
    throughput = success_count / seconds if seconds > 0 else 0.0
    return LoadTestResult(
        profile=profile,
        duration_ms=duration_ms,
        attempts=ordered,
        success_count=success_count,
        error_count=error_count,
        timeout_count=timeout_count,
        requests_per_second=throughput,
        latency_ms=tuple(
            attempt.latency_ms for attempt in ordered if attempt.latency_ms is not None
        ),
        queue_delay_ms=tuple(attempt.queue_delay_ms for attempt in ordered),
    )
