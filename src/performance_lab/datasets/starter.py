"""Compact authored-in-repository diagnostic starter suite."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from performance_lab.domain import (
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    GenerationConfig,
    TaskSpec,
)
from performance_lab.evaluation import (
    ClassificationAccuracyEvaluator,
    FieldExtractionEvaluator,
    JSONSchemaEvaluator,
    NormalizedExactMatchEvaluator,
    NumericToleranceEvaluator,
)
from performance_lab.plugins import Evaluator

from .local import DatasetRecord, MaterializedDataset

STARTER_SUITE_VERSION = "2026-08-15-v1"


@dataclass(frozen=True, slots=True)
class StarterSuiteBundle:
    suite: EvaluationSuite
    datasets: Mapping[str, MaterializedDataset]
    evaluators: Mapping[str, Evaluator]


def build_general_starter_suite() -> StarterSuiteBundle:
    """Return a small deterministic suite intended for device diagnostics, not ranking."""

    normalized = NormalizedExactMatchEvaluator()
    numeric = NumericToleranceEvaluator(absolute_tolerance=1e-9)
    classification = ClassificationAccuracyEvaluator()
    structured_schema = JSONSchemaEvaluator(
        {
            "type": "object",
            "required": ["name", "count"],
            "properties": {"name": {"type": "string"}, "count": {"type": "integer"}},
            "additionalProperties": False,
        }
    )
    extraction = FieldExtractionEvaluator()

    datasets = {
        "starter-instruction": _dataset(
            "starter-instruction",
            (
                _record("if-1", "Reply with exactly: BLUE", "BLUE"),
                _record("if-2", "Reply with exactly: seven", "seven"),
                _record("if-3", "Reply with exactly: LOCAL", "LOCAL"),
            ),
        ),
        "starter-factual": _dataset(
            "starter-factual",
            (
                _record(
                    "fq-1", "What is the capital of France? Answer with the city only.", "Paris"
                ),
                _record(
                    "fq-2", "What is the chemical formula of water? Answer only the formula.", "H2O"
                ),
                _record(
                    "fq-3", "Which planet is the largest in the Solar System? Name only.", "Jupiter"
                ),
            ),
        ),
        "starter-reasoning": _dataset(
            "starter-reasoning",
            (
                _record(
                    "rs-1",
                    "All lorps are mivs. Every miv is a zan. Is every lorp a zan? Answer yes or no.",
                    "yes",
                ),
                _record(
                    "rs-2",
                    "No red object is blue. This object is red. Can it also be blue? Answer yes or no.",
                    "no",
                ),
                _record(
                    "rs-3",
                    "Ana is older than Bea. Bea is older than Cy. Is Ana older than Cy? Answer yes or no.",
                    "yes",
                ),
            ),
        ),
        "starter-math": _dataset(
            "starter-math",
            (
                _record("ma-1", "Compute 8 + 9. Answer only the number.", 17),
                _record("ma-2", "Compute 6 * 7. Answer only the number.", 42),
                _record("ma-3", "Compute 1 / 4 as a decimal. Answer only the number.", 0.25),
                _record("ma-4", "A dozen contains how many items? Answer only the number.", 12),
            ),
        ),
        "starter-classification": _dataset(
            "starter-classification",
            (
                _record(
                    "cl-1",
                    "Classify sentiment as positive or negative: 'The update works perfectly.'",
                    "positive",
                ),
                _record(
                    "cl-2",
                    "Classify sentiment as positive or negative: 'The app crashes every time.'",
                    "negative",
                ),
                _record(
                    "cl-3", "Classify intent as question or command: 'Close the window.'", "command"
                ),
                _record(
                    "cl-4",
                    "Classify intent as question or command: 'Where is the station?'",
                    "question",
                ),
            ),
        ),
        "starter-structured": _dataset(
            "starter-structured",
            (
                _record(
                    "js-1",
                    'Return JSON only with name and count: name is "Ada", count is 2.',
                    {"name": "Ada", "count": 2},
                ),
                _record(
                    "js-2",
                    'Return JSON only with name and count: name is "Lin", count is 5.',
                    {"name": "Lin", "count": 5},
                ),
                _record(
                    "js-3",
                    'Return JSON only with name and count: name is "Kai", count is 1.',
                    {"name": "Kai", "count": 1},
                ),
            ),
        ),
    }

    evaluators: dict[str, Evaluator] = {
        normalized.evaluator_id: normalized,
        numeric.evaluator_id: numeric,
        classification.evaluator_id: classification,
        structured_schema.evaluator_id: structured_schema,
        extraction.evaluator_id: extraction,
    }
    tasks = (
        _task("instruction_following", "starter-instruction", normalized, "normalized_exact_match"),
        _task("factual_qa", "starter-factual", normalized, "normalized_exact_match"),
        _task("reasoning", "starter-reasoning", normalized, "normalized_exact_match"),
        _task("basic_math", "starter-math", numeric, "numeric_match"),
        _task("classification", "starter-classification", classification, "accuracy"),
        _task(
            "structured_json_adherence",
            "starter-structured",
            structured_schema,
            "json_schema_valid",
        ),
        _task("structured_json_fields", "starter-structured", extraction, "field_accuracy"),
    )
    suite = EvaluationSuite(
        suite_id="general-diagnostic-starter",
        suite_version=STARTER_SUITE_VERSION,
        tasks=tasks,
        generation=GenerationConfig(max_output_tokens=64, temperature=0.0, seed=7),
    )
    return StarterSuiteBundle(
        suite=suite,
        datasets=MappingProxyType(datasets),
        evaluators=MappingProxyType(evaluators),
    )


def _record(sample_id: str, prompt: str, expected: object) -> DatasetRecord:
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
        dataset_version=STARTER_SUITE_VERSION,
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
