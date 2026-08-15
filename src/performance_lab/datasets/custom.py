"""Reusable explicit configuration for user-provided JSONL/CSV datasets."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .local import (
    DatasetLoadError,
    FieldMapping,
    LocalDatasetLoader,
    MaterializedDataset,
    SamplingSpec,
    materialize_local_dataset,
)

DATASET_IMPORT_CONFIG_VERSION: Literal[1] = 1


class CustomDatasetModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DatasetImportConfigError(ValueError):
    pass


class DatasetImportConfig(CustomDatasetModel):
    schema_version: Literal[1] = DATASET_IMPORT_CONFIG_VERSION
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    split: str = Field(default="test", min_length=1)
    mapping: FieldMapping
    sampling: SamplingSpec = Field(default_factory=SamplingSpec)
    source_label: str | None = None


class DatasetSourceInspection(CustomDatasetModel):
    format: Literal["jsonl", "csv"]
    row_count: int = Field(ge=0)
    fields: tuple[str, ...]
    preview: tuple[Mapping[str, object], ...]


def load_dataset_import_config(path: Path) -> DatasetImportConfig:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DatasetImportConfigError(f"cannot read dataset import config: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetImportConfigError("dataset import config is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise DatasetImportConfigError("dataset import config must be a JSON object")
    if raw.get("schema_version") != DATASET_IMPORT_CONFIG_VERSION:
        raise DatasetImportConfigError(
            f"unsupported dataset import schema_version={raw.get('schema_version')!r}; "
            f"expected {DATASET_IMPORT_CONFIG_VERSION}"
        )
    try:
        return DatasetImportConfig.model_validate(raw)
    except ValidationError as exc:
        raise DatasetImportConfigError(str(exc)) from exc


def inspect_dataset_source(
    source: Path,
    *,
    preview_limit: int = 3,
    loader: LocalDatasetLoader | None = None,
) -> DatasetSourceInspection:
    """Expose source shape for a mapping UI without guessing semantic fields."""

    if preview_limit < 0:
        raise ValueError("preview_limit must be non-negative")
    suffix = source.suffix.lower()
    if suffix not in {".jsonl", ".csv"}:
        raise DatasetLoadError(f"unsupported dataset format: {suffix or '<none>'}")
    active_loader = loader or LocalDatasetLoader()
    rows = tuple(active_loader.load(source))
    fields = tuple(sorted({str(key) for row in rows for key in row}))
    return DatasetSourceInspection(
        format="jsonl" if suffix == ".jsonl" else "csv",
        row_count=len(rows),
        fields=fields,
        preview=rows[:preview_limit],
    )


def materialize_dataset_import(
    source: Path,
    config: DatasetImportConfig,
    *,
    loader: LocalDatasetLoader | None = None,
) -> MaterializedDataset:
    return materialize_local_dataset(
        source,
        dataset_id=config.dataset_id,
        dataset_version=config.dataset_version,
        split=config.split,
        mapping=config.mapping,
        sampling=config.sampling,
        source_label=config.source_label,
        loader=loader,
    )
