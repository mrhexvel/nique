from __future__ import annotations

from pydantic import SecretStr

from nique.api.client import VKApiClient
from nique.api.executor import VKApiExecutor
from nique.api.objects.messages import Message
from nique.entities.events import MessageNew
from nique.entities.tokens import AccessToken
from nique.features.routing.context import EventAccount, EventAccountId, MessageContext
from nique.features.routing.dispatcher import Dispatcher
from nique.features.routing.filters import Command, FromUser, Text
from nique.features.routing.middleware import NextHandler
from nique.features.routing.router import Router
from nique.shared.http.fake import FakeTransport


async def test_filters_and_onion_middleware() -> None:
    calls: list[str] = []
    router = Router()

    async def middleware(context: MessageContext, next_handler: NextHandler) -> None:
        calls.append("before")
        await next_handler(context)
        calls.append("after")

    router.use(middleware)

    @router.message(Command("ping") & FromUser())
    async def ping(_context: MessageContext) -> None:
        calls.append("handler")

    _ = ping
    api = VKApiClient(
        VKApiExecutor(
            FakeTransport(),
            AccessToken(value=SecretStr("token")),
            api_version="5.199",
            timeout=1,
        )
    )
    context = MessageContext(
        event=MessageNew(message=Message(id=1, date=1, peer_id=1, from_id=1, text="/ping")),
        account=EventAccount(EventAccountId("id"), "main"),
        api=api,
    )

    assert await (Text("/ping") | Text("hello")).check(context)
    assert await (~Text("hello")).check(context)
    await Dispatcher().dispatch(context, [router])
    assert calls == ["before", "handler", "after"]
