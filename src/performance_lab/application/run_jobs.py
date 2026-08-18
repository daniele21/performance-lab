"""Bounded server-owned lifecycle for local UI benchmark jobs."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import Run, RunStatus
from performance_lab.engine import ProgressEvent
from performance_lab.run_config import StarterRunConfig
from performance_lab.runner import RunExecutionResult, execute_starter_run


class RunJobError(RuntimeError):
    """Base class for local UI run lifecycle failures."""


class RunJobCapacityError(RunJobError):
    """Raised when the local process already owns an active benchmark job."""


class RunJobNotFoundError(RunJobError):
    """Raised when a requested job identifier is unknown."""


class FrozenConfigMismatchError(RunJobError):
    """Raised when the launch config no longer matches the reviewed digest."""


class RunJobState(StrEnum):
    STARTING = "starting"
    RUNNING = "running"
    CANCELLING = "cancelling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


_TERMINAL_JOB_STATES = {
    RunJobState.SUCCEEDED,
    RunJobState.FAILED,
    RunJobState.CANCELLED,
    RunJobState.INTERRUPTED,
}


class RunJobSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    api_version: str = "v1"
    job_id: str = Field(min_length=1)
    state: RunJobState
    revision: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    config_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    target_id: str | None = None
    model_id: str | None = None
    scenario: str | None = None
    phase: str | None = None
    completed_samples: int = Field(default=0, ge=0)
    total_samples: int = Field(default=0, ge=0)
    run_id: str | None = None
    run_status: RunStatus | None = None
    error_code: str | None = None
    error_message: str | None = None


class RunExecutor(Protocol):
    async def __call__(
        self,
        config: StarterRunConfig,
        *,
        progress_sink: Callable[[ProgressEvent], None] | None = None,
    ) -> RunExecutionResult: ...


class RunJobManager:
    """Own at most one active benchmark task per local Performance Lab process.

    The manager intentionally rejects excess launches instead of maintaining an
    unbounded queue. Progress is stored as the latest immutable snapshot, so SSE
    clients never require a growing per-client event buffer.
    """

    def __init__(
        self,
        *,
        executor: RunExecutor = execute_starter_run,
        recovered_runs: tuple[Run, ...] = (),
        poll_interval_seconds: float = 0.1,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        self._executor = executor
        self._poll_interval_seconds = poll_interval_seconds
        self._jobs: dict[str, RunJobSnapshot] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._active_job_id: str | None = None
        self._lock = asyncio.Lock()
        for run in recovered_runs:
            self._recover(run)

    def list_jobs(self) -> tuple[RunJobSnapshot, ...]:
        return tuple(
            sorted(
                self._jobs.values(),
                key=lambda item: (item.created_at, item.job_id),
                reverse=True,
            )
        )

    def get(self, job_id: str) -> RunJobSnapshot:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise RunJobNotFoundError(job_id) from exc

    async def launch(
        self,
        config: StarterRunConfig,
        *,
        config_digest: str,
        scenario: str | None = None,
    ) -> RunJobSnapshot:
        actual_digest = starter_run_config_digest(config)
        if actual_digest != config_digest:
            raise FrozenConfigMismatchError("launch config differs from frozen review")

        async with self._lock:
            if self._active_job_id is not None:
                active = self._jobs.get(self._active_job_id)
                if active is not None and active.state not in _TERMINAL_JOB_STATES:
                    raise RunJobCapacityError("one local benchmark job is already active")
                self._active_job_id = None

            now = datetime.now(UTC)
            job_id = f"job-{uuid4()}"
            snapshot = RunJobSnapshot(
                job_id=job_id,
                state=RunJobState.STARTING,
                revision=0,
                created_at=now,
                updated_at=now,
                config_digest=config_digest,
                target_id=config.target_id,
                model_id=config.model_id,
                scenario=scenario,
            )
            self._jobs[job_id] = snapshot
            self._active_job_id = job_id
            task = asyncio.create_task(self._execute(job_id, config), name=job_id)
            self._tasks[job_id] = task
            return snapshot

    async def cancel(self, job_id: str) -> RunJobSnapshot:
        async with self._lock:
            snapshot = self.get(job_id)
            if snapshot.state in _TERMINAL_JOB_STATES:
                return snapshot
            task = self._tasks.get(job_id)
            snapshot = self._replace(
                job_id,
                state=RunJobState.CANCELLING,
                phase="cancelling",
            )
            if task is not None and not task.done():
                task.cancel()

        if task is not None:
            with suppress(asyncio.CancelledError):
                await task
        return self.get(job_id)

    async def wait(self, job_id: str) -> RunJobSnapshot:
        task = self._tasks.get(job_id)
        if task is not None:
            with suppress(asyncio.CancelledError):
                await task
        return self.get(job_id)

    async def stream(
        self,
        job_id: str,
        *,
        after_revision: int = -1,
    ) -> AsyncIterator[RunJobSnapshot]:
        last_revision = after_revision
        while True:
            snapshot = self.get(job_id)
            if snapshot.revision > last_revision:
                yield snapshot
                last_revision = snapshot.revision
            if snapshot.state in _TERMINAL_JOB_STATES:
                return
            await asyncio.sleep(self._poll_interval_seconds)

    async def shutdown(self, *, timeout_seconds: float = 5.0) -> None:
        async with self._lock:
            job_id = self._active_job_id
            if job_id is None:
                return
            snapshot = self._jobs.get(job_id)
            task = self._tasks.get(job_id)
            if snapshot is None or task is None or task.done():
                self._active_job_id = None
                return
            self._replace(job_id, state=RunJobState.CANCELLING, phase="shutdown")
            task.cancel()

        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=timeout_seconds)
        except asyncio.CancelledError:
            pass
        except TimeoutError:
            self._replace(
                job_id,
                state=RunJobState.INTERRUPTED,
                phase="interrupted",
                error_code="shutdown_timeout",
                error_message="active benchmark did not stop before local process shutdown",
            )
        finally:
            async with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None

    async def _execute(self, job_id: str, config: StarterRunConfig) -> None:
        try:
            result = await self._executor(
                config,
                progress_sink=lambda event: self._on_progress(job_id, event),
            )
            state = _job_state_from_run_status(result.run.status)
            self._replace(
                job_id,
                state=state,
                phase="run_completed",
                completed_samples=len(result.run.samples),
                total_samples=max(
                    self.get(job_id).total_samples,
                    len(result.run.samples),
                ),
                run_id=result.run.run_id,
                run_status=result.run.status,
            )
        except asyncio.CancelledError:
            current = self.get(job_id)
            if current.state not in _TERMINAL_JOB_STATES:
                self._replace(
                    job_id,
                    state=RunJobState.CANCELLED,
                    phase="cancelled",
                )
            raise
        except Exception as exc:
            self._replace(
                job_id,
                state=RunJobState.FAILED,
                phase="failed",
                error_code=type(exc).__name__,
                error_message=_bounded_error_message(exc),
            )
        finally:
            async with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None

    def _on_progress(self, job_id: str, event: ProgressEvent) -> None:
        current = self.get(job_id)
        state = (
            RunJobState.CANCELLING
            if current.state == RunJobState.CANCELLING
            else RunJobState.RUNNING
        )
        self._replace(
            job_id,
            state=state,
            phase=event.phase.value,
            completed_samples=event.completed_samples,
            total_samples=event.total_samples,
            run_id=event.run_id,
        )

    def _replace(self, job_id: str, **changes: object) -> RunJobSnapshot:
        current = self.get(job_id)
        next_snapshot = current.model_copy(
            update={
                **changes,
                "revision": current.revision + 1,
                "updated_at": datetime.now(UTC),
            }
        )
        self._jobs[job_id] = next_snapshot
        return next_snapshot

    def _recover(self, run: Run) -> None:
        if run.status != RunStatus.RUNNING:
            return
        total_samples = run.fingerprint.load_profile.request_count
        now = datetime.now(UTC)
        job_id = f"interrupted-{run.run_id}"
        self._jobs[job_id] = RunJobSnapshot(
            job_id=job_id,
            state=RunJobState.INTERRUPTED,
            revision=0,
            created_at=run.created_at,
            updated_at=now,
            target_id=run.fingerprint.target_id,
            model_id=run.fingerprint.model.model_id,
            phase="interrupted",
            completed_samples=len(run.samples),
            total_samples=total_samples,
            run_id=run.run_id,
            run_status=run.status,
            error_code="process_restarted",
            error_message="working run was retained but was not published as completed evidence",
        )


def starter_run_config_digest(config: StarterRunConfig) -> str:
    canonical = json.dumps(
        config.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _job_state_from_run_status(status: RunStatus) -> RunJobState:
    if status == RunStatus.SUCCEEDED:
        return RunJobState.SUCCEEDED
    if status == RunStatus.CANCELLED:
        return RunJobState.CANCELLED
    return RunJobState.FAILED


def _bounded_error_message(exc: Exception) -> str:
    message = str(exc).strip() or type(exc).__name__
    return message[:500]
