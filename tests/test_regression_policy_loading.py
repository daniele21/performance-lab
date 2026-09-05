from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient

from performance_lab import artifact_launcher
from performance_lab.regression import MetricThresholdRule, RegressionPolicy
from performance_lab.ui_server import build_local_ui_app, main


def _policy() -> RegressionPolicy:
    return RegressionPolicy(
        policy_id="release-gate",
        policy_version="1",
        rules=(
            MetricThresholdRule(
                rule_id="accuracy",
                dimension="capability",
                metric="accuracy|exact-match@1",
                max_absolute_regression=0.02,
            ),
        ),
    )


def test_local_ui_lists_only_explicitly_loaded_regression_policies(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with TestClient(build_local_ui_app(regression_policies=(_policy(),))) as client:
        policies = client.get("/api/v1/regression-policies")
        assert policies.status_code == 200
        assert policies.json() == [
            {
                "api_version": "v1",
                "read_model_version": 1,
                "policy_id": "release-gate",
                "policy_version": "1",
                "rule_count": 1,
            }
        ]


def test_ui_entrypoint_loads_repeatable_versioned_policy_files(tmp_path, monkeypatch) -> None:
    policy_path = tmp_path / "release-policy.json"
    policy_path.write_text(_policy().model_dump_json(indent=2), encoding="utf-8")
    called: dict[str, object] = {}

    def fake_serve(
        config,
        *,
        port: int,
        assets_dir: Path | None,
        regression_policies: tuple[RegressionPolicy, ...],
    ) -> None:
        called["config"] = config
        called["port"] = port
        called["assets_dir"] = assets_dir
        called["policies"] = regression_policies

    monkeypatch.setattr("performance_lab.ui_server.serve_local_ui", fake_serve)
    stderr = StringIO()

    result = main(["--regression-policy", str(policy_path)], stderr=stderr)

    assert result == 0
    assert called["config"] is None
    assert called["port"] == 8765
    assert called["assets_dir"] is None
    assert called["policies"] == (_policy(),)
    assert stderr.getvalue() == ""


def test_artifact_launcher_command_forwards_explicit_policy_files(tmp_path) -> None:
    python = tmp_path / "runtime" / "bin" / "python"
    root = tmp_path / "artifact"
    config = tmp_path / "config.json"
    first = tmp_path / "policy-a.json"
    second = tmp_path / "policy-b.json"

    command = artifact_launcher.build_ui_command(
        python=python,
        root=root,
        port=9876,
        config=config,
        regression_policies=(first, second),
    )

    assert command[:3] == [str(python), "-m", "performance_lab.ui_server"]
    assert command.count("--regression-policy") == 2
    assert command[-4:] == ["--regression-policy", str(first), "--regression-policy", str(second)]
