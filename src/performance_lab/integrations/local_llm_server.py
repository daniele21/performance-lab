"""Identity client for the public daniele21/local-llm-server contract."""

from __future__ import annotations

from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from performance_lab.domain import HardwareIdentity, ModelIdentity, RuntimeIdentity

LOCAL_LLM_IDENTITY_PROTOCOL_VERSION: Literal["local-llm-identity-v1"] = "local-llm-identity-v1"


class LocalLLMServerIdentityError(RuntimeError):
    """Raised when the configured identity contract cannot be used safely."""


class _IdentityModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class _ServerIdentity(_IdentityModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class _ModelIdentity(_IdentityModel):
    id: str = Field(min_length=1)
    revision: str | None = Field(default=None, min_length=1)
    artifact_digest: str | None = Field(default=None, min_length=1)
    artifact_key: str | None = Field(default=None, min_length=1)
    quantization: str | None = Field(default=None, min_length=1)
    verification: Literal["verified", "available_unverified"]


class _RuntimeIdentity(_IdentityModel):
    name: str = Field(min_length=1)
    version: str | None = Field(default=None, min_length=1)
    implementation: str | None = Field(default=None, min_length=1)
    config_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    config: dict[str, object]
    fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    captured_at: float | None = Field(default=None, ge=0)
    evidence_grade: Literal["verified", "partial"]


class _HardwareIdentity(_IdentityModel):
    system: str = Field(min_length=1)
    machine: str = Field(min_length=1)
    processor: str | None = Field(default=None, min_length=1)
    logical_cpus: int | None = Field(default=None, gt=0)
    total_memory_bytes: int | None = Field(default=None, gt=0)
    accelerator: str | None = Field(default=None, min_length=1)
    extra: dict[str, str | int | float | bool] = Field(default_factory=dict)


class _RuntimeEntry(_IdentityModel):
    model: _ModelIdentity
    runtime: _RuntimeIdentity
    hardware: _HardwareIdentity


class _IdentityDocument(_IdentityModel):
    protocol_version: Literal["local-llm-identity-v1"]
    server: _ServerIdentity
    default_model: str | None = Field(default=None, min_length=1)
    models: dict[str, _RuntimeEntry]


class ResolvedLocalLLMServerIdentity(_IdentityModel):
    protocol_version: Literal["local-llm-identity-v1"]
    server_name: str
    server_version: str
    selected_runtime_key: str
    model: ModelIdentity
    runtime: RuntimeIdentity
    hardware: HardwareIdentity
    evidence_grade: Literal["verified", "partial"]


class LocalLLMServerIdentityClient:
    """Fetch and strictly validate a versioned, path-free identity document."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 2.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def resolve(self, *, model_id: str | None = None) -> ResolvedLocalLLMServerIdentity:
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(f"{self._base_url}/v1/runtime/identity")
                response.raise_for_status()
                raw: object = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LocalLLMServerIdentityError("local-llm-server identity request failed") from exc

        try:
            document = _IdentityDocument.model_validate(raw)
        except ValidationError as exc:
            raise LocalLLMServerIdentityError("invalid local-llm-identity-v1 response") from exc

        runtime_key, entry = _select_entry(document, model_id)
        return ResolvedLocalLLMServerIdentity(
            protocol_version=LOCAL_LLM_IDENTITY_PROTOCOL_VERSION,
            server_name=document.server.name,
            server_version=document.server.version,
            selected_runtime_key=runtime_key,
            model=ModelIdentity(
                model_id=entry.model.id,
                revision=entry.model.revision,
                artifact_digest=entry.model.artifact_digest,
                quantization=entry.model.quantization,
            ),
            runtime=RuntimeIdentity(
                name=entry.runtime.name,
                version=entry.runtime.version,
                config_digest=entry.runtime.config_digest,
            ),
            hardware=HardwareIdentity(
                device_class=entry.hardware.machine,
                cpu=entry.hardware.processor,
                accelerator=entry.hardware.accelerator,
                memory_bytes=entry.hardware.total_memory_bytes,
                os=entry.hardware.system,
            ),
            evidence_grade=entry.runtime.evidence_grade,
        )


def _select_entry(
    document: _IdentityDocument,
    model_id: str | None,
) -> tuple[str, _RuntimeEntry]:
    if model_id is not None:
        direct = document.models.get(model_id)
        if direct is not None:
            return model_id, direct
        matches = [
            (key, entry) for key, entry in document.models.items() if entry.model.id == model_id
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise LocalLLMServerIdentityError(
                f"model identity is ambiguous in local-llm-server: {model_id}"
            )
        raise LocalLLMServerIdentityError(
            f"model is missing from local-llm-server identity: {model_id}"
        )

    if document.default_model is not None:
        default = document.models.get(document.default_model)
        if default is not None:
            return document.default_model, default
    if len(document.models) == 1:
        return next(iter(document.models.items()))
    raise LocalLLMServerIdentityError("cannot select a runtime from local-llm-server identity")
