"""Versioned workload-specific suites kept outside the generic execution engine."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import (
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    GenerationConfig,
    TaskSpec,
)
from performance_lab.evaluation import FieldExtractionEvaluator, JSONSchemaEvaluator
from performance_lab.plugins import Evaluator

from .local import DatasetRecord, MaterializedDataset

STRUCTURED_DOCUMENT_PACK_VERSION = "2026-08-15-v1"


class WorkloadPackModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class WorkloadPackDefinition(WorkloadPackModel):
    pack_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    task_family: str = Field(min_length=1)
    suite_id: str = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class WorkloadPackBundle:
    definition: WorkloadPackDefinition
    suite: EvaluationSuite
    datasets: Mapping[str, MaterializedDataset]
    evaluators: Mapping[str, Evaluator]


STRUCTURED_DOCUMENT_EXTRACTION = WorkloadPackDefinition(
    pack_id="structured-document-extraction",
    version=STRUCTURED_DOCUMENT_PACK_VERSION,
    title="Structured document extraction",
    description=(
        "Diagnostic workload for extracting a fixed invoice-like schema "
        "from short authored documents."
    ),
    task_family="structured_extraction",
    suite_id="workload-structured-document-extraction",
)


def available_workload_packs() -> tuple[WorkloadPackDefinition, ...]:
    return (STRUCTURED_DOCUMENT_EXTRACTION,)


def build_workload_pack(pack_id: str, *, version: str | None = None) -> WorkloadPackBundle:
    if pack_id != STRUCTURED_DOCUMENT_EXTRACTION.pack_id:
        raise KeyError(pack_id)
    if version is not None and version != STRUCTURED_DOCUMENT_EXTRACTION.version:
        raise KeyError(f"{pack_id}@{version}")
    return _build_structured_document_extraction()


def _build_structured_document_extraction() -> WorkloadPackBundle:
    schema = {
        "type": "object",
        "required": ["document_id", "vendor", "total", "currency", "due_date"],
        "properties": {
            "document_id": {"type": "string"},
            "vendor": {"type": "string"},
            "total": {"type": "number"},
            "currency": {"type": "string", "enum": ["EUR", "USD", "GBP"]},
            "due_date": {"type": "string"},
        },
        "additionalProperties": False,
    }
    schema_evaluator = JSONSchemaEvaluator(schema)
    field_evaluator = FieldExtractionEvaluator()
    records = (
        _record(
            "doc-1",
            "Invoice INV-104 from Northwind Labs. Total EUR 1280.50. Due 2026-09-15.",
            {
                "document_id": "INV-104",
                "vendor": "Northwind Labs",
                "total": 1280.50,
                "currency": "EUR",
                "due_date": "2026-09-15",
            },
        ),
        _record(
            "doc-2",
            "Bill B-778 | Vendor: Cedar Systems | Amount: USD 420 | Due: 2026-10-01",
            {
                "document_id": "B-778",
                "vendor": "Cedar Systems",
                "total": 420,
                "currency": "USD",
                "due_date": "2026-10-01",
            },
        ),
        _record(
            "doc-3",
            "Reference AC-55. Supplier Alpine Coffee. GBP 73.25 payable by 2026-08-31.",
            {
                "document_id": "AC-55",
                "vendor": "Alpine Coffee",
                "total": 73.25,
                "currency": "GBP",
                "due_date": "2026-08-31",
            },
        ),
        _record(
            "doc-4",
            "Document ZX9 from Blue River SRL; due 2026-11-20; grand total EUR 999.99.",
            {
                "document_id": "ZX9",
                "vendor": "Blue River SRL",
                "total": 999.99,
                "currency": "EUR",
                "due_date": "2026-11-20",
            },
        ),
        _record(
            "doc-5",
            "Vendor Green Pine Ltd issued GP-2026-7. Total USD 150.00, due 2026-09-05.",
            {
                "document_id": "GP-2026-7",
                "vendor": "Green Pine Ltd",
                "total": 150.0,
                "currency": "USD",
                "due_date": "2026-09-05",
            },
        ),
        _record(
            "doc-6",
            "Receipt R88, Oak & Stone, amount GBP 2400, payment deadline 2026-12-12.",
            {
                "document_id": "R88",
                "vendor": "Oak & Stone",
                "total": 2400,
                "currency": "GBP",
                "due_date": "2026-12-12",
            },
        ),
    )
    dataset_id = "workload-structured-document-extraction"
    dataset = _dataset(dataset_id, records)
    evaluators: dict[str, Evaluator] = {
        schema_evaluator.evaluator_id: schema_evaluator,
        field_evaluator.evaluator_id: field_evaluator,
    }
    tasks = (
        _task(
            "schema_adherence",
            dataset_id,
            schema_evaluator,
            "json_schema_valid",
        ),
        _task(
            "field_correctness",
            dataset_id,
            field_evaluator,
            "field_accuracy",
        ),
    )
    suite = EvaluationSuite(
        suite_id=STRUCTURED_DOCUMENT_EXTRACTION.suite_id,
        suite_version=STRUCTURED_DOCUMENT_EXTRACTION.version,
        tasks=tasks,
        generation=GenerationConfig(
            max_output_tokens=160,
            temperature=0.0,
            seed=7,
            response_format="json_object",
        ),
    )
    return WorkloadPackBundle(
        definition=STRUCTURED_DOCUMENT_EXTRACTION,
        suite=suite,
        datasets=MappingProxyType({dataset_id: dataset}),
        evaluators=MappingProxyType(evaluators),
    )


def _record(sample_id: str, document: str, expected: dict[str, object]) -> DatasetRecord:
    prompt = (
        "Extract the document into JSON with exactly these keys: document_id, vendor, total, "
        f"currency, due_date. Document: {document}"
    )
    return DatasetRecord(sample_id=sample_id, input=prompt, expected=expected)


def _dataset(dataset_id: str, records: tuple[DatasetRecord, ...]) -> MaterializedDataset:
    digest = sha256(
        json.dumps(
            [record.model_dump(mode="json") for record in records],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    snapshot = DatasetSnapshot(
        dataset_id=dataset_id,
        dataset_version=STRUCTURED_DOCUMENT_PACK_VERSION,
        source="builtin:performance-lab-authored",
        split="test",
        content_sha256=digest,
        selection_policy="all-authored-v1",
        sample_count=len(records),
    )
    return MaterializedDataset(snapshot=snapshot, records=records)


def _task(task_id: str, dataset_id: str, evaluator: Evaluator, metric: str) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        dataset_snapshot_id=dataset_id,
        evaluator=EvaluatorRef(evaluator_id=evaluator.evaluator_id, version=evaluator.version),
        metric_names=(metric,),
    )
