from performance_lab.evaluation import (
    JSONSchemaEvaluator,
    NumericToleranceEvaluator,
    describe_evaluator,
)


class UnknownEvaluator:
    evaluator_id = "plugin-owned"
    version = "3"

    def evaluate(self, *, actual: object, expected: object):
        del actual, expected
        return ()


def test_numeric_descriptor_exposes_owned_tolerance_without_global_weight() -> None:
    descriptor = describe_evaluator(
        NumericToleranceEvaluator(absolute_tolerance=0.25, relative_tolerance=0.01)
    )

    assert descriptor.evaluator_type == "deterministic"
    assert descriptor.deterministic is True
    assert descriptor.explanation_supported is False
    assert descriptor.configuration == {
        "absolute_tolerance": 0.25,
        "relative_tolerance": 0.01,
    }
    assert descriptor.rule_summary is not None
    assert "tolerance" in descriptor.rule_summary.lower()
    assert "weight" not in descriptor.configuration


def test_json_schema_descriptor_retains_exact_schema_configuration() -> None:
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string"}},
        "additionalProperties": False,
    }

    descriptor = describe_evaluator(JSONSchemaEvaluator(schema))

    assert descriptor.configuration == {"schema": schema}
    assert descriptor.rule_summary is not None
    assert "draft 2020-12" in descriptor.rule_summary.lower()


def test_unknown_plugin_descriptor_does_not_guess_semantics() -> None:
    descriptor = describe_evaluator(UnknownEvaluator())

    assert descriptor.evaluator_id == "plugin-owned"
    assert descriptor.version == "3"
    assert descriptor.evaluator_type == "custom"
    assert descriptor.deterministic is None
    assert descriptor.explanation_supported is None
    assert descriptor.rule_summary is None
    assert descriptor.configuration == {}
