"""Versioned regression endpoint attached to the local product API."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, status

from performance_lab.application import RegressionEvaluationReadModel, UIQueryService


def attach_regression_api(app: FastAPI, queries: UIQueryService) -> None:
    """Attach policy-backed regression routes before the built frontend root mount."""

    @app.get("/api/v1/regression-evaluations", response_model=RegressionEvaluationReadModel)
    def evaluate_regression(
        baseline_run_id: str = Query(min_length=1),
        candidate_run_id: str = Query(min_length=1),
        policy_id: str = Query(min_length=1),
        policy_version: str = Query(min_length=1),
    ) -> RegressionEvaluationReadModel:
        try:
            return queries.evaluate_regression(
                baseline_run_id=baseline_run_id,
                candidate_run_id=candidate_run_id,
                policy_id=policy_id,
                policy_version=policy_version,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
