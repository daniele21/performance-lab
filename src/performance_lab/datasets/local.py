"""Local dataset loading, explicit field mapping and deterministic materialization."""

from __future__ import annotations

import csv
import json
import random
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import DatasetSnapshot


class DatasetModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DatasetLoadError(ValueError):
    pass


class FieldMapping(DatasetModel):
    id_field: str = Field(min_length=1)
    input_field: str = Field(min_length=1)
    expected_field: str = Field(min_length=1)
    split_field: str | None = None


class SamplingSpec(DatasetModel):
    seed: int = 0
    sample_limit: int | None = Field(default=None, gt=0)


class DatasetRecord(DatasetModel):
    sample_id: str = Field(min_length=1)
    input: object
    expected: object
    metadata: Mapping[str, object] = Field(default_factory=dict)


class MaterializedDataset(DatasetModel):
    snapshot: DatasetSnapshot
    records: tuple[DatasetRecord, ...]


class LocalDatasetLoader:
    """Read JSONL/CSV without guessing semantic columns."""

    loader_id = "local-jsonl-csv"

    def load(self, source: Path, *, split: str | None = None) -> Sequence[Mapping[str, object]]:
        del split
        suffix = source.suffix.lower()
        if suffix == ".jsonl":
            return self._load_jsonl(source)
        if suffix == ".csv":
            return self._load_csv(source)
        raise DatasetLoadError(f"unsupported dataset format: {suffix or '<none>'}")

    @staticmethod
    def _load_jsonl(source: Path) -> tuple[Mapping[str, object], ...]:
        rows: list[Mapping[str, object]] = []
        try:
            lines = source.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise DatasetLoadError(f"cannot read dataset: {source}") from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                raw: object = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetLoadError(f"invalid JSONL at line {line_number}") from exc
            if not isinstance(raw, dict):
                raise DatasetLoadError(f"JSONL line {line_number} is not an object")
            rows.append(cast(dict[str, object], raw))
        return tuple(rows)

    @staticmethod
    def _load_csv(source: Path) -> tuple[Mapping[str, object], ...]:
        try:
            with source.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    raise DatasetLoadError("CSV has no header")
                return tuple(dict(row) for row in reader)
        except OSError as exc:
            raise DatasetLoadError(f"cannot read dataset: {source}") from exc


def materialize_local_dataset(
    source: Path,
    *,
    dataset_id: str,
    dataset_version: str,
    split: str,
    mapping: FieldMapping,
    sampling: SamplingSpec | None = None,
    source_label: str | None = None,
    loader: LocalDatasetLoader | None = None,
) -> MaterializedDataset:
    """Freeze the exact selected records and their provenance into a snapshot."""

    active_sampling = sampling or SamplingSpec()
    active_loader = loader or LocalDatasetLoader()
    raw_rows = active_loader.load(source)
    records: list[DatasetRecord] = []
    for index, row in enumerate(raw_rows, start=1):
        if mapping.split_field is not None:
            row_split = row.get(mapping.split_field)
            if row_split is None:
                raise DatasetLoadError(
                    f"row {index} is missing configured split field {mapping.split_field!r}"
                )
            if str(row_split) != split:
                continue
        records.append(_map_record(row, index=index, mapping=mapping))

    if not records:
        raise DatasetLoadError(f"no records available for split {split!r}")

    selected = records
    if active_sampling.sample_limit is not None and active_sampling.sample_limit < len(records):
        randomizer = random.Random(active_sampling.seed)
        selected = randomizer.sample(records, active_sampling.sample_limit)

    frozen_records = tuple(selected)
    digest = _records_digest(frozen_records)
    policy = (
        f"seeded-sample-v1:seed={active_sampling.seed}:limit="
        f"{active_sampling.sample_limit if active_sampling.sample_limit is not None else 'all'}"
    )
    snapshot = DatasetSnapshot(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        source=source_label or f"local:{source.name}",
        split=split,
        content_sha256=digest,
        selection_policy=policy,
        sample_count=len(frozen_records),
    )
    return MaterializedDataset(snapshot=snapshot, records=frozen_records)


def _map_record(row: Mapping[str, object], *, index: int, mapping: FieldMapping) -> DatasetRecord:
    required = (mapping.id_field, mapping.input_field, mapping.expected_field)
    missing = [field for field in required if field not in row]
    if missing:
        raise DatasetLoadError(f"row {index} is missing configured fields: {', '.join(missing)}")
    sample_id = str(row[mapping.id_field])
    metadata = {key: value for key, value in row.items() if key not in required}
    return DatasetRecord(
        sample_id=sample_id,
        input=row[mapping.input_field],
        expected=row[mapping.expected_field],
        metadata=metadata,
    )


def _records_digest(records: tuple[DatasetRecord, ...]) -> str:
    serialized = json.dumps(
        [record.model_dump(mode="json") for record in records],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(serialized.encode("utf-8")).hexdigest()
