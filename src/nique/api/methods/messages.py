from __future__ import annotations

from pydantic import Field

from nique.api.executor import VKApiExecutor
from nique.api.objects.messages import Message
from nique.api.serialization import VKRequestSerializer
from nique.shared.models import VKRequestModel, VKResponseModel


class MessagesSendRequest(VKRequestModel):
    peer_id: int
    message: str | None = None
    random_id: int = 0
    reply_to: int | None = None
    attachment: list[str] | None = None


class MessagesGetByIdResponse(VKResponseModel):
    count: int
    items: list[Message] = Field(default_factory=list[Message])


class MessagesLongPollServer(VKResponseModel):
    key: str
    server: str
    ts: int
    pts: int | None = None


class MessagesMethods:
    def __init__(self, executor: VKApiExecutor, serializer: VKRequestSerializer) -> None:
        self._executor = executor
        self._serializer = serializer

    async def send(
        self,
        *,
        peer_id: int,
        message: str | None = None,
        random_id: int = 0,
        reply_to: int | None = None,
        attachment: list[str] | None = None,
    ) -> int:
        request = MessagesSendRequest(
            peer_id=peer_id,
            message=message,
            random_id=random_id,
            reply_to=reply_to,
            attachment=attachment,
        )
        return await self._executor.call("messages.send", self._serializer.serialize(request), int)

    async def get_by_id(self, *, message_ids: list[int]) -> MessagesGetByIdResponse:
        return await self._executor.call(
            "messages.getById",
            self._serializer.serialize(message_ids=message_ids),
            MessagesGetByIdResponse,
        )

    async def get_long_poll_server(
        self, *, need_pts: bool = False, lp_version: int = 3
    ) -> MessagesLongPollServer:
        return await self._executor.call(
            "messages.getLongPollServer",
            self._serializer.serialize(need_pts=need_pts, lp_version=lp_version),
            MessagesLongPollServer,
        )
