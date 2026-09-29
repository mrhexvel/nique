from __future__ import annotations

from collections.abc import Sequence

from nique.features.routing.context import MessageContext
from nique.features.routing.middleware import Middleware, NextHandler
from nique.features.routing.router import HandlerRegistration, Router


class Dispatcher:
    """Matches normalized contexts to filters, middleware, and handlers."""

    def __init__(self, middleware: Sequence[Middleware] = ()) -> None:
        self._middleware = tuple(middleware)

    async def dispatch(self, context: MessageContext, routers: Sequence[Router]) -> None:
        for router in routers:
            for registration in router.handlers:
                if all([await item.check(context) for item in registration.filters]):
                    await self._invoke(
                        context,
                        registration,
                        (*self._middleware, *router.middleware),
                    )

    async def _invoke(
        self,
        context: MessageContext,
        registration: HandlerRegistration,
        middleware: Sequence[Middleware],
    ) -> None:
        async def handler(current: MessageContext) -> None:
            await registration.callback(current)

        chain: NextHandler = handler
        for item in reversed(middleware):
            next_handler = chain

            async def wrapped(
                current: MessageContext,
                current_middleware: Middleware = item,
                following: NextHandler = next_handler,
            ) -> None:
                await current_middleware(current, following)

            chain = wrapped
        await chain(context)
