from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from nique.features.routing.context import MessageContext

NextHandler = Callable[[MessageContext], Awaitable[None]]


class Middleware(Protocol):
    async def __call__(self, context: MessageContext, next_handler: NextHandler) -> None: ...
