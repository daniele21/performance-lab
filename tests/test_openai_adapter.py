import asyncio
import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from performance_lab.adapters import OpenAICompatibleAdapter
from performance_lab.domain import AuthConfig, AuthStrategy, EndpointProfile, GenerationConfig
from performance_lab.plugins import (
    ChatMessage,
    InferenceAdapterError,
    InferenceErrorCode,
    InferenceRequest,
    MessageRole,
)


class FakeOpenAIHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def _send_json(self, status: int, payload: object) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            self._send_json(200, {"data": [{"id": "fake-model"}]})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        if payload.get("model") == "server-error":
            self._send_json(503, {"error": "unavailable"})
            return
        if payload.get("stream"):
            events = [
                {
                    "model": "fake-model",
                    "choices": [{"delta": {"content": "hel"}, "finish_reason": None}],
                },
                {
                    "model": "fake-model",
                    "choices": [{"delta": {"content": "lo"}, "finish_reason": "stop"}],
                },
                {
                    "model": "fake-model",
                    "choices": [],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2},
                },
            ]
            body = "".join(f"data: {json.dumps(event)}\n\n" for event in events)
            body += "data: [DONE]\n\n"
            encoded = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        self._send_json(
            200,
            {
                "model": "fake-model",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "hello"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2},
            },
        )


@contextmanager
def fake_openai_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOpenAIHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/v1/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def request(model: str = "fake-model") -> InferenceRequest:
    return InferenceRequest(
        request_id="request-1",
        messages=(ChatMessage(role=MessageRole.USER, content="say hello"),),
        generation=GenerationConfig(
            max_output_tokens=16,
            temperature=0.0,
            seed=7,
            response_format="json_object",
        ),
        model=model,
    )


def test_probe_and_generate_against_local_server() -> None:
    async def exercise(base_url: str) -> tuple[object, object]:
        adapter = OpenAICompatibleAdapter(
            EndpointProfile(profile_id="local", base_url=base_url, model_selector="fake-model")
        )
        try:
            return await adapter.probe(), await adapter.generate(request())
        finally:
            await adapter.aclose()

    with fake_openai_server() as base_url:
        probe, response = asyncio.run(exercise(base_url))

    assert probe.healthy
    assert probe.models == ("fake-model",)
    assert response.text == "hello"
    assert response.usage is not None
    assert response.usage.input_tokens == 3
    assert response.usage.output_tokens == 2


def test_stream_exposes_client_boundary_timestamps_and_usage() -> None:
    async def exercise(base_url: str) -> list[object]:
        adapter = OpenAICompatibleAdapter(
            EndpointProfile(profile_id="local", base_url=base_url, model_selector="fake-model")
        )
        try:
            return [chunk async for chunk in adapter.stream(request())]
        finally:
            await adapter.aclose()

    with fake_openai_server() as base_url:
        chunks = asyncio.run(exercise(base_url))

    assert "".join(chunk.text_delta for chunk in chunks) == "hello"
    assert all(chunk.emitted_at_ns > 0 for chunk in chunks)
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.output_tokens == 2


def test_server_errors_are_normalized() -> None:
    async def exercise(base_url: str) -> None:
        adapter = OpenAICompatibleAdapter(EndpointProfile(profile_id="local", base_url=base_url))
        try:
            with pytest.raises(InferenceAdapterError) as error:
                await adapter.generate(request(model="server-error"))
            assert error.value.code == InferenceErrorCode.SERVER
            assert error.value.retryable
            assert error.value.status_code == 503
        finally:
            await adapter.aclose()

    with fake_openai_server() as base_url:
        asyncio.run(exercise(base_url))


def test_missing_environment_credential_fails_before_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PERF_LAB_TEST_TOKEN", raising=False)
    profile = EndpointProfile(
        profile_id="secured",
        base_url="http://127.0.0.1:1/v1/",
        auth=AuthConfig(
            strategy=AuthStrategy.BEARER_ENV,
            credential_env="PERF_LAB_TEST_TOKEN",
        ),
    )
    with pytest.raises(InferenceAdapterError) as error:
        OpenAICompatibleAdapter(profile)
    assert error.value.code == InferenceErrorCode.AUTHENTICATION
