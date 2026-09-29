from __future__ import annotations

from pydantic import TypeAdapter

from nique.api.executor import VKApiExecutor


class RawMethods:
    """Escape hatch for VK methods without a typed wrapper."""

    def __init__(self, executor: VKApiExecutor) -> None:
        self._executor = executor
        self._adapter = TypeAdapter(object)

    async def call(self, method: str, *, params: dict[str, object] | None = None) -> object:
        return await self._executor.call(method, params or {}, self._adapter)
