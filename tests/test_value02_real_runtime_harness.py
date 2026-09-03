from pathlib import Path

import pytest
from tests.real_runtime.browser_value02_local_llm_server import (
    _candidate_models,
    _case_from_hash,
    build_value02_ui_config,
    normalize_models,
)


def test_value02_requires_two_unique_models() -> None:
    assert normalize_models([" model-a ", "model-b", "model-a"]) == ("model-a", "model-b")
    with pytest.raises(ValueError, match="at least two unique"):
        normalize_models(["model-a", "model-a"])


def test_value02_config_keeps_first_party_evidence_enabled(tmp_path: Path) -> None:
    config = build_value02_ui_config(
        base_url="http://127.0.0.1:1235/",
        models=("model-a", "model-b"),
        store_path=tmp_path / "runs.sqlite3",
    )

    assert config["target_id"] == "local-llm-server-value02"
    assert config["endpoint"]["base_url"] == "http://127.0.0.1:1235/v1/"
    assert config["model_id"] == "model-a"
    assert config["evidence_mode"] == "aggregate_safe"
    assert config["local_llm_server_identity"]["required"] is True
    assert config["local_llm_server_identity"]["model_id"] == "model-a"
    assert config["local_llm_server_telemetry"]["model_id"] == "model-a"


def test_value02_candidate_inventory_reads_only_the_selected_target() -> None:
    planning = {
        "targets": [
            {
                "target": {"target_id": "other"},
                "candidates": [{"model_id": "wrong-model"}],
            },
            {
                "target": {"target_id": "local-llm-server-value02"},
                "candidates": [{"model_id": "model-a"}, {"model_id": "model-b"}],
            },
        ]
    }

    assert _candidate_models(planning, target_id="local-llm-server-value02") == (
        "model-a",
        "model-b",
    )


def test_value02_case_hash_extracts_exact_task_and_sample() -> None:
    assert _case_from_hash("#campaigns/c-1/cases/reasoning/case-7") == ("reasoning", "case-7")
    assert _case_from_hash("#campaigns/c-1") is None
