import asyncio
import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from performance_lab.domain import EndpointProfile, HardwareIdentity
from performance_lab.integrations import LocalLLMServerIdentityClient
from performance_lab.run_config import LocalLLMServerIdentityConfig, StarterRunConfig
from performance_lab.runner import RunExecutionError, execute_starter_run


class IdentityFixtureHandler(BaseHTTPRequestHandler):
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
            self._send_json(200, {"data": [{"id": "org/fake-model"}]})
            return
        if self.path == "/v1/runtime/identity":
            self._send_json(
                200,
                {
                    "protocol_version": "local-llm-identity-v1",
                    "server": {"name": "local-llm-server", "version": "0.3.8"},
                    "default_model": "fake-model",
                    "models": {
                        "fake-model": {
                            "model": {
                                "id": "org/fake-model",
                                "revision": "rev-42",
                                "artifact_digest": f"sha256:{'a' * 64}",
                                "artifact_key": "b" * 64,
                                "quantization": "Q4_K_M",
                                "verification": "verified",
                            },
                            "runtime": {
                                "name": "llama_cpp",
                                "version": "0.3.15",
                                "implementation": "LlamaCppEngine",
                                "config_digest": "c" * 64,
                                "config": {
                                    "backend": "llama_cpp",
                                    "ctx_size": 4096,
                                    "n_threads": 8,
                                },
                                "fingerprint": "d" * 64,
                                "captured_at": 1.0,
                                "evidence_grade": "verified",
                            },
                            "hardware": {
                                "system": "linux",
                                "machine": "x86_64",
                                "processor": "Example CPU",
                                "logical_cpus": 8,
                                "total_memory_bytes": 17179869184,
                                "accelerator": None,
                                "extra": {},
                            },
                        }
                    },
                },
            )
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        self._send_json(
            200,
            {
                "model": "org/fake-model",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "BLUE"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 3, "completion_tokens": 1},
            },
        )


@contextmanager
def identity_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), IdentityFixtureHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_identity_client_maps_server_contract_to_canonical_domain_identity() -> None:
    async def exercise(base_url: str):
        return await LocalLLMServerIdentityClient(base_url).resolve(model_id="fake-model")

    with identity_server() as base_url:
        identity = asyncio.run(exercise(base_url))

    assert identity.selected_runtime_key == "fake-model"
    assert identity.model.model_id == "org/fake-model"
    assert identity.model.revision == "rev-42"
    assert identity.model.artifact_digest == f"sha256:{'a' * 64}"
    assert identity.model.quantization == "Q4_K_M"
    assert identity.runtime.name == "llama_cpp"
    assert identity.runtime.version == "0.3.15"
    assert identity.runtime.config_digest == "c" * 64
    assert identity.hardware.device_class == "x86_64"
    assert identity.hardware.cpu == "Example CPU"
    assert identity.hardware.memory_bytes == 17179869184
    assert identity.hardware.os == "linux"


def test_starter_run_freezes_local_server_identity_into_fingerprint(tmp_path) -> None:
    with identity_server() as base_url:
        config = StarterRunConfig(
            target_id="identity-fixture",
            endpoint_identity="identity-fixture",
            endpoint=EndpointProfile(
                profile_id="fixture",
                base_url=f"{base_url}/v1/",
                model_selector="fake-model",
            ),
            model_id="fake-model",
            store_path=tmp_path / "runs.sqlite3",
            run_id="identity-run",
            local_llm_server_identity=LocalLLMServerIdentityConfig(
                base_url=base_url,
                model_id="fake-model",
                required=True,
            ),
        )
        result = asyncio.run(execute_starter_run(config))

    fingerprint = result.run.fingerprint
    assert fingerprint.model.model_id == "org/fake-model"
    assert fingerprint.model.revision == "rev-42"
    assert fingerprint.model.quantization == "Q4_K_M"
    assert fingerprint.runtime.name == "llama_cpp"
    assert fingerprint.runtime.version == "0.3.15"
    assert fingerprint.runtime.config_digest == "c" * 64
    assert fingerprint.hardware.device_class == "x86_64"
    assert fingerprint.hardware.memory_bytes == 17179869184
    assert result.bundle_path.exists()


def test_required_identity_rejects_hardware_conflict(tmp_path) -> None:
    with identity_server() as base_url:
        config = StarterRunConfig(
            target_id="identity-conflict",
            endpoint_identity="identity-fixture",
            endpoint=EndpointProfile(
                profile_id="fixture",
                base_url=f"{base_url}/v1/",
                model_selector="fake-model",
            ),
            model_id="fake-model",
            store_path=tmp_path / "runs.sqlite3",
            local_llm_server_identity=LocalLLMServerIdentityConfig(
                base_url=base_url,
                required=True,
            ),
            hardware=HardwareIdentity(os="darwin"),
        )
        with pytest.raises(RunExecutionError, match="hardware conflicts"):
            asyncio.run(execute_starter_run(config))
