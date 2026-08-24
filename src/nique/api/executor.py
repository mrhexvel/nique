from __future__ import annotations

from typing import cast

from pydantic import TypeAdapter

from nique.api.errors import (
    VKApiError,
    VKAuthorizationError,
    VKErrorPayload,
    VKRateLimitError,
)
from nique.api.serialization import VKRequestSerializer
from nique.entities.tokens import AccessToken
from nique.shared.exceptions import TransportProtocolError
from nique.shared.http.contracts import HttpTransport


class VKApiExecutor:
    """Executes VK methods and validates their response envelopes."""

    def __init__(
        self,
        transport: HttpTransport,
        token: AccessToken,
        *,
        api_version: str,
        timeout: float,
        serializer: VKRequestSerializer | None = None,
        api_url: str = "https://api.vk.ru/method",
    ) -> None:
        self._transport = transport
        self._token = token
        self._api_version = api_version
        self._timeout = timeout
        self._serializer = serializer or VKRequestSerializer()
        self._api_url = api_url.rstrip("/")

    async def call[T](
        self,
        method: str,
        params: dict[str, object],
        response_type: type[T] | TypeAdapter[T],
    ) -> T:
        body = self._serializer.serialize(
            **params,
            access_token=self._token.value.get_secret_value(),
            v=self._api_version,
        )
        response = await self._transport.request(
            "POST", f"{self._api_url}/{method}", data=body, timeout=self._timeout
        )
        payload = response.json()
        if not isinstance(payload, dict):
            raise TransportProtocolError("VK response envelope must be an object")
        envelope = cast("dict[str, object]", payload)
        error_data = envelope.get("error")
        if error_data is not None:
            error = VKErrorPayload.model_validate(error_data)
            exception_type = self._error_type(error.error_code)
            raise exception_type(error)
        if "response" not in envelope:
            raise TransportProtocolError("VK response envelope has no response field")
        adapter = (
            response_type if isinstance(response_type, TypeAdapter) else TypeAdapter(response_type)
        )
        return adapter.validate_python(envelope["response"])

    @staticmethod
    def _error_type(error_code: int) -> type[VKApiError]:
        if error_code == 6:
            return VKRateLimitError
        if error_code in {5, 27, 28}:
            return VKAuthorizationError
        return VKApiError
