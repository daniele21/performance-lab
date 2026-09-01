"""Browser execution-policy overrides layered on canonical target/query behavior."""

from __future__ import annotations

from performance_lab.domain import EvidenceMode
from performance_lab.run_config import StarterRunConfig

from .run_jobs import starter_run_config_digest
from .target_queries import UIQueryService as TargetUIQueryService
from .ui_models import RunPreflightReadModel, RunPreflightRequest


class UIQueryService(TargetUIQueryService):
    """Apply product-owned retention defaults without changing CLI/campaign safety defaults.

    Direct ``Test a model`` runs are diagnostic and therefore evidence-rich. Campaign-derived
    runs remain aggregate-safe even if the UI server itself was started from a richer template.
    """

    def preflight(self, request: RunPreflightRequest) -> RunPreflightReadModel:
        prepared = super().preflight(request)
        if not prepared.can_run or prepared.preview is None:
            return prepared
        config = prepared.preview.config.model_copy(
            update={"evidence_mode": EvidenceMode.EVIDENCE_RICH}
        )
        preview = prepared.preview.model_copy(
            update={
                "config": config,
                "config_digest": starter_run_config_digest(config),
            }
        )
        return prepared.model_copy(update={"preview": preview})

    def _campaign_run_config(self, **kwargs: object) -> StarterRunConfig:
        config = super()._campaign_run_config(**kwargs)
        return config.model_copy(update={"evidence_mode": EvidenceMode.AGGREGATE_SAFE})
