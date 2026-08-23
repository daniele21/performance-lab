from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient

from performance_lab.domain import EndpointProfile, HardwareIdentity
from performance_lab.run_config import StarterRunConfig
from performance_lab.ui_server import UI_SERVER_HOST, build_local_ui_app, main


def _config(tmp_path: Path) -> StarterRunConfig:
    return StarterRunConfig(
        target_id="local-target",
        endpoint_identity="loopback:1234",
        endpoint=EndpointProfile(
            profile_id="local-openai",
            base_url="http://127.0.0.1:1234/v1",
            timeout_seconds=30,
        ),
        model_id="configured-model",
        store_path=tmp_path / "custom-runs.sqlite3",
        run_id="cli-only-run-id",
        hardware=HardwareIdentity(device_id="device-a", device_class="laptop"),
    )


def test_local_ui_composition_preserves_execution_template_in_frozen_preflight(tmp_path) -> None:
    config = _config(tmp_path)

    with TestClient(build_local_ui_app(config)) as client:
        targets = client.get("/api/v1/targets")
        assert targets.status_code == 200
        assert targets.json()[0]["target_id"] == "local-target"

        jobs = client.get("/api/v1/run-jobs")
        assert jobs.status_code == 200
        assert jobs.json() == []

        preflight = client.post(
            "/api/v1/run-preflight",
            json={
                "target_id": "local-target",
                "model_id": "model-from-browser",
                "scenario": "general_capability",
                "use_host_telemetry": True,
            },
        )
        assert preflight.status_code == 200
        preview = preflight.json()["preview"]
        assert preview is not None
        frozen = preview["config"]
        assert frozen["store_path"] == str(config.store_path)
        assert frozen["model_id"] == "model-from-browser"
        assert frozen["run_id"] is None
        assert frozen["use_host_telemetry"] is True
        assert frozen["hardware"]["device_id"] == "device-a"
        assert frozen["hardware"]["device_class"] == "laptop"


def test_local_ui_can_serve_built_frontend_without_shadowing_api(tmp_path) -> None:
    config = _config(tmp_path)
    assets = tmp_path / "web"
    assets.mkdir()
    (assets / "index.html").write_text("<html><body>built-performance-lab</body></html>", encoding="utf-8")

    with TestClient(build_local_ui_app(config, assets_dir=assets)) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "built-performance-lab" in page.text
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"


def test_ui_entrypoint_loads_config_and_keeps_listener_on_loopback(tmp_path, monkeypatch) -> None:
    config = _config(tmp_path)
    config_path = tmp_path / "ui-config.json"
    config_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    called: dict[str, object] = {}

    def fake_serve(value: StarterRunConfig, *, port: int, assets_dir: Path | None) -> None:
        called["config"] = value
        called["port"] = port
        called["assets_dir"] = assets_dir

    monkeypatch.setattr("performance_lab.ui_server.serve_local_ui", fake_serve)
    stdout = StringIO()
    stderr = StringIO()

    result = main(
        ["--config", str(config_path), "--port", "9876"],
        stdout=stdout,
        stderr=stderr,
    )

    assert result == 0
    assert called == {"config": config, "port": 9876, "assets_dir": None}
    assert f"http://{UI_SERVER_HOST}:9876" in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_ui_entrypoint_accepts_built_assets(tmp_path, monkeypatch) -> None:
    config = _config(tmp_path)
    config_path = tmp_path / "ui-config.json"
    config_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    assets = tmp_path / "web"
    assets.mkdir()
    (assets / "index.html").write_text("<html></html>", encoding="utf-8")
    called: dict[str, object] = {}

    def fake_serve(value: StarterRunConfig, *, port: int, assets_dir: Path | None) -> None:
        called["config"] = value
        called["port"] = port
        called["assets_dir"] = assets_dir

    monkeypatch.setattr("performance_lab.ui_server.serve_local_ui", fake_serve)
    stdout = StringIO()
    stderr = StringIO()

    result = main(
        ["--config", str(config_path), "--assets", str(assets), "--port", "9876"],
        stdout=stdout,
        stderr=stderr,
    )

    assert result == 0
    assert called["config"] == config
    assert called["port"] == 9876
    assert called["assets_dir"] == assets.resolve()
    assert "built product" in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_ui_entrypoint_rejects_invalid_port_before_starting_server(tmp_path) -> None:
    config = _config(tmp_path)
    config_path = tmp_path / "ui-config.json"
    config_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    stderr = StringIO()

    result = main(["--config", str(config_path), "--port", "0"], stderr=stderr)

    assert result == 2
    assert "port must be between 1 and 65535" in stderr.getvalue()


def test_ui_entrypoint_rejects_missing_built_index(tmp_path) -> None:
    config = _config(tmp_path)
    config_path = tmp_path / "ui-config.json"
    config_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    assets = tmp_path / "web"
    assets.mkdir()
    stderr = StringIO()

    result = main(
        ["--config", str(config_path), "--assets", str(assets)],
        stderr=stderr,
    )

    assert result == 2
    assert "missing index.html" in stderr.getvalue()
