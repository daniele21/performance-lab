"""Shared bounded admission control for local evaluation execution."""

from __future__ import annotations

import asyncio


class EvaluationCapacityError(RuntimeError):
    pass


class EvaluationCapacity:
    """Allow exactly one local evaluation owner without creating a wait queue."""

    def __init__(self) -> None:
        self._owner: str | None = None
        self._lock = asyncio.Lock()

    @property
    def owner(self) -> str | None:
        return self._owner

    async def acquire(self, owner: str) -> None:
        async with self._lock:
            if self._owner is not None and self._owner != owner:
                raise EvaluationCapacityError(f"evaluation capacity is owned by {self._owner}")
            self._owner = owner

    async def release(self, owner: str) -> None:
        async with self._lock:
            if self._owner == owner:
                self._owner = None
