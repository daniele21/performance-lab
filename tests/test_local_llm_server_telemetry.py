import asyncio
import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread

from performance_lab.domain import (
    EndpointProfile,
    MeasurementProvenance,
    TelemetryLevel,
)
from performance_lab.run_config import LocalLLMServerTelemetryConfig, StarterRunConfig
from performance_lab.runner import execute_starter_run
from performance_lab.telemetry import LocalLLMServerStatusCollector, TelemetrySession


class LocalLLMServerFixtureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    _status_counter = 0
    _lock = Lock()

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def _send_json(self, payload: object) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/status":
            with self._lock:
                type(self)._status_counter += 1
                active = type(self)._status_counter % 2 == 0
            self._send_json(
                {
                    "default_model": "fake-model",
                    "models": {
                        "fake-model": {
                            "active": active,
                            "active_requests": 1 if active else 0,
                            "max_concurrent_requests": 4,
                            "phase": "generating" if active else "idle",
                            "output_chunks": 3 if active else 0,
                            "output_characters": 12 if active else 0,
                            "chunks_per_second": 12.5 if active else 0.0,
                        }
                    },
                }
            )
            return
        if self.path == "/v1/models":
            self._send_json({"data": [{"id": "fake-model"}]})
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        if self.path == "/v1/chat/completions":
            self._send_json(
                {
                    "model": "fake-model",
                    "choices": [
                        {
                            "message": {"role": "assistant", "content": "BLUE"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 1},
                }
            )
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()


@contextmanager
def local_llm_server_fixture() -> Iterator[str]:
    LocalLLMServerFixtureHandler._status_counter = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalLLMServerFixtureHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_status_collector_preserves_runtime_metric_semantics() -> None:
    async def exercise(base_url: str):
        collector = LocalLLMServerStatusCollector(
            base_url,
            model_id="fake-model",
            sample_interval_seconds=0.005,
        )
        session = TelemetrySession([collector])
        await session.start("run-1")
        await asyncio.sleep(0.025)
        result = await session.stop()
        return collector, result

    with local_llm_server_fixture() as base_url:
        collector, result = asyncio.run(exercise(base_url))

    assert collector.selected_model_id == "fake-model"
    assert result.measurements
    by_name = {measurement.name: measurement for measurement in result.measurements}
    assert by_name["status_sample_count"].value >= 2
    assert by_name["peak_active_requests"].value == 1
    assert by_name["peak_chunks_per_second"].value == 12.5
    assert by_name["max_concurrent_requests_reported"].value == 4
    assert all(
        measurement.provenance == MeasurementProvenance.RUNTIME
        for measurement in result.measurements
    )
    assert "tokens_per_second" not in by_name


def test_starter_run_can_collect_local_llm_server_status_evidence(tmp_path) -> None:
    with local_llm_server_fixture() as base_url:
        config = StarterRunConfig(
            target_id="local-llm-server-fixture",
            endpoint_identity="fixture",
            endpoint=EndpointProfile(
                profile_id="fixture",
                base_url=f"{base_url}/v1/",
                model_selector="fake-model",
            ),
            model_id="fake-model",
            store_path=tmp_path / "runs.sqlite3",
            run_id="runtime-telemetry-run",
            local_llm_server_telemetry=LocalLLMServerTelemetryConfig(
                base_url=base_url,
                model_id="fake-model",
                sample_interval_seconds=0.005,
            ),
        )
        result = asyncio.run(execute_starter_run(config))

    assert result.run.status.value == "succeeded"
    assert result.run.fingerprint.telemetry.level == TelemetryLevel.INSTRUMENTED
    assert result.run.fingerprint.telemetry.collectors == ("local-llm-server-status",)
    runtime_measurements = tuple(
        measurement
        for measurement in result.run.aggregate_measurements
        if measurement.provenance == MeasurementProvenance.RUNTIME
    )
    assert runtime_measurements
    assert {measurement.name for measurement in runtime_measurements} >= {
        "status_sample_count",
        "peak_active_requests",
        "peak_chunks_per_second",
    }
    assert result.bundle_path.exists()
