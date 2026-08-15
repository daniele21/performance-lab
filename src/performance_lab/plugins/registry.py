"""Small explicit registry for replaceable Performance Lab plugins."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from .contracts import PluginKind


class PluginRegistryError(LookupError):
    """Base registry error."""


class DuplicatePluginError(PluginRegistryError):
    pass


class PluginNotFoundError(PluginRegistryError):
    pass


@dataclass(slots=True)
class PluginRegistry:
    """In-memory registry with deterministic names and no import-time discovery."""

    _plugins: dict[tuple[PluginKind, str], object] = field(default_factory=dict)

    def register(self, kind: PluginKind, plugin_id: str, plugin: object) -> None:
        if not plugin_id:
            raise ValueError("plugin_id cannot be empty")
        key = (kind, plugin_id)
        if key in self._plugins:
            raise DuplicatePluginError(f"plugin already registered: {kind.value}:{plugin_id}")
        self._plugins[key] = plugin

    def get(self, kind: PluginKind, plugin_id: str) -> object | None:
        return self._plugins.get((kind, plugin_id))

    def require(self, kind: PluginKind, plugin_id: str) -> object:
        plugin = self.get(kind, plugin_id)
        if plugin is None:
            raise PluginNotFoundError(f"plugin not found: {kind.value}:{plugin_id}")
        return plugin

    def ids(self, kind: PluginKind) -> tuple[str, ...]:
        return tuple(sorted(plugin_id for plugin_kind, plugin_id in self._plugins if plugin_kind == kind))

    def items(self) -> Iterator[tuple[PluginKind, str, object]]:
        for (kind, plugin_id), plugin in sorted(
            self._plugins.items(), key=lambda item: (item[0][0].value, item[0][1])
        ):
            yield kind, plugin_id, plugin
