import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from threading import Thread

from performance_lab.cli import main


class StarterRunHandler(BaseHTTPRequestHandler):
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

    def do_GET(self) -> None:
        self._send_json({"data": [{"id": "fake-model"}]})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
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


@contextmanager
def starter_run_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), StarterRunHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/v1/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_run_command_persists_completed_run_and_bundle(tmp_path) -> None:
    store_path = tmp_path / "runs.sqlite3"
    config_path = tmp_path / "run.json"

    with starter_run_server() as base_url:
        config_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "target_id": "local-test",
                    "endpoint_identity": "local-test-server",
                    "endpoint": {
                        "profile_id": "local-test",
                        "base_url": base_url,
                        "model_selector": "fake-model",
                    },
                    "model_id": "fake-model",
                    "store_path": str(store_path),
                    "run_id": "cli-run-test",
                }
            ),
            encoding="utf-8",
        )
        output = StringIO()
        exit_code = main(["run", "--config", str(config_path), "--json"], stdout=output)

    result = json.loads(output.getvalue())
    assert exit_code == 0
    assert result["run_id"] == "cli-run-test"
    assert result["status"] == "succeeded"
    assert result["sample_count"] > 0
    assert store_path.exists()
    assert (tmp_path / "artifacts" / "cli-run-test.plab.zip").exists()
