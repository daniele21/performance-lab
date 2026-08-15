"""Versioned configuration for the executable CLI evaluation path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError

from performance_lab.domain import EndpointProfile, HardwareIdentity

RUN_CONFIG_VERSION: Literal[1] = 1


class RunConfigError(ValueError):
    pass


class LocalLLMServerTelemetryConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    base_url: HttpUrl
    model_id: str | None = Field(default=None, min_length=1)
    sample_interval_seconds: float = Field(default=0.05, gt=0, le=60)
    timeout_seconds: float = Field(default=2.0, gt=0, le=120)


class LocalLLMServerIdentityConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    base_url: HttpUrl
    model_id: str | None = Field(default=None, min_length=1)
    timeout_seconds: float = Field(default=2.0, gt=0, le=120)
    required: bool = False


class StarterRunConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = RUN_CONFIG_VERSION
    target_id: str = Field(min_length=1)
    endpoint_identity: str = Field(min_length=1)
    endpoint: EndpointProfile
    model_id: str = Field(min_length=1)
    store_path: Path = Path(".performance-lab/runs.sqlite3")
    run_id: str | None = Field(default=None, min_length=1)
    use_host_telemetry: bool = False
    local_llm_server_telemetry: LocalLLMServerTelemetryConfig | None = None
    local_llm_server_identity: LocalLLMServerIdentityConfig | None = None
    hardware: HardwareIdentity = Field(default_factory=HardwareIdentity)
    suite_id: Literal["general-diagnostic-starter"] = "general-diagnostic-starter"


def load_starter_run_config(path: Path) -> StarterRunConfig:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RunConfigError(f"cannot read run config: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RunConfigError("run config is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise RunConfigError("run config must be a JSON object")
    if raw.get("schema_version") != RUN_CONFIG_VERSION:
        raise RunConfigError(
            f"unsupported run config schema_version={raw.get('schema_version')!r}; "
            f"expected {RUN_CONFIG_VERSION}"
        )
    try:
        return StarterRunConfig.model_validate(raw)
    except ValidationError as exc:
        raise RunConfigError(str(exc)) from exc
