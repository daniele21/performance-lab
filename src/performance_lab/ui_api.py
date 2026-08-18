"""Thin versioned HTTP adapter for the local browser product."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from performance_lab.application import (
    BaselineSummaryReadModel,
    ComparisonReadModel,
    PolicySummaryReadModel,
    RunDetailReadModel,
    RunSummaryReadModel,
    SuiteSummaryReadModel,
    TargetSummaryReadModel,
    TestedModelReadModel,
    UIQueryService,
)
from performance_lab.storage import RunNotFoundError


def create_ui_app(queries: UIQueryService) -> FastAPI:
    """Create the local read API without moving domain ownership into transport code."""

    app = FastAPI(
        title="Performance Lab Local UI API",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "api_version": "v1"}

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

    @app.get("/api/v1/tested-models", response_model=list[TestedModelReadModel])
    def list_tested_models() -> tuple[TestedModelReadModel, ...]:
        return queries.list_tested_models()

    @app.get("/api/v1/targets", response_model=list[TargetSummaryReadModel])
    def list_targets() -> tuple[TargetSummaryReadModel, ...]:
        return queries.list_targets()

    @app.get("/api/v1/suites", response_model=list[SuiteSummaryReadModel])
    def list_suites() -> tuple[SuiteSummaryReadModel, ...]:
        return queries.list_suites()

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
