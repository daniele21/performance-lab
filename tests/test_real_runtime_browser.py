from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests" / "real_runtime" / "browser_local_llm_server.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("value01_real_browser", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_browser_config_requires_first_party_identity_and_evidence_rich(tmp_path: Path) -> None:
    module = _load_script()
    config = module.build_browser_run_config(
        base_url="http://127.0.0.1:1235/",
        model="qwen",
        store_path=tmp_path / "runs.sqlite3",
    )

    assert config["target_id"] == "local-llm-server-value01-browser"
    assert config["endpoint"]["base_url"] == "http://127.0.0.1:1235/v1/"
    assert config["endpoint"]["model_selector"] == "qwen"
    assert config["evidence_mode"] == "evidence_rich"
    assert config["local_llm_server_identity"]["required"] is True
    assert config["local_llm_server_identity"]["model_id"] == "qwen"
    assert config["local_llm_server_telemetry"]["model_id"] == "qwen"
