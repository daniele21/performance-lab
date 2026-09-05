"""Versioned repeatability endpoint attached to the local product API."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from performance_lab.application import RepeatabilityReadModel, UIQueryService


def attach_repeatability_api(app: FastAPI, queries: UIQueryService) -> None:
    """Attach exact-fingerprint repeatability reads before the built frontend root mount."""

    @app.get("/api/v1/runs/{run_id}/repeatability", response_model=RepeatabilityReadModel)
    def repeatability(run_id: str) -> RepeatabilityReadModel:
        try:
            return queries.repeatability(run_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="completed run not found") from exc
