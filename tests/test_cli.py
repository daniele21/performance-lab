import json
from io import StringIO

from performance_lab.cli import main
from performance_lab.domain import (
    DatasetSnapshot,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    ModelIdentity,
)
from performance_lab.plugins import AdapterCapabilities, ProbeResult


class FakeProbeAdapter:
    def __init__(self, profile) -> None:
        self.profile = profile

    async def probe(self) -> ProbeResult:
        return ProbeResult(
            healthy=True,
            adapter_id="openai-compatible",
            models=("model-a",),
            capabilities=AdapterCapabilities(streaming=True, model_discovery=True),
        )

    async def aclose(self) -> None:
        return None


def fingerprint() -> ExecutionFingerprint:
    dataset = DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="fixture",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )
    return ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="local",
        model=ModelIdentity(model_id="model-a"),
        generation=GenerationConfig(max_output_tokens=8, temperature=0.0),
        prompt_template_version="chat-v1",
        dataset_snapshots=(dataset,),
        evaluator_versions=(EvaluatorRef(evaluator_id="exact", version="1"),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(),
    )


def test_probe_json_output(monkeypatch) -> None:
    monkeypatch.setattr("performance_lab.cli.OpenAICompatibleAdapter", FakeProbeAdapter)
    output = StringIO()
    exit_code = main(
        ["probe", "--base-url", "http://localhost:1234/v1/", "--json"],
        stdout=output,
    )
    payload = json.loads(output.getvalue())
    assert exit_code == 0
    assert payload["healthy"] is True
    assert payload["models"] == ["model-a"]


def test_inspect_fingerprint(tmp_path) -> None:
    source = tmp_path / "fingerprint.json"
    source.write_text(fingerprint().model_dump_json(), encoding="utf-8")
    output = StringIO()
    exit_code = main(["inspect", str(source)], stdout=output)
    assert exit_code == 0
    assert "Kind: execution_fingerprint" in output.getvalue()
    assert "Model: model-a" in output.getvalue()


def test_inspect_rejects_invalid_json(tmp_path) -> None:
    source = tmp_path / "bad.json"
    source.write_text("not-json", encoding="utf-8")
    output = StringIO()
    exit_code = main(["inspect", str(source)], stdout=output)
    assert exit_code == 2
    assert "invalid JSON" in output.getvalue()
