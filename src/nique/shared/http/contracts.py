from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from nique.shared.http.response import HttpResponse


class HttpTransport(Protocol):
    """Minimal asynchronous HTTP boundary used by NiQue."""

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
        data: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse: ...

    async def aclose(self) -> None: ...


class HttpSessionFactory(Protocol):
    """Creates independently owned transports, primarily for cookie-isolated auth."""

    def create(self) -> HttpTransport: ...
