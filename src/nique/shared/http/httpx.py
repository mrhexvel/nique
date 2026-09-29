from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from nique.shared.exceptions import (
    TransportConnectionError,
    TransportError,
    TransportTimeoutError,
)
from nique.shared.http.response import HttpResponse

if TYPE_CHECKING:
    import httpx


class HttpxTransport:
    """Optional HTTPX transport; importing NiQue does not require HTTPX."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        owns_client: bool | None = None,
    ) -> None:
        try:
            import httpx
        except ImportError as error:
            raise ImportError("HttpxTransport requires nique[httpx]") from error

        self._httpx = httpx
        self._client = client or httpx.AsyncClient()
        self._owns_client = client is None if owns_client is None else owns_client
        self._closed = False

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
        data: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        try:
            response = await self._client.request(
                method,
                url,
                params=cast("Any", params),
                data=cast("Any", data),
                headers=headers,
                timeout=timeout,
            )
        except self._httpx.TimeoutException as error:
            raise TransportTimeoutError("HTTP request timed out") from error
        except self._httpx.ConnectError as error:
            raise TransportConnectionError("HTTP connection failed") from error
        except self._httpx.HTTPError as error:
            raise TransportError("HTTP request failed") from error
        return HttpResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=str(response.url),
        )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_client:
            await self._client.aclose()
