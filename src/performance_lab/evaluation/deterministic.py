"""Versioned deterministic evaluator primitives."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import math
import re
import unicodedata

from jsonschema import SchemaError, ValidationError as JSONSchemaValidationError, validate

from performance_lab.domain import EvaluatorRef, Score

_NORMALIZATION_VERSION = "text-normalization-v1"


class EvaluationError(ValueError):
    """Evaluator configuration/input failure, distinct from model execution failure."""


class DeterministicEvaluator:
    evaluator_id: str
    version = "1"

    @property
    def evaluator_ref(self) -> EvaluatorRef:
        return EvaluatorRef(evaluator_id=self.evaluator_id, version=self.version)

    def _score(
        self,
        metric: str,
        value: float,
        *,
        higher_is_better: bool = True,
        numerator: float | None = None,
        denominator: float | None = None,
    ) -> tuple[Score, ...]:
        return (
            Score(
                metric=metric,
                value=value,
                evaluator=self.evaluator_ref,
                higher_is_better=higher_is_better,
                numerator=numerator,
                denominator=denominator,
            ),
        )


def normalize_text(value: object) -> str:
    if not isinstance(value, str):
        raise EvaluationError("text evaluator requires string values")
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return " ".join(normalized.split())


class ExactMatchEvaluator(DeterministicEvaluator):
    evaluator_id = "exact-match"

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        value = 1.0 if actual == expected else 0.0
        return self._score("exact_match", value, numerator=value, denominator=1.0)


class NormalizedExactMatchEvaluator(DeterministicEvaluator):
    evaluator_id = f"normalized-exact-match:{_NORMALIZATION_VERSION}"

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        value = 1.0 if normalize_text(actual) == normalize_text(expected) else 0.0
        return self._score("normalized_exact_match", value, numerator=value, denominator=1.0)


class NumericToleranceEvaluator(DeterministicEvaluator):
    evaluator_id = "numeric-tolerance"

    def __init__(self, *, absolute_tolerance: float = 0.0, relative_tolerance: float = 0.0) -> None:
        if absolute_tolerance < 0 or relative_tolerance < 0:
            raise EvaluationError("numeric tolerances must be non-negative")
        self.absolute_tolerance = absolute_tolerance
        self.relative_tolerance = relative_tolerance

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        try:
            actual_number = float(actual)  # type: ignore[arg-type]
            expected_number = float(expected)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise EvaluationError("numeric evaluator requires numeric-coercible values") from exc
        matched = math.isclose(
            actual_number,
            expected_number,
            rel_tol=self.relative_tolerance,
            abs_tol=self.absolute_tolerance,
        )
        value = float(matched)
        return self._score("numeric_match", value, numerator=value, denominator=1.0)


class ClassificationAccuracyEvaluator(NormalizedExactMatchEvaluator):
    evaluator_id = f"classification-accuracy:{_NORMALIZATION_VERSION}"

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        value = 1.0 if normalize_text(actual) == normalize_text(expected) else 0.0
        return self._score("accuracy", value, numerator=value, denominator=1.0)


class SetPRFEvaluator(DeterministicEvaluator):
    evaluator_id = f"set-prf:{_NORMALIZATION_VERSION}"

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        actual_set = _normalized_set(actual)
        expected_set = _normalized_set(expected)
        true_positive = len(actual_set & expected_set)
        precision_denominator = len(actual_set)
        recall_denominator = len(expected_set)
        precision = true_positive / precision_denominator if precision_denominator else float(not expected_set)
        recall = true_positive / recall_denominator if recall_denominator else float(not actual_set)
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        return (
            Score(
                metric="precision",
                value=precision,
                evaluator=self.evaluator_ref,
                higher_is_better=True,
                numerator=float(true_positive),
                denominator=float(precision_denominator or 1),
            ),
            Score(
                metric="recall",
                value=recall,
                evaluator=self.evaluator_ref,
                higher_is_better=True,
                numerator=float(true_positive),
                denominator=float(recall_denominator or 1),
            ),
            Score(
                metric="f1",
                value=f1,
                evaluator=self.evaluator_ref,
                higher_is_better=True,
            ),
        )


class RegexValidityEvaluator(DeterministicEvaluator):
    evaluator_id = "regex-validity"

    def __init__(self, pattern: str) -> None:
        try:
            self.pattern = re.compile(pattern)
        except re.error as exc:
            raise EvaluationError(f"invalid evaluator regex: {exc}") from exc

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        del expected
        if not isinstance(actual, str):
            raise EvaluationError("regex evaluator requires string actual value")
        value = float(self.pattern.fullmatch(actual) is not None)
        return self._score("pattern_valid", value, numerator=value, denominator=1.0)


class JSONParseEvaluator(DeterministicEvaluator):
    evaluator_id = "json-parse"

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        del expected
        value = 1.0
        try:
            _json_value(actual)
        except EvaluationError:
            value = 0.0
        return self._score("json_valid", value, numerator=value, denominator=1.0)


class JSONSchemaEvaluator(DeterministicEvaluator):
    evaluator_id = "json-schema"

    def __init__(self, schema: Mapping[str, object]) -> None:
        self.schema = dict(schema)
        try:
            validate(instance=None, schema=self.schema)
        except SchemaError as exc:
            raise EvaluationError(f"invalid JSON Schema: {exc.message}") from exc
        except JSONSchemaValidationError:
            pass

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        del expected
        try:
            instance = _json_value(actual)
            validate(instance=instance, schema=self.schema)
            value = 1.0
        except (EvaluationError, JSONSchemaValidationError):
            value = 0.0
        return self._score("json_schema_valid", value, numerator=value, denominator=1.0)


class FieldExtractionEvaluator(DeterministicEvaluator):
    evaluator_id = f"field-extraction:{_NORMALIZATION_VERSION}"

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        actual_mapping = _mapping_value(actual, "actual")
        expected_mapping = _mapping_value(expected, "expected")
        if not expected_mapping:
            raise EvaluationError("field extraction expected mapping cannot be empty")
        matched = 0
        for key, expected_value in expected_mapping.items():
            if key not in actual_mapping:
                continue
            if _normalized_value(actual_mapping[key]) == _normalized_value(expected_value):
                matched += 1
        denominator = len(expected_mapping)
        value = matched / denominator
        return self._score(
            "field_accuracy",
            value,
            numerator=float(matched),
            denominator=float(denominator),
        )


def aggregate_scores(scores: Sequence[Score]) -> Score:
    if not scores:
        raise EvaluationError("cannot aggregate an empty score sequence")
    first = scores[0]
    if any(
        score.metric != first.metric
        or score.evaluator != first.evaluator
        or score.higher_is_better != first.higher_is_better
        for score in scores[1:]
    ):
        raise EvaluationError("scores must share metric, evaluator and direction")
    if all(score.numerator is not None and score.denominator is not None for score in scores):
        numerator = sum(score.numerator or 0.0 for score in scores)
        denominator = sum(score.denominator or 0.0 for score in scores)
        if denominator <= 0:
            raise EvaluationError("aggregate denominator must be positive")
        return Score(
            metric=first.metric,
            value=numerator / denominator,
            evaluator=first.evaluator,
            higher_is_better=first.higher_is_better,
            numerator=numerator,
            denominator=denominator,
        )
    return Score(
        metric=first.metric,
        value=sum(score.value for score in scores) / len(scores),
        evaluator=first.evaluator,
        higher_is_better=first.higher_is_better,
    )


def _normalized_set(value: object) -> set[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise EvaluationError("set PRF evaluator requires a non-string sequence")
    return {normalize_text(item) for item in value}


def _json_value(value: object) -> object:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise EvaluationError("value is not valid JSON") from exc
    return value


def _mapping_value(value: object, label: str) -> Mapping[str, object]:
    parsed = _json_value(value)
    if not isinstance(parsed, dict):
        raise EvaluationError(f"{label} must be a JSON object/mapping")
    return parsed


def _normalized_value(value: object) -> object:
    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, list):
        return tuple(_normalized_value(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((str(key), _normalized_value(item)) for key, item in value.items()))
    return value
