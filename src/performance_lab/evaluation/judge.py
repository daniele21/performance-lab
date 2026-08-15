"""Opt-in rubric evaluation through an explicitly identified judge endpoint."""

from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from performance_lab.domain import EvaluatorRef, GenerationConfig, Score
from performance_lab.plugins import (
    ChatMessage,
    InferenceAdapter,
    InferenceRequest,
    MessageRole,
)


class JudgeModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class JudgeEvaluationError(ValueError):
    pass


class JudgeConfig(JudgeModel):
    judge_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    rubric_id: str = Field(min_length=1)
    rubric_version: str = Field(min_length=1)
    prompt_template_version: str = Field(default="judge-json-v1", min_length=1)
    generation: GenerationConfig = GenerationConfig(
        max_output_tokens=256,
        temperature=0.0,
        response_format="json_object",
    )
    retain_rationale: bool = False


class JudgeProvenance(JudgeModel):
    judge_id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    rubric_id: str = Field(min_length=1)
    rubric_version: str = Field(min_length=1)
    prompt_template_version: str = Field(min_length=1)
    generation: GenerationConfig


class JudgeResponse(JudgeModel):
    score: float = Field(ge=0.0, le=1.0)
    rationale: str | None = None


class JudgeEvaluationResult(JudgeModel):
    score: Score
    provenance: JudgeProvenance
    rationale: str | None = None


class LLMRubricJudge:
    """Optional judge service; deterministic evaluators remain the default execution path."""

    def __init__(self, adapter: InferenceAdapter, config: JudgeConfig) -> None:
        self.adapter = adapter
        self.config = config

    async def evaluate(
        self,
        *,
        sample_id: str,
        actual: object,
        expected: object,
        rubric: str,
    ) -> JudgeEvaluationResult:
        if not rubric.strip():
            raise JudgeEvaluationError("rubric text must be non-empty")
        request = InferenceRequest(
            request_id=f"judge:{self.config.judge_id}:{sample_id}",
            model=self.config.model_id,
            generation=self.config.generation,
            messages=(
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        "You are an evaluation judge. Apply the supplied rubric only. "
                        "Return JSON with score in [0,1] and optional rationale."
                    ),
                ),
                ChatMessage(
                    role=MessageRole.USER,
                    content=_judge_payload(actual=actual, expected=expected, rubric=rubric),
                ),
            ),
        )
        response = await self.adapter.generate(request)
        try:
            payload: object = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise JudgeEvaluationError("judge response is not valid JSON") from exc
        try:
            judged = JudgeResponse.model_validate(payload)
        except ValidationError as exc:
            raise JudgeEvaluationError("judge response does not match the score contract") from exc

        evaluator = EvaluatorRef(
            evaluator_id=f"llm-judge:{self.config.judge_id}:{self.config.rubric_id}",
            version=self.config.rubric_version,
        )
        score = Score(
            metric="rubric_score",
            value=judged.score,
            evaluator=evaluator,
            higher_is_better=True,
        )
        provenance = JudgeProvenance(
            judge_id=self.config.judge_id,
            adapter_id=self.adapter.adapter_id,
            model_id=self.config.model_id,
            rubric_id=self.config.rubric_id,
            rubric_version=self.config.rubric_version,
            prompt_template_version=self.config.prompt_template_version,
            generation=self.config.generation,
        )
        return JudgeEvaluationResult(
            score=score,
            provenance=provenance,
            rationale=judged.rationale if self.config.retain_rationale else None,
        )


def _judge_payload(*, actual: object, expected: object, rubric: str) -> str:
    return json.dumps(
        {
            "rubric": rubric,
            "actual": actual,
            "expected": expected,
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
