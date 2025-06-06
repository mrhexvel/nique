from typing import Any, Awaitable, Callable, TypeAlias

from core.context.event_context import EventContext
from core.dispatcher import MessageHandler

HandlerFunc: TypeAlias = Callable[[EventContext], Awaitable[None]]


class Router:
    """
    A class to register and manage message event handlers with optional filters.

    Example usage:
    ```
    router = Router()

    @router.on_message(text="hello")
    async def greet(ctx: MessageContext):
        await ctx.answer("zdarova.")
    ```
    """

    def __init__(self) -> None:
        self._handlers: list[MessageHandler] = []

    def on_message(self, **filters: Any) -> Callable[[HandlerFunc], HandlerFunc]:
        """
        Register a new message handler with optional filters.

        Args:
            **filters: Keyword arguments used to filter incoming message events.

        Returns:
            A decorator that registers the handler function.
        """

        def decorator(func: HandlerFunc) -> HandlerFunc:
            handler = MessageHandler(func, filters)
            self._handlers.append(handler)
            return func

        return decorator

    def get_handlers(self) -> list[MessageHandler]:
        """
        Get all registered message handlers.

        Returns:
            A list of `MessageHandler` instances.
        """
        return self._handlers

    def __repr__(self) -> str:
        return f"<Router handlers={len(self._handlers)}>"
