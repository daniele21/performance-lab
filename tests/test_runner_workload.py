import pytest

from performance_lab.run_config import StarterRunConfig
from performance_lab.runner import RunExecutionError, _resolve_execution_bundle
from performance_lab.domain import EndpointProfile


def _config(*, suite_id: str, suite_version: str | None) -> StarterRunConfig:
    return StarterRunConfig(
        target_id="target-a",
        endpoint_identity="loopback:1234",
        endpoint=EndpointProfile(
            profile_id="endpoint-a",
            base_url="http://127.0.0.1:1234/v1",
        ),
        model_id="model-a",
        suite_id=suite_id,
        suite_version=suite_version,
    )


def test_runner_resolves_versioned_workload_pack() -> None:
    bundle = _resolve_execution_bundle(
        _config(
            suite_id="workload-structured-document-extraction",
            suite_version="2026-08-15-v1",
        )
    )

    assert bundle.suite.suite_id == "workload-structured-document-extraction"
    assert bundle.suite.suite_version == "2026-08-15-v1"
    assert bundle.benchmark_protocol_version == "workload-quality-v1"


def test_runner_rejects_unknown_suite_version() -> None:
    with pytest.raises(RunExecutionError):
        _resolve_execution_bundle(
            _config(
                suite_id="workload-structured-document-extraction",
                suite_version="missing-version",
            )
        )
