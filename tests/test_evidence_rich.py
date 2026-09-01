from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile

from performance_lab.domain import (
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    EvidenceMode,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    SampleContentEvidence,
    SampleExecution,
    SampleStatus,
    TaskSpec,
)
from performance_lab.run_config import StarterRunConfig
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_server import build_local_ui_app
from performance_lab.domain import EndpointProfile


def _run(run_id: str, status: RunStatus) -> Run:
    now = datetime.now(UTC)
    evaluator = EvaluatorRef(evaluator_id="exact-match", version="1")
    snapshot = DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="fixture",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )
    generation = GenerationConfig(max_output_tokens=8, temperature=0.0)
    suite = EvaluationSuite(
        suite_id="demo-suite",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="qa",
                dataset_snapshot_id="demo",
                evaluator=evaluator,
                metric_names=("exact_match",),
            ),
        ),
        generation=generation,
    )
    fingerprint = ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="loopback",
        model=ModelIdentity(model_id="model-a"),
        generation=generation,
        prompt_template_version="direct-user-v1",
        dataset_snapshots=(snapshot,),
        evaluator_versions=(evaluator,),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(request_count=1),
    )
    samples = ()
    completed_at = None
    if status != RunStatus.RUNNING:
        samples = (
            SampleExecution(
                sample_id="sample-1",
                task_id="qa",
                status=SampleStatus.SUCCEEDED,
                started_at=now,
                completed_at=now,
            ),
        )
        completed_at = now
    return Run(
        run_id=run_id,
        status=status,
        fingerprint=fingerprint,
        suite=suite,
        created_at=now,
        completed_at=completed_at,
        samples=samples,
    )


def test_evidence_rich_content_promotes_locally_but_never_enters_bundle(tmp_path: Path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    working = _run("run-rich", RunStatus.RUNNING)
    store.save_working(working)
    evidence = SampleContentEvidence(
        run_id="run-rich",
        task_id="qa",
        sample_id="sample-1",
        prompt="PRIVATE PROMPT",
        response="PRIVATE RESPONSE",
    )
    store.save_working_sample_content(evidence)

    assert store.get_sample_content("run-rich", "qa", "sample-1", 1) is None

    store.publish(_run("run-rich", RunStatus.SUCCEEDED))
    assert store.get_sample_content("run-rich", "qa", "sample-1", 1) == evidence

    bundle = store.export_bundle("run-rich", tmp_path / "run-rich.plab.zip")
    with ZipFile(bundle) as archive:
        assert set(archive.namelist()) == {"manifest.json", "run.json"}
        run_payload = archive.read("run.json").decode("utf-8")
    assert "PRIVATE PROMPT" not in run_payload
    assert "PRIVATE RESPONSE" not in run_payload
    assert "prompt" not in json.loads(run_payload)["samples"][0]

    assert store.delete_completed_sample_content("run-rich") == 1
    assert store.get_sample_content("run-rich", "qa", "sample-1", 1) is None
    assert store.get_completed("run-rich") is not None


def test_hard_restart_discards_sensitive_working_content_but_keeps_interrupted_run(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / "runs.sqlite3"
    store = SQLiteRunStore(store_path)
    store.save_working(_run("run-interrupted", RunStatus.RUNNING))
    store.save_working_sample_content(
        SampleContentEvidence(
            run_id="run-interrupted",
            task_id="qa",
            sample_id="sample-1",
            prompt="SENSITIVE WORKING PROMPT",
        )
    )
    endpoint = EndpointProfile(
        profile_id="local",
        base_url="http://127.0.0.1:1235/v1/",
        model_selector="model-a",
    )
    config = StarterRunConfig(
        target_id="target",
        endpoint_identity="127.0.0.1:1235",
        endpoint=endpoint,
        model_id="model-a",
        store_path=store_path,
        evidence_mode=EvidenceMode.AGGREGATE_SAFE,
    )

    build_local_ui_app(config)

    reopened = SQLiteRunStore(store_path)
    assert [run.run_id for run in reopened.list_working()] == ["run-interrupted"]
    assert reopened.delete_working_sample_content("run-interrupted") == 0
