"""Dimension-specific run compatibility rules.

Compatibility answers whether a delta is scientifically interpretable for a dimension.
It intentionally does not require the model/runtime/configuration under test to match:
those are often the variables the user wants to compare.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from .schemas import ExecutionFingerprint, FrozenModel, NonEmptyStr


class ComparisonDimension(StrEnum):
    CAPABILITY = "capability"
    RUNTIME = "runtime"
    RESOURCE = "resource"


class NonComparabilityCode(StrEnum):
    DATASET = "dataset_snapshot_mismatch"
    EVALUATOR = "evaluator_mismatch"
    BENCHMARK_PROTOCOL = "benchmark_protocol_mismatch"
    PROMPT_TEMPLATE = "prompt_template_mismatch"
    LOAD_PROFILE = "load_profile_mismatch"
    HARDWARE = "hardware_identity_mismatch"
    TELEMETRY_LEVEL = "telemetry_level_mismatch"
    TELEMETRY_PROTOCOL = "telemetry_protocol_mismatch"
    TELEMETRY_COLLECTORS = "telemetry_collectors_mismatch"
    ENDPOINT_IDENTITY = "endpoint_identity_mismatch"


class NonComparabilityReason(FrozenModel):
    code: NonComparabilityCode
    field: NonEmptyStr
    baseline: object | None = None
    candidate: object | None = None
    message: NonEmptyStr


class CompatibilityResult(FrozenModel):
    dimension: ComparisonDimension
    comparable: bool
    reasons: tuple[NonComparabilityReason, ...] = Field(default=())

    @classmethod
    def from_reasons(
        cls,
        dimension: ComparisonDimension,
        reasons: list[NonComparabilityReason],
    ) -> CompatibilityResult:
        return cls(
            dimension=dimension,
            comparable=not reasons,
            reasons=tuple(reasons),
        )


def _reason(
    code: NonComparabilityCode,
    field: str,
    baseline: object,
    candidate: object,
) -> NonComparabilityReason:
    return NonComparabilityReason(
        code=code,
        field=field,
        baseline=baseline,
        candidate=candidate,
        message=f"{field} differs between baseline and candidate",
    )


def _dataset_identity(fp: ExecutionFingerprint) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (item.dataset_id, item.dataset_version, item.content_sha256)
        for item in fp.dataset_snapshots
    )


def _evaluator_identity(fp: ExecutionFingerprint) -> tuple[tuple[str, str], ...]:
    return tuple((item.evaluator_id, item.version) for item in fp.evaluator_versions)


def compare_fingerprints(
    baseline: ExecutionFingerprint,
    candidate: ExecutionFingerprint,
    dimension: ComparisonDimension,
) -> CompatibilityResult:
    """Return typed reasons when two runs are not comparable for ``dimension``.

    Rules are deliberately conservative and versioned by code + benchmark protocol.
    The model identity, quantization, runtime identity and generation configuration are
    *not* invariant fields: they are valid experimental variables.
    """

    reasons: list[NonComparabilityReason] = []

    if baseline.benchmark_protocol_version != candidate.benchmark_protocol_version:
        reasons.append(
            _reason(
                NonComparabilityCode.BENCHMARK_PROTOCOL,
                "benchmark_protocol_version",
                baseline.benchmark_protocol_version,
                candidate.benchmark_protocol_version,
            )
        )

    if dimension == ComparisonDimension.CAPABILITY:
        if _dataset_identity(baseline) != _dataset_identity(candidate):
            reasons.append(
                _reason(
                    NonComparabilityCode.DATASET,
                    "dataset_snapshots",
                    _dataset_identity(baseline),
                    _dataset_identity(candidate),
                )
            )
        if _evaluator_identity(baseline) != _evaluator_identity(candidate):
            reasons.append(
                _reason(
                    NonComparabilityCode.EVALUATOR,
                    "evaluator_versions",
                    _evaluator_identity(baseline),
                    _evaluator_identity(candidate),
                )
            )
        if baseline.prompt_template_version != candidate.prompt_template_version:
            reasons.append(
                _reason(
                    NonComparabilityCode.PROMPT_TEMPLATE,
                    "prompt_template_version",
                    baseline.prompt_template_version,
                    candidate.prompt_template_version,
                )
            )

    elif dimension == ComparisonDimension.RUNTIME:
        if baseline.load_profile != candidate.load_profile:
            reasons.append(
                _reason(
                    NonComparabilityCode.LOAD_PROFILE,
                    "load_profile",
                    baseline.load_profile.model_dump(mode="json"),
                    candidate.load_profile.model_dump(mode="json"),
                )
            )
        if baseline.hardware != candidate.hardware:
            reasons.append(
                _reason(
                    NonComparabilityCode.HARDWARE,
                    "hardware",
                    baseline.hardware.model_dump(mode="json"),
                    candidate.hardware.model_dump(mode="json"),
                )
            )

    elif dimension == ComparisonDimension.RESOURCE:
        if baseline.hardware != candidate.hardware:
            reasons.append(
                _reason(
                    NonComparabilityCode.HARDWARE,
                    "hardware",
                    baseline.hardware.model_dump(mode="json"),
                    candidate.hardware.model_dump(mode="json"),
                )
            )
        if baseline.telemetry.level != candidate.telemetry.level:
            reasons.append(
                _reason(
                    NonComparabilityCode.TELEMETRY_LEVEL,
                    "telemetry.level",
                    baseline.telemetry.level,
                    candidate.telemetry.level,
                )
            )
        if baseline.telemetry.protocol_version != candidate.telemetry.protocol_version:
            reasons.append(
                _reason(
                    NonComparabilityCode.TELEMETRY_PROTOCOL,
                    "telemetry.protocol_version",
                    baseline.telemetry.protocol_version,
                    candidate.telemetry.protocol_version,
                )
            )
        if baseline.telemetry.collectors != candidate.telemetry.collectors:
            reasons.append(
                _reason(
                    NonComparabilityCode.TELEMETRY_COLLECTORS,
                    "telemetry.collectors",
                    baseline.telemetry.collectors,
                    candidate.telemetry.collectors,
                )
            )

    return CompatibilityResult.from_reasons(dimension, reasons)
