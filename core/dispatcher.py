from typing import Any, Awaitable, Callable

from core.context.message_context import MessageContext


class MessageHandler:
    def __init__(
        self,
        func: Callable[[MessageContext], Awaitable[None]],
        filters: dict[str, Any],
    ):
        self.func = func
        self.filters = filters

    def matches(self, ctx: MessageContext) -> bool:
        """
        Checks if the given `MessageContext` matches the filter criteria.

        Args:
            ctx: The `MessageContext` instance containing the event to be checked.

        Returns:
            A boolean indicating whether the event in the context matches
            all the filter criteria specified in the handler.
        """

        for key, value in self.filters.items():
            attr = getattr(ctx.event, key, None)
            if attr != value:
                return False
        return True

    async def __call__(self, ctx: MessageContext):
        await self.func(ctx)
