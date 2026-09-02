"""Capability evaluation primitives and optional judge-based evaluation."""

from .descriptors import EvaluatorDescriptor, describe_evaluator
from .deterministic import (
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
    normalize_text,
)
from .judge import (
    JudgeConfig,
    JudgeEvaluationError,
    JudgeEvaluationResult,
    JudgeProvenance,
    JudgeResponse,
    LLMRubricJudge,
)

__all__ = [
    "ClassificationAccuracyEvaluator",
    "EvaluationError",
    "EvaluatorDescriptor",
    "ExactMatchEvaluator",
    "FieldExtractionEvaluator",
    "JSONParseEvaluator",
    "JSONSchemaEvaluator",
    "JudgeConfig",
    "JudgeEvaluationError",
    "JudgeEvaluationResult",
    "JudgeProvenance",
    "JudgeResponse",
    "LLMRubricJudge",
    "NormalizedExactMatchEvaluator",
    "NumericToleranceEvaluator",
    "RegexValidityEvaluator",
    "SetPRFEvaluator",
    "aggregate_scores",
    "describe_evaluator",
    "normalize_text",
]
