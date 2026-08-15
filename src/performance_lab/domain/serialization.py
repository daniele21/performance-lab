"""Version-aware serialization helpers."""

from __future__ import annotations

import json
from typing import Any, TypeVar, cast

from pydantic import ValidationError

from .schemas import SCHEMA_VERSION, VersionedModel

T = TypeVar("T", bound=VersionedModel)


class SchemaLoadError(ValueError):
    """Base class for persisted-schema loading failures."""


class UnsupportedSchemaVersion(SchemaLoadError):
    def __init__(self, found: object) -> None:
        super().__init__(
            f"unsupported schema_version={found!r}; expected {SCHEMA_VERSION}"
        )
        self.found = found


class InvalidSerializedModel(SchemaLoadError):
    pass


def _check_version(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise UnsupportedSchemaVersion(payload.get("schema_version"))


def load_dict(model_type: type[T], payload: dict[str, Any]) -> T:
    """Load one current-version model without guessing migrations."""
    _check_version(payload)
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        raise InvalidSerializedModel(str(exc)) from exc


def load_json(model_type: type[T], payload: str | bytes) -> T:
    try:
        raw = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as exc:
        raise InvalidSerializedModel("payload is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise InvalidSerializedModel("top-level JSON payload must be an object")
    return load_dict(model_type, cast(dict[str, Any], raw))
