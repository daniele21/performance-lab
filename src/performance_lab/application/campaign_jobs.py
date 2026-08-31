"""Bounded server-owned execution lifecycle for evaluation campaigns."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from performance_lab.domain import (
    TERMINAL_CAMPAIGN_ENTRY_STATUSES,
    TERMINAL_CAMPAIGN_STATUSES,
    Campaign,
    CampaignEntry,
    CampaignEntryStatus,
    CampaignStatus,
    DecisionPolicyRef,
    RunStatus,
)
from performance_lab.engine import ProgressEvent
from performance_lab.run_config import StarterRunConfig
from performance_lab.runner import RunExecutionResult, execute_starter_run
from performance_lab.storage import CampaignNotFoundError, SQLiteCampaignStore

from .evaluation_capacity import EvaluationCapacity, EvaluationCapacityError
from .run_jobs import starter_run_config_digest


class CampaignJobError(RuntimeError):
    pass


class CampaignCapacityError(CampaignJobError):
    pass


class CampaignNotFoundJobError(CampaignJobError):
    pass


@dataclass(frozen=True, slots=True)
class CampaignRunSpec:
    candidate_id: str
    model_id: str
    config: StarterRunConfig


@dataclass(frozen=True, slots=True)
class CampaignLaunchPlan:
    plan_digest: str
    use_case_id: str
    use_case_version: str
    target_id: str
    suite_id: str
    suite_version: str
    decision_policy: DecisionPolicyRef
    runs: tuple[CampaignRunSpec, ...]


class CampaignRunExecutor(Protocol):
    async def __call__(
        self,
        config: StarterRunConfig,
        *,
        progress_sink: Callable[[ProgressEvent], None] | None = None,
    ) -> RunExecutionResult: ...


class CampaignJobManager:
    """Execute one bounded campaign at a time while preserving immutable Run ownership."""

    def __init__(
        self,
        store: SQLiteCampaignStore,
        *,
        capacity: EvaluationCapacity,
        executor: CampaignRunExecutor = execute_starter_run,
        poll_interval_seconds: float = 0.1,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        self._store = store
        self._capacity = capacity
        self._executor = executor
        self._poll_interval_seconds = poll_interval_seconds
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._active_campaign_id: str | None = None
        self._cancel_requested: set[str] = set()
        self._shutdown_requested: set[str] = set()
        self._lock = asyncio.Lock()
        self._recover_interrupted()

    def list_campaigns(self) -> tuple[Campaign, ...]:
        return tuple(
            sorted(
                self._store.list_all(),
                key=lambda item: (item.created_at, item.campaign_id),
                reverse=True,
            )
        )

    def get(self, campaign_id: str) -> Campaign:
        try:
            return self._store.get(campaign_id)
        except CampaignNotFoundError as exc:
            raise CampaignNotFoundJobError(campaign_id) from exc

    async def launch(self, plan: CampaignLaunchPlan) -> Campaign:
        if not plan.runs:
            raise ValueError("campaign launch plan requires at least one run")
        if len(plan.runs) > 32:
            raise ValueError("campaign launch plan cannot exceed 32 runs")

        campaign_id = f"campaign-{uuid4()}"
        owner_id = _capacity_owner(campaign_id)
        async with self._lock:
            if self._active_campaign_id is not None:
                active = self.get(self._active_campaign_id)
                if active.status not in TERMINAL_CAMPAIGN_STATUSES:
                    raise CampaignCapacityError("one local evaluation campaign is already active")
                self._active_campaign_id = None
            try:
                await self._capacity.acquire(owner_id)
            except EvaluationCapacityError as exc:
                raise CampaignCapacityError("local evaluation capacity is already in use") from exc

            now = datetime.now(UTC)
            prepared_specs: list[CampaignRunSpec] = []
            entries: list[CampaignEntry] = []
            for index, spec in enumerate(plan.runs):
                run_id = spec.config.run_id or f"run-{uuid4()}"
                config = spec.config.model_copy(update={"run_id": run_id})
                prepared_specs.append(
                    CampaignRunSpec(
                        candidate_id=spec.candidate_id,
                        model_id=spec.model_id,
                        config=config,
                    )
                )
                entries.append(
                    CampaignEntry(
                        entry_id=f"entry-{index + 1}",
                        candidate_id=spec.candidate_id,
                        model_id=spec.model_id,
                        config_digest=starter_run_config_digest(config),
                    )
                )
            campaign = Campaign(
                campaign_id=campaign_id,
                plan_digest=plan.plan_digest,
                use_case_id=plan.use_case_id,
                use_case_version=plan.use_case_version,
                target_id=plan.target_id,
                suite_id=plan.suite_id,
                suite_version=plan.suite_version,
                decision_policy=plan.decision_policy,
                status=CampaignStatus.QUEUED,
                created_at=now,
                updated_at=now,
                entries=tuple(entries),
            )
            try:
                self._store.save(campaign)
                self._active_campaign_id = campaign_id
                task = asyncio.create_task(
                    self._execute(campaign_id, tuple(prepared_specs)),
                    name=campaign_id,
                )
            except Exception:
                self._active_campaign_id = None
                await self._capacity.release(owner_id)
                raise
            self._tasks[campaign_id] = task
            return campaign

    async def cancel(self, campaign_id: str) -> Campaign:
        async with self._lock:
            campaign = self.get(campaign_id)
            if campaign.status in TERMINAL_CAMPAIGN_STATUSES:
                return campaign
            self._cancel_requested.add(campaign_id)
            campaign = self._replace_campaign(campaign, status=CampaignStatus.CANCELLING)
            task = self._tasks.get(campaign_id)
            if task is not None and not task.done():
                task.cancel()

        if task is not None:
            with suppress(asyncio.CancelledError):
                await task
        return self.get(campaign_id)

    async def stream(
        self,
        campaign_id: str,
        *,
        after_revision: int = -1,
    ) -> AsyncIterator[Campaign]:
        revision = after_revision
        while True:
            campaign = self.get(campaign_id)
            if campaign.revision > revision:
                yield campaign
                revision = campaign.revision
            if campaign.status in TERMINAL_CAMPAIGN_STATUSES:
                return
            await asyncio.sleep(self._poll_interval_seconds)

    async def shutdown(self, *, timeout_seconds: float = 5.0) -> None:
        async with self._lock:
            campaign_id = self._active_campaign_id
            if campaign_id is None:
                return
            campaign = self.get(campaign_id)
            if campaign.status in TERMINAL_CAMPAIGN_STATUSES:
                self._active_campaign_id = None
                return
            self._shutdown_requested.add(campaign_id)
            self._replace_campaign(campaign, status=CampaignStatus.CANCELLING)
            task = self._tasks.get(campaign_id)
            if task is not None and not task.done():
                task.cancel()

        if task is not None:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=timeout_seconds)
            except (asyncio.CancelledError, TimeoutError):
                pass

    async def _execute(
        self,
        campaign_id: str,
        specs: tuple[CampaignRunSpec, ...],
    ) -> None:
        owner_id = _capacity_owner(campaign_id)
        try:
            self._replace_campaign(self.get(campaign_id), status=CampaignStatus.RUNNING)
            for index, spec in enumerate(specs):
                if self._stop_requested(campaign_id):
                    break
                self._replace_entry(
                    campaign_id,
                    index,
                    status=CampaignEntryStatus.RUNNING,
                    run_id=spec.config.run_id,
                )
                try:
                    result = await self._executor(
                        spec.config,
                        progress_sink=lambda event, entry_index=index: self._on_progress(
                            campaign_id,
                            entry_index,
                            event,
                        ),
                    )
                    self._finish_entry_from_run(campaign_id, index, result)
                except asyncio.CancelledError:
                    if self._stop_requested(campaign_id):
                        self._replace_entry(
                            campaign_id,
                            index,
                            status=(
                                CampaignEntryStatus.INTERRUPTED
                                if campaign_id in self._shutdown_requested
                                else CampaignEntryStatus.CANCELLED
                            ),
                        )
                        break
                    raise
                except Exception as exc:
                    self._replace_entry(
                        campaign_id,
                        index,
                        status=CampaignEntryStatus.FAILED,
                        error_code=type(exc).__name__,
                        error_message=_bounded_error_message(exc),
                    )

                if self._stop_requested(campaign_id):
                    break

            self._finalize(campaign_id)
        except asyncio.CancelledError:
            self._finalize(campaign_id)
        finally:
            await self._capacity.release(owner_id)
            async with self._lock:
                if self._active_campaign_id == campaign_id:
                    self._active_campaign_id = None
            self._cancel_requested.discard(campaign_id)
            self._shutdown_requested.discard(campaign_id)

    def _finish_entry_from_run(
        self,
        campaign_id: str,
        index: int,
        result: RunExecutionResult,
    ) -> None:
        if result.run.status == RunStatus.SUCCEEDED:
            status = CampaignEntryStatus.SUCCEEDED
            error_code = None
            error_message = None
        elif result.run.status == RunStatus.CANCELLED:
            status = (
                CampaignEntryStatus.INTERRUPTED
                if campaign_id in self._shutdown_requested
                else CampaignEntryStatus.CANCELLED
            )
            error_code = "process_shutdown" if status == CampaignEntryStatus.INTERRUPTED else None
            error_message = (
                "campaign execution was interrupted by local process shutdown"
                if status == CampaignEntryStatus.INTERRUPTED
                else None
            )
        else:
            status = CampaignEntryStatus.FAILED
            error_code = "run_failed"
            error_message = "the immutable run completed with failed status"
        self._replace_entry(
            campaign_id,
            index,
            status=status,
            run_id=result.run.run_id,
            completed_samples=len(result.run.samples),
            total_samples=max(len(result.run.samples), result.run.fingerprint.load_profile.request_count),
            error_code=error_code,
            error_message=error_message,
        )

    def _on_progress(self, campaign_id: str, index: int, event: ProgressEvent) -> None:
        campaign = self.get(campaign_id)
        if campaign.status in TERMINAL_CAMPAIGN_STATUSES:
            return
        current = campaign.entries[index]
        if current.status in TERMINAL_CAMPAIGN_ENTRY_STATUSES:
            return
        self._replace_entry(
            campaign_id,
            index,
            status=CampaignEntryStatus.RUNNING,
            run_id=event.run_id,
            completed_samples=event.completed_samples,
            total_samples=event.total_samples,
        )

    def _finalize(self, campaign_id: str) -> Campaign:
        campaign = self.get(campaign_id)
        shutdown = campaign_id in self._shutdown_requested
        cancelled = campaign_id in self._cancel_requested
        if shutdown:
            entry_status = CampaignEntryStatus.INTERRUPTED
            campaign_status = CampaignStatus.INTERRUPTED
            error_code = "process_shutdown"
            error_message = "campaign execution was interrupted by local process shutdown"
        elif cancelled:
            entry_status = CampaignEntryStatus.CANCELLED
            campaign_status = CampaignStatus.CANCELLED
            error_code = None
            error_message = None
        else:
            entry_status = CampaignEntryStatus.CANCELLED
            failed = any(
                entry.status in {CampaignEntryStatus.FAILED, CampaignEntryStatus.INTERRUPTED}
                for entry in campaign.entries
            )
            campaign_status = CampaignStatus.FAILED if failed else CampaignStatus.SUCCEEDED
            error_code = "one_or_more_runs_failed" if failed else None
            error_message = (
                "one or more planned runs did not produce successful immutable evidence"
                if failed
                else None
            )

        entries = tuple(
            entry
            if entry.status in TERMINAL_CAMPAIGN_ENTRY_STATUSES
            else entry.model_copy(
                update={
                    "status": entry_status,
                    **(
                        {
                            "error_code": "process_shutdown",
                            "error_message": "campaign entry did not complete before process shutdown",
                        }
                        if entry_status == CampaignEntryStatus.INTERRUPTED
                        else {}
                    ),
                }
            )
            for entry in campaign.entries
        )
        now = datetime.now(UTC)
        return self._replace_campaign(
            campaign,
            status=campaign_status,
            entries=entries,
            completed_at=now,
            error_code=error_code,
            error_message=error_message,
        )

    def _replace_entry(self, campaign_id: str, index: int, **changes: object) -> Campaign:
        campaign = self.get(campaign_id)
        entries = list(campaign.entries)
        entries[index] = entries[index].model_copy(update=changes)
        return self._replace_campaign(campaign, entries=tuple(entries))

    def _replace_campaign(self, campaign: Campaign, **changes: object) -> Campaign:
        updated = campaign.model_copy(
            update={
                **changes,
                "revision": campaign.revision + 1,
                "updated_at": datetime.now(UTC),
            }
        )
        self._store.save(updated)
        return updated

    def _stop_requested(self, campaign_id: str) -> bool:
        return campaign_id in self._cancel_requested or campaign_id in self._shutdown_requested

    def _recover_interrupted(self) -> None:
        now = datetime.now(UTC)
        for campaign in self._store.list_active():
            entries = tuple(
                entry
                if entry.status in TERMINAL_CAMPAIGN_ENTRY_STATUSES
                else entry.model_copy(
                    update={
                        "status": CampaignEntryStatus.INTERRUPTED,
                        "error_code": "process_restarted",
                        "error_message": "campaign entry was active when the local process restarted",
                    }
                )
                for entry in campaign.entries
            )
            recovered = campaign.model_copy(
                update={
                    "status": CampaignStatus.INTERRUPTED,
                    "revision": campaign.revision + 1,
                    "updated_at": now,
                    "completed_at": now,
                    "entries": entries,
                    "error_code": "process_restarted",
                    "error_message": "campaign was active when the local process restarted",
                }
            )
            self._store.save(recovered)


def _capacity_owner(campaign_id: str) -> str:
    return f"campaign:{campaign_id}"


def _bounded_error_message(exc: Exception) -> str:
    message = str(exc).strip() or type(exc).__name__
    return message[:500]
