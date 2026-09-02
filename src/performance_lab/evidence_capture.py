"""Local evidence-rich adapter wrapper for prompt/model-output capture."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Protocol

from performance_lab.domain import SampleContentEvidence
from performance_lab.plugins import (
    InferenceAdapter,
    InferenceChunk,
    InferenceRequest,
    InferenceResponse,
    ProbeResult,
)


class EvidenceCaptureError(RuntimeError):
    """Raised when evidence-rich execution cannot retain the content it promised."""


class SampleContentSink(Protocol):
    def save_working_sample_content(self, evidence: SampleContentEvidence) -> None: ...

    def delete_working_sample_content(self, run_id: str) -> int: ...


class EvidenceCapturingAdapter:
    """Capture the exact rendered chat content around one delegated inference adapter.

    Content is written only to working local evidence. The run store atomically promotes those
    rows when the owning Run is published; a hard-interrupted run can discard the working rows.
    """

    def __init__(
        self,
        delegate: InferenceAdapter,
        sink: SampleContentSink,
        *,
        run_id: str,
    ) -> None:
        self._delegate = delegate
        self._sink = sink
        self._run_id = run_id
        self.adapter_id = delegate.adapter_id

    async def probe(self) -> ProbeResult:
        return await self._delegate.probe()

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        evidence = self._prompt_evidence(request)
        self._save(evidence)
        response = await self._delegate.generate(request)
        self._save(evidence.model_copy(update={"response": response.text}))
        return response

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        return self._stream(request)

    async def _stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        evidence = self._prompt_evidence(request)
        self._save(evidence)
        parts: list[str] = []
        async for chunk in self._delegate.stream(request):
            parts.append(chunk.text_delta)
            yield chunk
        self._save(evidence.model_copy(update={"response": "".join(parts)}))

    async def cancel(self, request_id: str) -> bool:
        return await self._delegate.cancel(request_id)

    def _prompt_evidence(self, request: InferenceRequest) -> SampleContentEvidence:
        task_id, sample_id = _sample_identity(self._run_id, request.request_id)
        return SampleContentEvidence(
            run_id=self._run_id,
            task_id=task_id,
            sample_id=sample_id,
            attempt=1,
            prompt=_render_prompt(request),
        )

    def _save(self, evidence: SampleContentEvidence) -> None:
        try:
            self._sink.save_working_sample_content(evidence)
        except Exception as exc:
            with suppress(Exception):
                self._sink.delete_working_sample_content(self._run_id)
            raise EvidenceCaptureError(
                "evidence-rich execution could not retain prompt/model-output content"
            ) from exc


def _sample_identity(run_id: str, request_id: str) -> tuple[str, str]:
    prefix = f"{run_id}:"
    if not request_id.startswith(prefix):
        raise EvidenceCaptureError("inference request identity does not belong to the active run")
    remainder = request_id[len(prefix) :]
    task_id, separator, sample_id = remainder.partition(":")
    if not separator or not task_id or not sample_id:
        raise EvidenceCaptureError("inference request identity is not sample-addressable")
    return task_id, sample_id


def _render_prompt(request: InferenceRequest) -> str:
    if len(request.messages) == 1:
        return request.messages[0].content
    return "\n\n".join(
        f"{message.role.value.upper()}:\n{message.content}" for message in request.messages
    )
