"""OpenAI-compatible reference transport adapter."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator, Mapping
from time import perf_counter_ns
from typing import cast

import httpx

from performance_lab.domain import AuthStrategy, EndpointProfile, GenerationConfig
from performance_lab.plugins import (
    AdapterCapabilities,
    InferenceAdapterError,
    InferenceChunk,
    InferenceErrorCode,
    InferenceRequest,
    InferenceResponse,
    ProbeResult,
    TokenUsage,
)

_SUPPORTED_GENERATION_PARAMETERS = frozenset(
    {"max_output_tokens", "temperature", "top_p", "seed", "stop", "response_format"}
)


class OpenAICompatibleAdapter:
    """Normalize OpenAI-compatible chat-completion endpoints into the lab contract."""

    adapter_id = "openai-compatible"

    def __init__(
        self,
        profile: EndpointProfile,
        *,
        model: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.profile = profile
        self.model = model or profile.model_selector
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=str(profile.base_url).rstrip("/"),
            timeout=profile.timeout_seconds,
            headers=self._auth_headers(),
        )
        self._active_tasks: dict[str, asyncio.Task[object]] = {}

    def _auth_headers(self) -> dict[str, str]:
        auth = self.profile.auth
        if auth.strategy == AuthStrategy.NONE:
            return {}
        assert auth.credential_env is not None
        credential = os.getenv(auth.credential_env)
        if not credential:
            raise InferenceAdapterError(
                InferenceErrorCode.AUTHENTICATION,
                f"credential environment variable is not set: {auth.credential_env}",
            )
        if auth.strategy == AuthStrategy.BEARER_ENV:
            return {"Authorization": f"Bearer {credential}"}
        if auth.strategy == AuthStrategy.API_KEY_ENV:
            return {"api-key": credential}
        assert auth.header_name is not None
        return {auth.header_name: credential}

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _register_current_task(self, request_id: str) -> None:
        task = asyncio.current_task()
        if task is not None:
            self._active_tasks[request_id] = cast(asyncio.Task[object], task)

    def _unregister_current_task(self, request_id: str) -> None:
        task = asyncio.current_task()
        registered = self._active_tasks.get(request_id)
        if registered is task:
            self._active_tasks.pop(request_id, None)

    async def cancel(self, request_id: str) -> bool:
        task = self._active_tasks.get(request_id)
        if task is None or task.done():
            return False
        task.cancel()
        return True

    async def probe(self) -> ProbeResult:
        try:
            response = await self._request("GET", "models")
            payload = self._object(response.json(), "models response")
            raw_models = payload.get("data", [])
            models: list[str] = []
            if isinstance(raw_models, list):
                for raw_model in raw_models:
                    if isinstance(raw_model, dict):
                        model_id = raw_model.get("id")
                        if isinstance(model_id, str):
                            models.append(model_id)
            return ProbeResult(
                healthy=True,
                adapter_id=self.adapter_id,
                models=tuple(models),
                capabilities=AdapterCapabilities(
                    streaming=True,
                    model_discovery=True,
                    token_usage=None,
                    seed=None,
                    structured_output=None,
                    supported_generation_parameters=_SUPPORTED_GENERATION_PARAMETERS,
                ),
            )
        except InferenceAdapterError as exc:
            return ProbeResult(
                healthy=False,
                adapter_id=self.adapter_id,
                capabilities=AdapterCapabilities(
                    supported_generation_parameters=_SUPPORTED_GENERATION_PARAMETERS
                ),
                metadata={"error_code": exc.code.value},
            )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        self._register_current_task(request.request_id)
        try:
            response = await self._request(
                "POST",
                "chat/completions",
                json_body=self._request_payload(request, stream=False),
            )
            return self._parse_response(request.request_id, response.json())
        except asyncio.CancelledError as exc:
            raise InferenceAdapterError(
                InferenceErrorCode.CANCELLED,
                f"request cancelled: {request.request_id}",
            ) from exc
        finally:
            self._unregister_current_task(request.request_id)

    async def _stream_impl(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        self._register_current_task(request.request_id)
        try:
            try:
                async with self._client.stream(
                    "POST",
                    "chat/completions",
                    json=self._request_payload(request, stream=True),
                ) as response:
                    self._raise_for_status(response)
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if not data or data == "[DONE]":
                            continue
                        try:
                            payload_raw: object = json.loads(data)
                        except json.JSONDecodeError as exc:
                            raise InferenceAdapterError(
                                InferenceErrorCode.PROTOCOL,
                                "stream contained invalid JSON",
                            ) from exc
                        yield self._parse_chunk(request.request_id, payload_raw)
            except httpx.TimeoutException as exc:
                raise self._transport_error(
                    InferenceErrorCode.TIMEOUT, exc, retryable=True
                ) from exc
            except httpx.TransportError as exc:
                raise self._transport_error(
                    InferenceErrorCode.CONNECTION, exc, retryable=True
                ) from exc
        except asyncio.CancelledError as exc:
            raise InferenceAdapterError(
                InferenceErrorCode.CANCELLED,
                f"request cancelled: {request.request_id}",
            ) from exc
        finally:
            self._unregister_current_task(request.request_id)

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        return self._stream_impl(request)

    def _request_payload(self, request: InferenceRequest, *, stream: bool) -> dict[str, object]:
        model = request.model or self.model
        if model is None:
            raise InferenceAdapterError(
                InferenceErrorCode.INVALID_REQUEST,
                "an explicit model is required for chat completions",
            )
        if not request.messages:
            raise InferenceAdapterError(
                InferenceErrorCode.INVALID_REQUEST,
                "at least one chat message is required",
            )
        payload: dict[str, object] = {
            "model": model,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
            "stream": stream,
        }
        self._apply_generation(payload, request.generation)
        if stream:
            payload["stream_options"] = {"include_usage": True}
        return payload

    @staticmethod
    def _apply_generation(payload: dict[str, object], generation: GenerationConfig) -> None:
        payload["max_tokens"] = generation.max_output_tokens
        if generation.temperature is not None:
            payload["temperature"] = generation.temperature
        if generation.top_p is not None:
            payload["top_p"] = generation.top_p
        if generation.seed is not None:
            payload["seed"] = generation.seed
        if generation.stop:
            payload["stop"] = list(generation.stop)
        if generation.response_format is not None:
            payload["response_format"] = {"type": generation.response_format}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Mapping[str, object] | None = None,
    ) -> httpx.Response:
        try:
            response = await self._client.request(method, path, json=json_body)
        except httpx.TimeoutException as exc:
            raise self._transport_error(InferenceErrorCode.TIMEOUT, exc, retryable=True) from exc
        except httpx.TransportError as exc:
            raise self._transport_error(InferenceErrorCode.CONNECTION, exc, retryable=True) from exc
        self._raise_for_status(response)
        return response

    @staticmethod
    def _transport_error(
        code: InferenceErrorCode,
        exc: Exception,
        *,
        retryable: bool,
    ) -> InferenceAdapterError:
        return InferenceAdapterError(code, str(exc) or code.value, retryable=retryable)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        if status < 400:
            return
        if status in {401, 403}:
            code = InferenceErrorCode.AUTHENTICATION
            retryable = False
        elif status == 429:
            code = InferenceErrorCode.RATE_LIMIT
            retryable = True
        elif status >= 500:
            code = InferenceErrorCode.SERVER
            retryable = True
        else:
            code = InferenceErrorCode.INVALID_REQUEST
            retryable = False
        raise InferenceAdapterError(
            code,
            f"endpoint returned HTTP {status}",
            retryable=retryable,
            status_code=status,
        )

    def _parse_response(self, request_id: str, raw: object) -> InferenceResponse:
        payload = self._object(raw, "chat completion response")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise InferenceAdapterError(
                InferenceErrorCode.PROTOCOL,
                "chat completion response has no choices",
            )
        choice = self._object(choices[0], "chat completion choice")
        message = self._object(choice.get("message"), "chat completion message")
        content = message.get("content")
        if not isinstance(content, str):
            raise InferenceAdapterError(
                InferenceErrorCode.PROTOCOL,
                "chat completion message content is not text",
            )
        model = payload.get("model")
        finish_reason = choice.get("finish_reason")
        return InferenceResponse(
            request_id=request_id,
            text=content,
            model=model if isinstance(model, str) else None,
            finish_reason=finish_reason if isinstance(finish_reason, str) else None,
            usage=self._parse_usage(payload.get("usage")),
        )

    def _parse_chunk(self, request_id: str, raw: object) -> InferenceChunk:
        payload = self._object(raw, "stream chunk")
        text_delta = ""
        finish_reason: str | None = None
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            choice = self._object(choices[0], "stream choice")
            delta = self._object(choice.get("delta", {}), "stream delta")
            content = delta.get("content")
            if isinstance(content, str):
                text_delta = content
            raw_finish = choice.get("finish_reason")
            if isinstance(raw_finish, str):
                finish_reason = raw_finish
        return InferenceChunk(
            request_id=request_id,
            text_delta=text_delta,
            emitted_at_ns=perf_counter_ns(),
            finish_reason=finish_reason,
            usage=self._parse_usage(payload.get("usage")),
        )

    @staticmethod
    def _parse_usage(raw: object) -> TokenUsage | None:
        if not isinstance(raw, dict):
            return None
        prompt_tokens = raw.get("prompt_tokens")
        completion_tokens = raw.get("completion_tokens")
        return TokenUsage(
            input_tokens=prompt_tokens if isinstance(prompt_tokens, int) else None,
            output_tokens=completion_tokens if isinstance(completion_tokens, int) else None,
        )

    @staticmethod
    def _object(raw: object, label: str) -> dict[str, object]:
        if not isinstance(raw, dict):
            raise InferenceAdapterError(
                InferenceErrorCode.PROTOCOL,
                f"{label} is not a JSON object",
            )
        return cast(dict[str, object], raw)
