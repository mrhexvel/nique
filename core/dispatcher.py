from typing import Any, Awaitable, Callable

from client.base import BaseClient
from core.context.event_context import EventContext


class MessageHandler:
    def __init__(
        self,
        func: Callable[[EventContext], Awaitable[None]],
        filters: dict[str, Any],
    ):
        self.func = func
        self.filters = filters

    def matches(self, ctx: EventContext) -> bool:
        """
        Checks if the given `MessageContext` matches the filter criteria.

        Args:
            ctx: The `MessageContext` instance containing the event to be checked.

        Returns:
            A boolean indicating whether the event in the context matches
            all the filter criteria specified in the handler.
        """

        for key, value in self.filters.items():
            attr = getattr(ctx, key, None)
            if attr != value:
                return False
        return True

    async def __call__(self, ctx: EventContext):
        await self.func(ctx)


#  пока пусть будет здесь, потом разделю
async def dispatch_event(ctx: EventContext, client: BaseClient, routers):
    """
    Dispatches an event to the registered message handlers.

    :param ctx: An EventContext containing the event to be dispatched.
    :param client: The BaseClient instance used to access the VK API.
    :param routers: A list of Router instances containing the registered handlers.
    """
    await ctx.load_full_message()

    for router in routers:
        for handler in router.get_handlers():
            if handler.matches(ctx):
                await handler(ctx)
