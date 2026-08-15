import asyncio
import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from performance_lab.domain import MeasurementProvenance
from performance_lab.telemetry import (
    InstrumentedEndpointCollector,
    TelemetryAvailability,
    TelemetrySession,
)


class RuntimeTelemetryHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def _send_json(self, payload: object) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        run_id = payload["run_id"]
        if self.path == "/telemetry/start":
            self._send_json(
                {
                    "protocol_version": "runtime-telemetry-v1",
                    "run_id": run_id,
                    "metric_names": ["peak_vram_bytes", "decode_tokens_per_second"],
                    "identity": {
                        "runtime": {"name": "local-runtime", "version": "1.2.3"},
                        "model": {"model_id": "model-a", "quantization": "Q4"},
                        "hardware": {"device_id": "gpu-0", "accelerator": "test-gpu"},
                    },
                }
            )
            return
        if self.path == "/telemetry/stop":
            self._send_json(
                {
                    "protocol_version": "runtime-telemetry-v1",
                    "run_id": run_id,
                    "measurements": [
                        {
                            "name": "peak_vram_bytes",
                            "value": 1024,
                            "unit": "bytes",
                            "scope": "run",
                        },
                        {
                            "name": "decode_tokens_per_second",
                            "value": 42.5,
                            "unit": "tokens/s",
                            "scope": "run",
                        },
                    ],
                }
            )
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()


@contextmanager
def telemetry_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeTelemetryHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_instrumented_collector_preserves_runtime_provenance_and_identity() -> None:
    async def exercise(base_url: str) -> tuple[InstrumentedEndpointCollector, object]:
        collector = InstrumentedEndpointCollector(base_url)
        session = TelemetrySession([collector])
        await session.start("run-1")
        return collector, await session.stop()

    with telemetry_server() as base_url:
        collector, result = asyncio.run(exercise(base_url))

    assert collector.identity.runtime.name == "local-runtime"
    assert collector.identity.model is not None
    assert collector.identity.model.quantization == "Q4"
    assert collector.capabilities().metric_names == frozenset(
        {"peak_vram_bytes", "decode_tokens_per_second"}
    )
    assert result.outcomes[0].availability == TelemetryAvailability.AVAILABLE
    assert len(result.measurements) == 2
    assert all(
        measurement.provenance == MeasurementProvenance.RUNTIME
        for measurement in result.measurements
    )


def test_protocol_mismatch_is_isolated_by_telemetry_session() -> None:
    class WrongProtocolHandler(RuntimeTelemetryHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            self._send_json(
                {
                    "protocol_version": "unsupported-v9",
                    "run_id": payload["run_id"],
                }
            )

    server = ThreadingHTTPServer(("127.0.0.1", 0), WrongProtocolHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        async def exercise() -> object:
            session = TelemetrySession([InstrumentedEndpointCollector(f"http://{host}:{port}")])
            await session.start("run-2")
            return await session.stop()

        result = asyncio.run(exercise())
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.outcomes[0].availability == TelemetryAvailability.ERROR
    assert result.measurements == ()
