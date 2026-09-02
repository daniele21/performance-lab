import asyncio

import pytest

from performance_lab.evaluation import (
    JudgeConfig,
    JudgeEvaluationError,
    LLMRubricJudge,
)
from performance_lab.plugins import FakeInferenceAdapter


def test_judge_records_model_rubric_prompt_and_generation_provenance() -> None:
    adapter = FakeInferenceAdapter(response_text='{"score":0.75,"rationale":"mostly correct"}')
    judge = LLMRubricJudge(
        adapter,
        JudgeConfig(
            judge_id="quality-judge",
            model_id="judge-model",
            rubric_id="helpfulness",
            rubric_version="2",
        ),
    )

    result = asyncio.run(
        judge.evaluate(
            sample_id="sample-1",
            actual="candidate answer",
            expected="reference answer",
            rubric="Score semantic correctness and instruction adherence.",
        )
    )

    assert result.score.value == 0.75
    assert result.score.evaluator.evaluator_id == "llm-judge:quality-judge:helpfulness"
    assert result.score.evaluator.version == "2"
    assert result.provenance.adapter_id == adapter.adapter_id
    assert result.provenance.model_id == "judge-model"
    assert result.provenance.rubric_id == "helpfulness"
    assert result.provenance.rubric_version == "2"
    assert result.provenance.prompt_template_version == "judge-json-v1"
    assert result.provenance.generation.temperature == 0.0
    assert result.provenance.generation.response_format == "json_object"
    assert result.rationale is None
    assert adapter.requests[0].model == "judge-model"
    assert adapter.requests[0].generation == result.provenance.generation


def test_judge_rationale_is_retained_only_when_opted_in() -> None:
    adapter = FakeInferenceAdapter(response_text='{"score":1.0,"rationale":"fully correct"}')
    judge = LLMRubricJudge(
        adapter,
        JudgeConfig(
            judge_id="quality-judge",
            model_id="judge-model",
            rubric_id="correctness",
            rubric_version="1",
            retain_rationale=True,
        ),
    )

    result = asyncio.run(
        judge.evaluate(
            sample_id="sample-2",
            actual="yes",
            expected="yes",
            rubric="Return 1 for a fully correct answer and 0 otherwise.",
        )
    )

    assert result.rationale == "fully correct"


def test_invalid_judge_response_is_distinct_from_model_task_failure() -> None:
    judge = LLMRubricJudge(
        FakeInferenceAdapter(response_text="not-json"),
        JudgeConfig(
            judge_id="quality-judge",
            model_id="judge-model",
            rubric_id="correctness",
            rubric_version="1",
        ),
    )

    with pytest.raises(JudgeEvaluationError, match="valid JSON"):
        asyncio.run(
            judge.evaluate(
                sample_id="sample-3",
                actual="answer",
                expected="reference",
                rubric="Score correctness.",
            )
        )
