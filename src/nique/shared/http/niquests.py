from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import niquests

from nique.shared.exceptions import (
    TransportConnectionError,
    TransportError,
    TransportTimeoutError,
)
from nique.shared.http.response import HttpResponse


class NiquestsTransport:
    """Niquests-backed transport with explicit session ownership."""

    def __init__(
        self,
        session: niquests.AsyncSession | None = None,
        *,
        owns_session: bool | None = None,
    ) -> None:
        self._session = session or niquests.AsyncSession()
        self._owns_session = session is None if owns_session is None else owns_session
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
            response = await self._session.request(
                method,
                url,
                params=cast("Any", params),
                data=cast("Any", data),
                headers=cast("Any", headers),
                timeout=timeout,
            )
        except niquests.exceptions.Timeout as error:
            raise TransportTimeoutError("HTTP request timed out") from error
        except niquests.exceptions.ConnectionError as error:
            raise TransportConnectionError("HTTP connection failed") from error
        except niquests.exceptions.RequestException as error:
            raise TransportError("HTTP request failed") from error

        status_code = response.status_code
        if status_code is None:
            raise TransportError("HTTP response has no status code")
        return HttpResponse(
            status_code=status_code,
            headers=dict(response.headers),
            content=response.content or b"",
            url=str(response.url),
        )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_session:
            await self._session.close()


class NiquestsSessionFactory:
    """Creates isolated, owned Niquests sessions."""

    def create(self) -> NiquestsTransport:
        return NiquestsTransport()
