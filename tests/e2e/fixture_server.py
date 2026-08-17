from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

GOOD_MODEL = "fixture-good"
BAD_MODEL = "fixture-bad"
CONFIG_DIGEST = "c" * 64
RUNTIME_FINGERPRINT = "d" * 64

_GOOD_ANSWERS: dict[str, str] = {
    "Reply with exactly: BLUE": "BLUE",
    "Reply with exactly: seven": "seven",
    "Reply with exactly: LOCAL": "LOCAL",
    "What is the capital of France? Answer with the city only.": "Paris",
    "What is the chemical formula of water? Answer only the formula.": "H2O",
    "Which planet is the largest in the Solar System? Name only.": "Jupiter",
    "All lorps are mivs. Every miv is a zan. Is every lorp a zan? Answer yes or no.": "yes",
    "No red object is blue. This object is red. Can it also be blue? Answer yes or no.": "no",
    "Ana is older than Bea. Bea is older than Cy. Is Ana older than Cy? Answer yes or no.": "yes",
    "Compute 8 + 9. Answer only the number.": "17",
    "Compute 6 * 7. Answer only the number.": "42",
    "Compute 1 / 4 as a decimal. Answer only the number.": "0.25",
    "A dozen contains how many items? Answer only the number.": "12",
    "Classify sentiment as positive or negative: 'The update works perfectly.'": "positive",
    "Classify sentiment as positive or negative: 'The app crashes every time.'": "negative",
    "Classify intent as question or command: 'Close the window.'": "command",
    "Classify intent as question or command: 'Where is the station?'": "question",
    'Return JSON only with name and count: name is "Ada", count is 2.': '{"name":"Ada","count":2}',
    'Return JSON only with name and count: name is "Lin", count is 5.': '{"name":"Lin","count":5}',
    'Return JSON only with name and count: name is "Kai", count is 1.': '{"name":"Kai","count":1}',
}


def _identity_entry(model_id: str) -> dict[str, Any]:
    return {
        "model": {
            "id": model_id,
            "revision": "e2e-revision",
            "artifact_digest": f"sha256:{model_id}",
            "artifact_key": f"e2e:{model_id}",
            "quantization": "fixture",
            "verification": "verified",
        },
        "runtime": {
            "name": "fixture-runtime",
            "version": "1.0.0",
            "implementation": "performance-lab-e2e",
            "config_digest": CONFIG_DIGEST,
            "config": {"concurrency": 1, "fixture": True},
            "fingerprint": RUNTIME_FINGERPRINT,
            "captured_at": 1.0,
            "evidence_grade": "verified",
        },
        "hardware": {
            "system": "linux",
            "machine": "x86_64",
            "processor": "fixture-cpu",
            "logical_cpus": 4,
            "total_memory_bytes": 8 * 1024 * 1024 * 1024,
            "accelerator": None,
            "extra": {"fixture": True},
        },
    }


def _status_entry() -> dict[str, Any]:
    return {
        "active": False,
        "active_requests": 0,
        "max_concurrent_requests": 1,
        "phase": "idle",
        "output_chunks": 0,
        "output_characters": 0,
        "chunks_per_second": 0.0,
    }


def _last_user_message(payload: dict[str, Any]) -> str:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return ""
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str):
                return content
    return ""


def _completion_text(payload: dict[str, Any]) -> str:
    model = payload.get("model")
    prompt = _last_user_message(payload)
    if model == GOOD_MODEL:
        return _GOOD_ANSWERS.get(prompt, "UNKNOWN")
    if model == BAD_MODEL:
        return "WRONG"
    return "UNKNOWN_MODEL"


class FixtureHandler(BaseHTTPRequestHandler):
    identity_mode = "ok"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return None

    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._json(
                HTTPStatus.OK,
                {
                    "object": "list",
                    "data": [
                        {"id": GOOD_MODEL, "object": "model"},
                        {"id": BAD_MODEL, "object": "model"},
                    ],
                },
            )
            return
        if self.path == "/v1/runtime/identity":
            if self.identity_mode == "unavailable":
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"detail": "identity unavailable"})
                return
            self._json(
                HTTPStatus.OK,
                {
                    "protocol_version": "local-llm-identity-v1",
                    "server": {"name": "fixture-local-llm-server", "version": "1.0.0"},
                    "default_model": GOOD_MODEL,
                    "models": {
                        GOOD_MODEL: _identity_entry(GOOD_MODEL),
                        BAD_MODEL: _identity_entry(BAD_MODEL),
                    },
                },
            )
            return
        if self.path == "/status":
            self._json(
                HTTPStatus.OK,
                {
                    **_status_entry(),
                    "default_model": GOOD_MODEL,
                    "models": {
                        GOOD_MODEL: _status_entry(),
                        BAD_MODEL: _status_entry(),
                    },
                },
            )
            return
        self._json(HTTPStatus.NOT_FOUND, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._json(HTTPStatus.NOT_FOUND, {"detail": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._json(HTTPStatus.BAD_REQUEST, {"detail": "invalid JSON"})
            return
        if not isinstance(payload, dict):
            self._json(HTTPStatus.BAD_REQUEST, {"detail": "payload must be an object"})
            return

        model = payload.get("model")
        text = _completion_text(payload)
        if payload.get("stream") is True:
            event = {
                "id": "chatcmpl-e2e",
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 4, "completion_tokens": 2},
            }
            body = (f"data: {json.dumps(event, separators=(',', ':'))}\n\ndata: [DONE]\n\n").encode(
                "utf-8"
            )
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self._json(
            HTTPStatus.OK,
            {
                "id": "chatcmpl-e2e",
                "object": "chat.completion",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 4,
                    "completion_tokens": 2,
                    "total_tokens": 6,
                },
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument(
        "--identity-mode",
        choices=("ok", "unavailable"),
        default="ok",
    )
    args = parser.parse_args()
    FixtureHandler.identity_mode = args.identity_mode
    server = ThreadingHTTPServer(("127.0.0.1", args.port), FixtureHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
