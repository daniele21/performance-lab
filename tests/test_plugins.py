import asyncio
from pathlib import Path

import pytest
from pydantic import ValidationError

from performance_lab.domain import GenerationConfig
from performance_lab.plugins import (
    ChatMessage,
    DuplicatePluginError,
    FakeInferenceAdapter,
    FakeTaskLoader,
    InferenceRequest,
    MessageRole,
    PluginKind,
    PluginNotFoundError,
    PluginRegistry,
)


def inference_request() -> InferenceRequest:
    return InferenceRequest(
        request_id="request-1",
        messages=(ChatMessage(role=MessageRole.USER, content="hello"),),
        generation=GenerationConfig(max_output_tokens=16, temperature=0.0),
        model="fake-model",
    )


def test_registry_is_explicit_and_rejects_duplicate_ids() -> None:
    registry = PluginRegistry()
    adapter = FakeInferenceAdapter()
    registry.register(PluginKind.INFERENCE_ADAPTER, adapter.adapter_id, adapter)

    assert registry.require(PluginKind.INFERENCE_ADAPTER, adapter.adapter_id) is adapter
    assert registry.ids(PluginKind.INFERENCE_ADAPTER) == ("fake-inference",)

    with pytest.raises(DuplicatePluginError):
        registry.register(PluginKind.INFERENCE_ADAPTER, adapter.adapter_id, adapter)
    with pytest.raises(PluginNotFoundError):
        registry.require(PluginKind.EVALUATOR, "missing")


def test_fake_inference_adapter_is_deterministic() -> None:
    async def exercise() -> tuple[str, list[str]]:
        adapter = FakeInferenceAdapter(response_text="answer", stream_deltas=("an", "swer"))
        request = inference_request()
        response = await adapter.generate(request)
        deltas = [chunk.text_delta async for chunk in adapter.stream(request)]
        return response.text, deltas

    text, deltas = asyncio.run(exercise())
    assert text == "answer"
    assert deltas == ["an", "swer"]


def test_fake_task_loader_returns_test_fixture() -> None:
    loader = FakeTaskLoader(({"id": "1", "prompt": "hello"},))
    records = loader.load(Path("ignored.jsonl"), split="test")
    assert tuple(records) == ({"id": "1", "prompt": "hello"},)


def test_plugin_contract_values_are_immutable() -> None:
    request = inference_request()
    with pytest.raises(ValidationError):
        request.request_id = "other"  # type: ignore[misc]
