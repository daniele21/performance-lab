"""Thin versioned HTTP adapter for the local browser product."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from performance_lab.application import (
    BaselineSummaryReadModel,
    BenchmarkDetailReadModel,
    CampaignCaseComparisonReadModel,
    CampaignCaseSummaryReadModel,
    CampaignPlanDigestMismatchError,
    CampaignPlanLaunchError,
    CampaignPlanningContextReadModel,
    CampaignPlanPreviewReadModel,
    CampaignPlanPreviewRequest,
    CampaignQueryService,
    CampaignReadModel,
    ComparisonReadModel,
    DatasetSummaryReadModel,
    EndpointConnectionInput,
    EndpointProbeReadModel,
    EvaluatorDefinitionReadModel,
    PolicySummaryReadModel,
    RunDetailReadModel,
    RunPreflightReadModel,
    RunPreflightRequest,
    RunSummaryReadModel,
    SampleEvidenceDetailReadModel,
    SampleSummaryReadModel,
    ScenarioSummaryReadModel,
    SuiteSummaryReadModel,
    TargetSummaryReadModel,
    TestedModelReadModel,
    UIQueryService,
    probe_endpoint_connection,
    probe_endpoint_profile,
)
from performance_lab.application.campaign_jobs import (
    CampaignCapacityError,
    CampaignJobManager,
    CampaignNotFoundJobError,
)
from performance_lab.application.run_jobs import (
    FrozenConfigMismatchError,
    RunJobCapacityError,
    RunJobManager,
    RunJobNotFoundError,
    RunJobSnapshot,
)
from performance_lab.storage import CampaignNotFoundError, RunNotFoundError


class RunLaunchRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    preflight: RunPreflightRequest
    config_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class CampaignLaunchRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    plan: CampaignPlanPreviewRequest
    plan_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


def create_ui_app(
    queries: UIQueryService,
    *,
    run_jobs: RunJobManager | None = None,
    campaign_jobs: CampaignJobManager | None = None,
    campaign_queries: CampaignQueryService | None = None,
) -> FastAPI:
    """Create the loopback UI API while keeping benchmark truth in application services."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if campaign_jobs is not None:
            await campaign_jobs.shutdown()
        if run_jobs is not None:
            await run_jobs.shutdown()

    app = FastAPI(
        title="Performance Lab Local UI API",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "api_version": "v1"}

    @app.post("/api/v1/endpoint-probes", response_model=EndpointProbeReadModel)
    async def probe_endpoint(request: EndpointConnectionInput) -> EndpointProbeReadModel:
        result = await probe_endpoint_connection(request)
        if not result.healthy:
            return result
        target = queries.register_session_connection(
            request,
            discovered_models=result.models,
            supported_generation_parameters=result.supported_generation_parameters,
        )
        return result.model_copy(update={"target": target})

    @app.post("/api/v1/targets/{target_id}/probe", response_model=EndpointProbeReadModel)
    async def probe_target_endpoint(target_id: str) -> EndpointProbeReadModel:
        try:
            target, endpoint, session_connection = queries.get_target_probe_context(target_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="target endpoint not found") from exc

        if session_connection is not None:
            result = await probe_endpoint_connection(session_connection)
        else:
            result = await probe_endpoint_profile(
                endpoint,
                endpoint_identity_value=target.endpoint_identity,
            )
        return result.model_copy(update={"target": target})

    @app.get("/api/v1/campaign-planning", response_model=CampaignPlanningContextReadModel)
    def campaign_planning() -> CampaignPlanningContextReadModel:
        return queries.campaign_planning_context()

    @app.post("/api/v1/campaign-plan-preview", response_model=CampaignPlanPreviewReadModel)
    def campaign_plan_preview(request: CampaignPlanPreviewRequest) -> CampaignPlanPreviewReadModel:
        return queries.preview_campaign_plan(request)

    @app.get("/api/v1/campaigns", response_model=list[CampaignReadModel])
    def list_campaigns() -> tuple[CampaignReadModel, ...]:
        _, read_queries = _require_campaigns(campaign_jobs, campaign_queries)
        return read_queries.list_campaigns()

    @app.post(
        "/api/v1/campaigns",
        response_model=CampaignReadModel,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def launch_campaign(request: CampaignLaunchRequest) -> CampaignReadModel:
        manager, read_queries = _require_campaigns(campaign_jobs, campaign_queries)
        try:
            plan = queries.prepare_campaign_launch(
                request.plan,
                expected_plan_digest=request.plan_digest,
            )
        except CampaignPlanDigestMismatchError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except CampaignPlanLaunchError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        try:
            campaign = await manager.launch(plan)
        except CampaignCapacityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return read_queries.get(campaign.campaign_id)

    @app.get("/api/v1/campaigns/{campaign_id}", response_model=CampaignReadModel)
    def get_campaign(campaign_id: str) -> CampaignReadModel:
        _, read_queries = _require_campaigns(campaign_jobs, campaign_queries)
        try:
            return read_queries.get(campaign_id)
        except CampaignNotFoundError as exc:
            raise HTTPException(status_code=404, detail="campaign not found") from exc

    @app.get(
        "/api/v1/campaigns/{campaign_id}/cases",
        response_model=list[CampaignCaseSummaryReadModel],
    )
    def list_campaign_cases(campaign_id: str) -> tuple[CampaignCaseSummaryReadModel, ...]:
        _, read_queries = _require_campaigns(campaign_jobs, campaign_queries)
        try:
            return read_queries.list_cases(campaign_id)
        except CampaignNotFoundError as exc:
            raise HTTPException(status_code=404, detail="campaign not found") from exc

    @app.get(
        "/api/v1/campaigns/{campaign_id}/cases/{task_id}/{sample_id}",
        response_model=CampaignCaseComparisonReadModel,
    )
    def compare_campaign_case(
        campaign_id: str,
        task_id: str,
        sample_id: str,
    ) -> CampaignCaseComparisonReadModel:
        _, read_queries = _require_campaigns(campaign_jobs, campaign_queries)
        try:
            return read_queries.compare_case(campaign_id, task_id, sample_id)
        except CampaignNotFoundError as exc:
            raise HTTPException(status_code=404, detail="campaign not found") from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="campaign case evidence not found") from exc

    @app.post("/api/v1/campaigns/{campaign_id}/cancel", response_model=CampaignReadModel)
    async def cancel_campaign(campaign_id: str) -> CampaignReadModel:
        manager, read_queries = _require_campaigns(campaign_jobs, campaign_queries)
        try:
            campaign = await manager.cancel(campaign_id)
        except CampaignNotFoundJobError as exc:
            raise HTTPException(status_code=404, detail="campaign not found") from exc
        return read_queries.get(campaign.campaign_id)

    @app.get("/api/v1/campaigns/{campaign_id}/events")
    def stream_campaign(
        campaign_id: str,
        after_revision: int = Query(default=-1, ge=-1),
    ) -> Response:
        manager, read_queries = _require_campaigns(campaign_jobs, campaign_queries)
        try:
            manager.get(campaign_id)
        except CampaignNotFoundJobError as exc:
            raise HTTPException(status_code=404, detail="campaign not found") from exc

        async def events() -> AsyncIterator[str]:
            async for _ in manager.stream(campaign_id, after_revision=after_revision):
                snapshot = read_queries.get(campaign_id)
                yield (
                    f"id: {snapshot.revision}\n"
                    "event: campaign\n"
                    f"data: {snapshot.model_dump_json()}\n\n"
                )

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/v1/runs", response_model=list[RunSummaryReadModel])
    def list_runs(
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> tuple[RunSummaryReadModel, ...]:
        return queries.list_runs(offset=offset, limit=limit)

    @app.get("/api/v1/runs/{run_id}", response_model=RunDetailReadModel)
    def get_run(run_id: str) -> RunDetailReadModel:
        try:
            return queries.get_run(run_id)
        except (LookupError, RunNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="completed run not found") from exc

    @app.get("/api/v1/runs/{run_id}/samples", response_model=list[SampleSummaryReadModel])
    def list_run_samples(run_id: str) -> tuple[SampleSummaryReadModel, ...]:
        try:
            return queries.list_run_samples(run_id)
        except (LookupError, RunNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="completed run not found") from exc

    @app.get(
        "/api/v1/runs/{run_id}/samples/{task_id}/{sample_id}/{attempt}",
        response_model=SampleEvidenceDetailReadModel,
    )
    def get_sample_evidence(
        run_id: str,
        task_id: str,
        sample_id: str,
        attempt: int = Path(ge=1),
    ) -> SampleEvidenceDetailReadModel:
        try:
            return queries.get_sample_evidence(run_id, task_id, sample_id, attempt)
        except (LookupError, RunNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="sample evidence not found") from exc

    @app.get("/api/v1/tested-models", response_model=list[TestedModelReadModel])
    def list_tested_models() -> tuple[TestedModelReadModel, ...]:
        return queries.list_tested_models()

    @app.get("/api/v1/targets", response_model=list[TargetSummaryReadModel])
    def list_targets() -> tuple[TargetSummaryReadModel, ...]:
        return queries.list_targets()

    @app.get("/api/v1/suites", response_model=list[SuiteSummaryReadModel])
    def list_suites() -> tuple[SuiteSummaryReadModel, ...]:
        return queries.list_suites()

    @app.get("/api/v1/benchmarks", response_model=list[SuiteSummaryReadModel])
    def list_benchmarks() -> tuple[SuiteSummaryReadModel, ...]:
        return queries.list_suites()

    @app.get(
        "/api/v1/benchmarks/{suite_id}/{suite_version}",
        response_model=BenchmarkDetailReadModel,
    )
    def get_benchmark(suite_id: str, suite_version: str) -> BenchmarkDetailReadModel:
        try:
            return queries.get_benchmark(suite_id, suite_version)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="benchmark definition not found") from exc

    @app.get("/api/v1/datasets", response_model=list[DatasetSummaryReadModel])
    def list_datasets() -> tuple[DatasetSummaryReadModel, ...]:
        return queries.list_datasets()

    @app.get("/api/v1/evaluators", response_model=list[EvaluatorDefinitionReadModel])
    def list_evaluators() -> tuple[EvaluatorDefinitionReadModel, ...]:
        return queries.list_evaluators()

    @app.get("/api/v1/scenarios", response_model=list[ScenarioSummaryReadModel])
    def list_scenarios() -> tuple[ScenarioSummaryReadModel, ...]:
        return queries.list_scenarios()

    @app.post("/api/v1/run-preflight", response_model=RunPreflightReadModel)
    def preflight(request: RunPreflightRequest) -> RunPreflightReadModel:
        return queries.preflight(request)

    @app.get("/api/v1/run-jobs", response_model=list[RunJobSnapshot])
    def list_run_jobs() -> tuple[RunJobSnapshot, ...]:
        manager = _require_run_jobs(run_jobs)
        return manager.list_jobs()

    @app.post(
        "/api/v1/run-jobs",
        response_model=RunJobSnapshot,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def launch_run(request: RunLaunchRequest) -> RunJobSnapshot:
        manager = _require_run_jobs(run_jobs)
        prepared = queries.preflight(request.preflight)
        if not prepared.can_run or prepared.preview is None:
            detail = [issue.message for issue in prepared.issues]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=detail or ["run preflight is not executable"],
            )
        if prepared.preview.config_digest != request.config_digest:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="frozen execution preview changed; review the run again",
            )
        try:
            return await manager.launch(
                prepared.preview.config,
                config_digest=request.config_digest,
                scenario=request.preflight.scenario.value,
            )
        except FrozenConfigMismatchError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RunJobCapacityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @app.get("/api/v1/run-jobs/{job_id}", response_model=RunJobSnapshot)
    def get_run_job(job_id: str) -> RunJobSnapshot:
        manager = _require_run_jobs(run_jobs)
        try:
            return manager.get(job_id)
        except RunJobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run job not found") from exc

    @app.post("/api/v1/run-jobs/{job_id}/cancel", response_model=RunJobSnapshot)
    async def cancel_run_job(job_id: str) -> RunJobSnapshot:
        manager = _require_run_jobs(run_jobs)
        try:
            return await manager.cancel(job_id)
        except RunJobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run job not found") from exc

    @app.get("/api/v1/run-jobs/{job_id}/events")
    def stream_run_job(
        job_id: str,
        after_revision: int = Query(default=-1, ge=-1),
    ) -> Response:
        manager = _require_run_jobs(run_jobs)
        try:
            manager.get(job_id)
        except RunJobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run job not found") from exc

        async def events() -> AsyncIterator[str]:
            async for snapshot in manager.stream(job_id, after_revision=after_revision):
                yield (
                    f"id: {snapshot.revision}\n"
                    "event: run_job\n"
                    f"data: {snapshot.model_dump_json()}\n\n"
                )

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/v1/baselines", response_model=list[BaselineSummaryReadModel])
    def list_baselines() -> tuple[BaselineSummaryReadModel, ...]:
        return queries.list_baselines()

    @app.get("/api/v1/regression-policies", response_model=list[PolicySummaryReadModel])
    def list_policies() -> tuple[PolicySummaryReadModel, ...]:
        return queries.list_policies()

    @app.get("/api/v1/comparisons", response_model=ComparisonReadModel)
    def compare(
        baseline_run_id: str = Query(min_length=1),
        candidate_run_id: str = Query(min_length=1),
    ) -> ComparisonReadModel:
        try:
            return queries.compare(baseline_run_id, candidate_run_id)
        except (LookupError, RunNotFoundError) as exc:
            raise HTTPException(
                status_code=404, detail="completed comparison run not found"
            ) from exc

    return app


def _require_run_jobs(run_jobs: RunJobManager | None) -> RunJobManager:
    if run_jobs is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="run lifecycle is not configured for this local process",
        )
    return run_jobs


def _require_campaigns(
    campaign_jobs: CampaignJobManager | None,
    campaign_queries: CampaignQueryService | None,
) -> tuple[CampaignJobManager, CampaignQueryService]:
    if campaign_jobs is None or campaign_queries is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="campaign lifecycle is not configured for this local process",
        )
    return campaign_jobs, campaign_queries
