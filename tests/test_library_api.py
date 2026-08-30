from fastapi.testclient import TestClient

from performance_lab.application import UIQueryService
from performance_lab.datasets import build_general_starter_suite
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app


def _client(tmp_path):
    bundle = build_general_starter_suite()
    queries = UIQueryService(
        SQLiteRunStore(tmp_path / "runs.sqlite3"),
        suites=(bundle.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
        inspectable_datasets=tuple(bundle.datasets.values()),
        evaluators=tuple(bundle.evaluators.values()),
    )
    return TestClient(create_ui_app(queries)), bundle


def test_benchmark_definition_api_exposes_cases_without_result_semantics(tmp_path) -> None:
    client, bundle = _client(tmp_path)

    listing = client.get("/api/v1/benchmarks")
    assert listing.status_code == 200
    assert listing.json() == [
        {
            "api_version": "v1",
            "read_model_version": 1,
            "suite_id": bundle.suite.suite_id,
            "suite_version": bundle.suite.suite_version,
            "task_count": 7,
            "task_ids": [task.task_id for task in bundle.suite.tasks],
        }
    ]

    detail = client.get(f"/api/v1/benchmarks/{bundle.suite.suite_id}/{bundle.suite.suite_version}")
    assert detail.status_code == 200
    payload = detail.json()
    assert len(payload["cases"]) == 23
    assert payload["definition_issues"] == []
    assert "run_id" not in payload
    assert "score" not in payload
    assert payload["cases"][0]["input"]
    assert "weight" not in payload["tasks"][0]["evaluator"]


def test_evaluator_api_exposes_owned_rules_without_global_weight(tmp_path) -> None:
    client, _ = _client(tmp_path)

    response = client.get("/api/v1/evaluators")

    assert response.status_code == 200
    evaluators = response.json()
    numeric = next(item for item in evaluators if item["evaluator_id"] == "numeric-tolerance")
    assert numeric["deterministic"] is True
    assert numeric["explanation_supported"] is False
    assert numeric["configuration"]["absolute_tolerance"] == 1e-9
    assert numeric["rule_summary"]
    assert "weight" not in numeric


def test_benchmark_api_requires_exact_known_version(tmp_path) -> None:
    client, bundle = _client(tmp_path)

    response = client.get(f"/api/v1/benchmarks/{bundle.suite.suite_id}/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "benchmark definition not found"}
