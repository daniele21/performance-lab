from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from performance_lab.domain.compatibility import (
    ComparisonDimension,
    NonComparabilityCode,
    compare_fingerprints,
)
from performance_lab.domain.schemas import (
    DatasetSnapshot,
    EndpointProfile,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    HardwareIdentity,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    SampleExecution,
    SampleStatus,
    Score,
    TaskSpec,
    TelemetryDescriptor,
    TelemetryLevel,
)
from performance_lab.domain.serialization import (
    UnsupportedSchemaVersion,
    load_json,
)


def dataset(version: str = "1") -> DatasetSnapshot:
    return DatasetSnapshot(
        dataset_id="general-reasoning",
        dataset_version=version,
        source="builtin",
        split="test",
        content_sha256="a" * 64,
        selection_policy="first-10-v1",
        sample_count=10,
    )


def evaluator(version: str = "1") -> EvaluatorRef:
    return EvaluatorRef(evaluator_id="exact-match", version=version)


def generation(temperature: float | None = 0.0) -> GenerationConfig:
    return GenerationConfig(max_output_tokens=128, temperature=temperature, seed=7)


def fingerprint(
    *,
    hardware: HardwareIdentity | None = None,
    telemetry: TelemetryDescriptor | None = None,
    dataset_snapshot: DatasetSnapshot | None = None,
    evaluator_ref: EvaluatorRef | None = None,
    prompt_template_version: str = "chat-v1",
    benchmark_protocol_version: str = "bench-v1",
    load_profile: LoadProfile | None = None,
    model_id: str = "model-a",
    temperature: float | None = 0.0,
) -> ExecutionFingerprint:
    return ExecutionFingerprint(
        target_id="target-1",
        adapter_type="openai-compatible",
        endpoint_identity="local-device-a",
        model=ModelIdentity(model_id=model_id),
        hardware=hardware or HardwareIdentity(device_id="device-a", os="linux"),
        generation=generation(temperature),
        prompt_template_version=prompt_template_version,
        dataset_snapshots=(dataset_snapshot or dataset(),),
        evaluator_versions=(evaluator_ref or evaluator(),),
        benchmark_protocol_version=benchmark_protocol_version,
        load_profile=load_profile or LoadProfile(concurrency=1, request_count=10),
        telemetry=telemetry or TelemetryDescriptor(),
    )


def suite() -> EvaluationSuite:
    return EvaluationSuite(
        suite_id="smoke",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="reasoning",
                dataset_snapshot_id="general-reasoning",
                evaluator=evaluator(),
                metric_names=("accuracy",),
            ),
        ),
        generation=generation(),
    )


def test_endpoint_profile_never_models_raw_secret() -> None:
    profile = EndpointProfile(profile_id="local", base_url="http://localhost:8080")
    payload = profile.model_dump(mode="json")
    assert "secret" not in str(payload).lower()
    with pytest.raises(ValidationError):
        EndpointProfile(
            profile_id="bad",
            base_url="http://localhost:8080",
            secret="raw-token",  # type: ignore[call-arg]
        )


def test_fingerprint_round_trip_and_digest_are_stable() -> None:
    original = fingerprint()
    restored = load_json(ExecutionFingerprint, original.model_dump_json())
    assert restored == original
    assert restored.fingerprint_id == original.fingerprint_id
    assert restored.canonical_json() == original.canonical_json()


def test_unknown_identity_fields_are_explicit_nulls() -> None:
    fp = ExecutionFingerprint(
        target_id="target-1",
        adapter_type="openai-compatible",
        endpoint_identity="opaque-endpoint",
        model=ModelIdentity(model_id="model-a"),
        generation=generation(),
        prompt_template_version="chat-v1",
        dataset_snapshots=(dataset(),),
        evaluator_versions=(evaluator(),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(),
    )
    payload = fp.model_dump(mode="json")
    assert payload["runtime"]["name"] is None
    assert payload["hardware"]["device_id"] is None


def test_schema_loader_rejects_future_version() -> None:
    payload = fingerprint().model_dump(mode="json")
    payload["schema_version"] = 2
    with pytest.raises(UnsupportedSchemaVersion):
        load_json(ExecutionFingerprint, __import__("json").dumps(payload))


def test_capability_allows_model_change_but_rejects_dataset_change() -> None:
    baseline = fingerprint(model_id="model-a")
    candidate = fingerprint(model_id="model-b")
    result = compare_fingerprints(
        baseline, candidate, ComparisonDimension.CAPABILITY
    )
    assert result.comparable

    changed_dataset = dataset(version="2").model_copy(
        update={"content_sha256": "b" * 64}
    )
    candidate = fingerprint(model_id="model-b", dataset_snapshot=changed_dataset)
    result = compare_fingerprints(
        baseline, candidate, ComparisonDimension.CAPABILITY
    )
    assert not result.comparable
    assert result.reasons[0].code == NonComparabilityCode.DATASET


def test_runtime_requires_same_hardware_and_load_profile() -> None:
    baseline = fingerprint()
    candidate = fingerprint(
        hardware=HardwareIdentity(device_id="device-b", os="linux")
    )
    result = compare_fingerprints(baseline, candidate, ComparisonDimension.RUNTIME)
    assert not result.comparable
    assert {reason.code for reason in result.reasons} == {
        NonComparabilityCode.HARDWARE
    }


def test_resource_requires_matching_telemetry_provenance_contract() -> None:
    baseline = fingerprint(
        telemetry=TelemetryDescriptor(
            level=TelemetryLevel.HOST,
            protocol_version="host-v1",
            collectors=("psutil-v1",),
        )
    )
    candidate = fingerprint(
        telemetry=TelemetryDescriptor(
            level=TelemetryLevel.HOST,
            protocol_version="host-v2",
            collectors=("psutil-v1",),
        )
    )
    result = compare_fingerprints(baseline, candidate, ComparisonDimension.RESOURCE)
    assert not result.comparable
    assert NonComparabilityCode.TELEMETRY_PROTOCOL in {
        reason.code for reason in result.reasons
    }


def test_terminal_run_requires_completion_time() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        Run(
            run_id="run-1",
            status=RunStatus.SUCCEEDED,
            fingerprint=fingerprint(),
            suite=suite(),
            created_at=now,
        )


def test_sample_failure_requires_typed_error() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        SampleExecution(
            sample_id="sample-1",
            task_id="reasoning",
            status=SampleStatus.FAILED,
            started_at=now,
            completed_at=now,
        )


def test_models_are_immutable() -> None:
    score = Score(
        metric="accuracy",
        value=1.0,
        evaluator=evaluator(),
        higher_is_better=True,
    )
    with pytest.raises(ValidationError):
        score.value = 0.0  # type: ignore[misc]
