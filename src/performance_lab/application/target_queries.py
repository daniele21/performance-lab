"""Target endpoint resolution for browser-initiated model discovery."""

from __future__ import annotations

from performance_lab.domain import EndpointProfile

from .planning_queries import UIQueryService as PlanningUIQueryService
from .ui_models import EndpointConnectionInput, TargetSummaryReadModel


class UIQueryService(PlanningUIQueryService):
    """Canonical UI queries plus safe endpoint resolution for configured target probes."""

    def get_target_probe_context(
        self,
        target_id: str,
    ) -> tuple[TargetSummaryReadModel, EndpointProfile, EndpointConnectionInput | None]:
        target = self._session_targets.get(target_id)
        if target is None:
            target = next((item for item in self.targets if item.target_id == target_id), None)
        if target is None:
            raise LookupError(f"target not found: {target_id}")

        endpoint = self._session_endpoint_profiles.get(target.endpoint_profile_id)
        if endpoint is None:
            endpoint = next(
                (
                    item
                    for item in self.endpoint_profiles
                    if item.profile_id == target.endpoint_profile_id
                ),
                None,
            )
        if endpoint is None:
            raise LookupError(f"endpoint profile not found: {target.endpoint_profile_id}")

        summary = next(item for item in self.list_targets() if item.target_id == target_id)
        return summary, endpoint, self._session_connections.get(target_id)
