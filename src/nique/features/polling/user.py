from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

from nique.api.client import VKApiClient
from nique.entities.events import NormalizedEvent
from nique.features.polling.adapters import adapt_user_event
from nique.shared.exceptions import TransportProtocolError
from nique.shared.http.contracts import HttpTransport


class UserLongPollEventSource:
    """User Long Poll loop with state isolated to one account."""

    def __init__(
        self, api: VKApiClient, transport: HttpTransport, *, wait: int = 25, version: int = 3
    ) -> None:
        self._api = api
        self._transport = transport
        self._wait = wait
        self._version = version

    async def listen(self) -> AsyncIterator[NormalizedEvent]:
        state = await self._api.messages.get_long_poll_server(
            need_pts=True, lp_version=self._version
        )
        while True:
            response = await self._transport.request(
                "GET",
                state.server,
                params={
                    "act": "a_check",
                    "key": state.key,
                    "ts": state.ts,
                    "wait": self._wait,
                    "mode": 2,
                    "version": self._version,
                },
                timeout=float(self._wait + 5),
            )
            payload = response.json()
            if not isinstance(payload, dict):
                raise TransportProtocolError("User Long Poll response must be an object")
            data = cast("dict[str, object]", payload)
            if data.get("failed") in {2, 3, 4}:
                state = await self._api.messages.get_long_poll_server(
                    need_pts=True, lp_version=self._version
                )
                continue
            ts = data.get("ts")
            if isinstance(ts, int):
                state.ts = ts
            updates = data.get("updates", [])
            if not isinstance(updates, list):
                raise TransportProtocolError("User Long Poll updates must be a list")
            for raw in cast("list[object]", updates):
                event = adapt_user_event(raw)
                if event is not None:
                    yield event
