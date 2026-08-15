import pytest

from performance_lab.evaluation import (
    ClassificationAccuracyEvaluator,
    EvaluationError,
    ExactMatchEvaluator,
    FieldExtractionEvaluator,
    JSONParseEvaluator,
    JSONSchemaEvaluator,
    NormalizedExactMatchEvaluator,
    NumericToleranceEvaluator,
    RegexValidityEvaluator,
    SetPRFEvaluator,
    aggregate_scores,
)


def test_exact_and_normalized_exact_match_are_distinct() -> None:
    assert ExactMatchEvaluator().evaluate(actual=" Hello ", expected="hello")[0].value == 0.0
    score = NormalizedExactMatchEvaluator().evaluate(actual=" Hello   WORLD ", expected="hello world")[0]
    assert score.value == 1.0
    assert "text-normalization-v1" in score.evaluator.evaluator_id


def test_numeric_tolerance() -> None:
    evaluator = NumericToleranceEvaluator(absolute_tolerance=0.05)
    assert evaluator.evaluate(actual="10.02", expected=10.0)[0].value == 1.0
    assert evaluator.evaluate(actual=10.2, expected=10.0)[0].value == 0.0


def test_classification_and_set_prf() -> None:
    assert ClassificationAccuracyEvaluator().evaluate(actual="YES", expected=" yes ")[0].value == 1.0
    scores = SetPRFEvaluator().evaluate(actual=["a", "b"], expected=["b", "c"])
    by_metric = {score.metric: score.value for score in scores}
    assert by_metric == {"precision": 0.5, "recall": 0.5, "f1": 0.5}


def test_regex_json_parse_and_schema_validity() -> None:
    assert RegexValidityEvaluator(r"[A-Z]{3}-\d{2}").evaluate(actual="ABC-12", expected=None)[0].value == 1.0
    assert JSONParseEvaluator().evaluate(actual='{"x": 1}', expected=None)[0].value == 1.0
    assert JSONParseEvaluator().evaluate(actual="not json", expected=None)[0].value == 0.0

    evaluator = JSONSchemaEvaluator(
        {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }
    )
    assert evaluator.evaluate(actual='{"name": "Ada"}', expected=None)[0].value == 1.0
    assert evaluator.evaluate(actual='{"name": 12}', expected=None)[0].value == 0.0


def test_field_level_extraction_and_aggregation() -> None:
    evaluator = FieldExtractionEvaluator()
    first = evaluator.evaluate(
        actual='{"name":" Ada ","city":"Milan"}',
        expected={"name": "ada", "city": "Rome"},
    )[0]
    second = evaluator.evaluate(
        actual={"name": "Ada", "city": "Rome"},
        expected={"name": "ada", "city": "Rome"},
    )[0]
    aggregate = aggregate_scores([first, second])
    assert first.value == 0.5
    assert second.value == 1.0
    assert aggregate.value == 0.75
    assert aggregate.numerator == 3.0
    assert aggregate.denominator == 4.0


def test_evaluator_failures_are_typed() -> None:
    with pytest.raises(EvaluationError):
        NumericToleranceEvaluator().evaluate(actual="abc", expected=1)
    with pytest.raises(EvaluationError):
        FieldExtractionEvaluator().evaluate(actual="[]", expected={"x": 1})
    with pytest.raises(EvaluationError):
        aggregate_scores([])
