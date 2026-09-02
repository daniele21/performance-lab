from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from performance_lab.domain import (
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    HardwareIdentity,
    LoadProfile,
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
    ModelIdentity,
    Run,
    RunStatus,
    RuntimeIdentity,
    SampleContentEvidence,
    SampleExecution,
    SampleStatus,
    TaskSpec,
    TelemetryDescriptor,
    TelemetryLevel,
)
from performance_lab.storage import SQLiteRunStore

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "tests" / "real_runtime" / "verify_value01_evidence.py"


def _suite() -> EvaluationSuite:
    evaluator = EvaluatorRef(evaluator_id="normalized_exact_match", version="1")
    return EvaluationSuite(
        suite_id="general-diagnostic-starter",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="qa",
                dataset_snapshot_id="demo",
                evaluator=evaluator,
                metric_names=("normalized_exact_match",),
            ),
        ),
        generation=GenerationConfig(max_output_tokens=16, temperature=0.0),
    )


def _run(run_id: str = "value01-real") -> Run:
    now = datetime.now(UTC)
    suite = _suite()
    evaluator = suite.tasks[0].evaluator
    fingerprint = ExecutionFingerprint(
        target_id="local-llm-server-real",
        adapter_type="openai-compatible",
        endpoint_identity="127.0.0.1:1235",
        model=ModelIdentity(model_id="qwen", revision="r1", quantization="Q4_K_M"),
        runtime=RuntimeIdentity(
            name="llama.cpp",
            version="b1234",
            config_digest="a" * 64,
        ),
        hardware=HardwareIdentity(
            device_class="arm64",
            cpu="Apple M4",
            memory_bytes=16 * 1024**3,
            os="Darwin",
        ),
        generation=suite.generation,
        prompt_template_version="direct-user-v1",
        dataset_snapshots=(
            DatasetSnapshot(
                dataset_id="demo",
                dataset_version="1",
                source="builtin",
                split="test",
                content_sha256="b" * 64,
                selection_policy="all",
                sample_count=1,
            ),
        ),
        evaluator_versions=(evaluator,),
        benchmark_protocol_version="starter-quality-v1",
        load_profile=LoadProfile(concurrency=1, request_count=1, streaming=False),
        telemetry=TelemetryDescriptor(
            level=TelemetryLevel.INSTRUMENTED,
            protocol_version="local-llm-server-status-v1",
            collectors=("local-llm-server-status",),
        ),
    )
    sample = SampleExecution(
        sample_id="sample-1",
        task_id="qa",
        status=SampleStatus.SUCCEEDED,
        started_at=now,
        completed_at=now,
    )
    measurement = Measurement(
        name="status_sample_count",
        value=3.0,
        unit="count",
        scope=MeasurementScope.RUN,
        provenance=MeasurementProvenance.RUNTIME,
        protocol_version="local-llm-server-status-v1",
        observed_at=now,
    )
    return Run(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=suite,
        created_at=now,
        completed_at=now,
        aggregate_measurements=(measurement,),
        samples=(sample,),
    )


def _publish(
    store: SQLiteRunStore,
    completed: Run,
    *,
    retain_content: bool,
) -> None:
    working = Run(
        run_id=completed.run_id,
        status=RunStatus.RUNNING,
        fingerprint=completed.fingerprint,
        suite=completed.suite,
        created_at=completed.created_at,
    )
    store.save_working(working)
    if retain_content:
        sample = completed.samples[0]
        store.save_working_sample_content(
            SampleContentEvidence(
                run_id=completed.run_id,
                task_id=sample.task_id,
                sample_id=sample.sample_id,
                attempt=sample.attempt,
                prompt="Reply with exactly: BLUE",
                response="BLUE",
            )
        )
    store.publish(completed)


def _verify(
    *,
    store_path: Path,
    bundle_path: Path,
    run_id: str,
    output_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--store",
            str(store_path),
            "--bundle",
            str(bundle_path),
            "--run-id",
            run_id,
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_value01_evidence_verifier_accepts_complete_real_evidence_shape(tmp_path: Path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    bundle_path = tmp_path / "value01-real.plab.zip"
    output_path = tmp_path / "verification.json"
    store = SQLiteRunStore(store_path)
    completed = _run()
    _publish(store, completed, retain_content=True)
    store.export_bundle(completed.run_id, bundle_path)

    result = _verify(
        store_path=store_path,
        bundle_path=bundle_path,
        run_id=completed.run_id,
        output_path=output_path,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "PASS"
    assert {check["name"] for check in manifest["checks"]} == {
        "completed_run",
        "portable_bundle_exists",
        "portable_bundle_shape",
        "portable_bundle_round_trip",
        "first_party_runtime_identity",
        "first_party_device_identity",
        "runtime_telemetry_descriptor",
        "runtime_telemetry_measurements",
        "local_sample_content",
    }
    assert all(check["status"] == "PASS" for check in manifest["checks"])


def test_value01_evidence_verifier_rejects_missing_evidence_rich_content(tmp_path: Path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    bundle_path = tmp_path / "value01-real.plab.zip"
    output_path = tmp_path / "verification.json"
    store = SQLiteRunStore(store_path)
    completed = _run()
    _publish(store, completed, retain_content=False)
    store.export_bundle(completed.run_id, bundle_path)

    result = _verify(
        store_path=store_path,
        bundle_path=bundle_path,
        run_id=completed.run_id,
        output_path=output_path,
    )

    assert result.returncode == 1
    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "FAIL"
    content_check = next(
        check for check in manifest["checks"] if check["name"] == "local_sample_content"
    )
    assert content_check["status"] == "FAIL"
