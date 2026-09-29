from __future__ import annotations

from dataclasses import dataclass, field
from typing import NewType

from nique.api.client import VKApiClient
from nique.entities.events import MessageNew

EventData = dict[str, object]
EventAccountId = NewType("EventAccountId", str)


@dataclass(frozen=True, slots=True)
class EventAccount:
    id: EventAccountId
    name: str


@dataclass(slots=True)
class MessageContext:
    """Account-bound behavior for a normalized message event."""

    event: MessageNew
    account: EventAccount
    api: VKApiClient
    data: EventData = field(default_factory=EventData)

    async def answer(
        self,
        message: str,
        *,
        random_id: int = 0,
        attachment: list[str] | None = None,
    ) -> int:
        return await self.api.messages.send(
            peer_id=self.event.message.peer_id,
            message=message,
            random_id=random_id,
            attachment=attachment,
        )

    async def reply(
        self,
        message: str,
        *,
        random_id: int = 0,
        attachment: list[str] | None = None,
    ) -> int:
        return await self.api.messages.send(
            peer_id=self.event.message.peer_id,
            message=message,
            reply_to=self.event.message.id,
            random_id=random_id,
            attachment=attachment,
        )
