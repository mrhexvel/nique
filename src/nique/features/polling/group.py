from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

from nique.api.client import VKApiClient
from nique.entities.events import NormalizedEvent
from nique.features.polling.adapters import adapt_group_event
from nique.shared.exceptions import TransportProtocolError
from nique.shared.http.contracts import HttpTransport


class GroupLongPollEventSource:
    """Group Long Poll loop with mutable state isolated to one account."""

    def __init__(
        self,
        api: VKApiClient,
        transport: HttpTransport,
        group_id: int,
        *,
        wait: int = 25,
    ) -> None:
        self._api = api
        self._transport = transport
        self._group_id = group_id
        self._wait = wait

    async def listen(self) -> AsyncIterator[NormalizedEvent]:
        state = await self._api.groups.get_long_poll_server(group_id=self._group_id)
        while True:
            response = await self._transport.request(
                "GET",
                state.server,
                params={"act": "a_check", "key": state.key, "ts": state.ts, "wait": self._wait},
                timeout=float(self._wait + 5),
            )
            payload = response.json()
            if not isinstance(payload, dict):
                raise TransportProtocolError("Group Long Poll response must be an object")
            data = cast("dict[str, object]", payload)
            failed = data.get("failed")
            if failed in {2, 3, 4}:
                state = await self._api.groups.get_long_poll_server(group_id=self._group_id)
                continue
            ts = data.get("ts")
            if isinstance(ts, (str, int)):
                state.ts = str(ts)
            updates = data.get("updates", [])
            if not isinstance(updates, list):
                raise TransportProtocolError("Group Long Poll updates must be a list")
            for raw in cast("list[object]", updates):
                event = adapt_group_event(raw)
                if event is not None:
                    yield event
