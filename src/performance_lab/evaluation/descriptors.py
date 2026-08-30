"""Evaluator-owned metadata used by inspection/read-model surfaces.

Descriptions live next to evaluator implementations so browser/API projections do not have to
reverse-engineer scoring semantics or invent explanations.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from performance_lab.plugins import Evaluator

from .deterministic import (
    ClassificationAccuracyEvaluator,
    ExactMatchEvaluator,
    FieldExtractionEvaluator,
    JSONParseEvaluator,
    JSONSchemaEvaluator,
    NormalizedExactMatchEvaluator,
    NumericToleranceEvaluator,
    RegexValidityEvaluator,
    SetPRFEvaluator,
)


@dataclass(frozen=True, slots=True)
class EvaluatorDescriptor:
    evaluator_id: str
    version: str
    evaluator_type: str
    deterministic: bool | None
    explanation_supported: bool | None
    rule_summary: str | None
    configuration: Mapping[str, object]


def describe_evaluator(evaluator: Evaluator) -> EvaluatorDescriptor:
    """Return truthful scoring metadata for a registered evaluator implementation.

    Unknown plugin evaluators retain their identity without guessing determinism, explanation
    support or scoring rules.
    """

    configuration: dict[str, object] = {}
    evaluator_type = "custom"
    deterministic: bool | None = None
    explanation_supported: bool | None = None
    rule_summary: str | None = None

    if isinstance(evaluator, ClassificationAccuracyEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = (
            "Case-folds, trims and whitespace-normalizes actual and expected labels, then scores "
            "1 for equality and 0 otherwise."
        )
    elif isinstance(evaluator, NormalizedExactMatchEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = (
            "Applies NFKC normalization, case-folding, trimming and whitespace normalization to "
            "actual and expected text, then scores 1 for equality and 0 otherwise."
        )
    elif isinstance(evaluator, ExactMatchEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = "Scores 1 when actual and expected values are exactly equal, else 0."
    elif isinstance(evaluator, NumericToleranceEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = (
            "Coerces actual and expected values to numbers and scores 1 when they are within the "
            "configured absolute/relative tolerance, else 0."
        )
        configuration = {
            "absolute_tolerance": evaluator.absolute_tolerance,
            "relative_tolerance": evaluator.relative_tolerance,
        }
    elif isinstance(evaluator, SetPRFEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = (
            "Normalizes sequence items as text sets and computes precision, recall and F1 from "
            "set overlap."
        )
    elif isinstance(evaluator, RegexValidityEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = "Scores 1 when the full actual string matches the configured regular expression."
        configuration = {"pattern": evaluator.pattern.pattern}
    elif isinstance(evaluator, JSONParseEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = "Scores 1 when the actual value can be interpreted as valid JSON, else 0."
    elif isinstance(evaluator, JSONSchemaEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = (
            "Parses the actual value as JSON when needed and validates it against the configured "
            "Draft 2020-12 JSON Schema."
        )
        configuration = {"schema": dict(evaluator.schema)}
    elif isinstance(evaluator, FieldExtractionEvaluator):
        evaluator_type = "deterministic"
        deterministic = True
        explanation_supported = False
        rule_summary = (
            "Parses actual and expected values as mappings and scores the fraction of expected "
            "fields whose normalized values match."
        )

    return EvaluatorDescriptor(
        evaluator_id=evaluator.evaluator_id,
        version=evaluator.version,
        evaluator_type=evaluator_type,
        deterministic=deterministic,
        explanation_supported=explanation_supported,
        rule_summary=rule_summary,
        configuration=MappingProxyType(configuration),
    )
