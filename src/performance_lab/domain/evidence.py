"""Explicit local-only sample content evidence contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CONTENT_EVIDENCE_SCHEMA_VERSION: Literal[1] = 1


class EvidenceMode(StrEnum):
    """Persistence mode for prompt/model-output content."""

    AGGREGATE_SAFE = "aggregate_safe"
    EVIDENCE_RICH = "evidence_rich"


class SampleContentEvidence(BaseModel):
    """Potentially sensitive prompt/output content retained outside canonical Run bundles."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = CONTENT_EVIDENCE_SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    attempt: int = Field(default=1, gt=0)
    prompt: str = Field(min_length=1)
    response: str | None = None
