from datetime import UTC, datetime

from fastapi.testclient import TestClient

from performance_lab.application import UIQueryService
from performance_lab.domain import (
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    TaskSpec,
)
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app


def _run() -> Run:
    evaluator = EvaluatorRef(evaluator_id="exact-match", version="1")
    dataset = DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="builtin",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )
    generation = GenerationConfig(max_output_tokens=16, temperature=0.0)
    suite = EvaluationSuite(
        suite_id="starter",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="qa",
                dataset_snapshot_id="demo",
                evaluator=evaluator,
                metric_names=("accuracy",),
            ),
        ),
        generation=generation,
    )
    now = datetime.now(UTC)
    return Run(
        run_id="run-1",
        status=RunStatus.SUCCEEDED,
        fingerprint=ExecutionFingerprint(
            target_id="local",
            adapter_type="openai-compatible",
            endpoint_identity="loopback",
            model=ModelIdentity(model_id="model-a"),
            generation=generation,
            prompt_template_version="chat-v1",
            dataset_snapshots=(dataset,),
            evaluator_versions=(evaluator,),
            benchmark_protocol_version="bench-v1",
            load_profile=LoadProfile(),
        ),
        suite=suite,
        created_at=now,
        completed_at=now,
    )


def test_versioned_read_api_serves_completed_evidence(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(_run())
    client = TestClient(create_ui_app(UIQueryService(store)))

    assert client.get("/api/v1/health").json() == {
        "status": "ok",
        "api_version": "v1",
    }
    runs = client.get("/api/v1/runs")
    assert runs.status_code == 200
    assert runs.json()[0]["run_id"] == "run-1"
    detail = client.get("/api/v1/runs/run-1")
    assert detail.status_code == 200
    assert detail.json()["summary"]["fingerprint_id"]
    assert client.get("/api/v1/runs/missing").status_code == 404
