from typing import Any, Awaitable, Callable, Optional, TypeAlias

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
        self._message_handlers: list[MessageHandler] = []
        self._startup_handlers: list[Callable[[], Awaitable[None]]] = []

    def on_message(
        self, **filters: Optional[Any]
    ) -> Callable[[HandlerFunc], HandlerFunc]:
        """
        Register a new message handler with optional filters.

        Args:
            **filters: Keyword arguments used to filter incoming message events.

        Returns:
            A decorator that registers the handler function.
        """

        def decorator(func: HandlerFunc) -> HandlerFunc:
            handler = MessageHandler(func, filters)
            self._message_handlers.append(handler)
            return func

        return decorator

    def on_startup(self):
        """
        Register a startup handler function.

        This method returns a decorator that registers a given function to be executed
        during the startup phase of the application. The function should be asynchronous
        and take no arguments.

        Returns:
            A decorator that registers the function as a startup handler.
        """

        def decorator(func: Callable[[], Awaitable[None]]):
            if func not in self._startup_handlers:
                self._startup_handlers.append(func)
            return func

        return decorator

    def get_handlers(self) -> list[MessageHandler]:
        """
        Get all registered message handlers.

        Returns:
            A list of `MessageHandler` instances.
        """
        return self._message_handlers

    def get_startup_handlers(self) -> list[Callable[[], Awaitable[None]]]:
        """
        Get all registered startup handlers.

        Returns:
            A list of callable functions that will be executed during the startup
            phase of the application.
        """
        return self._startup_handlers

    def __repr__(self) -> str:
        return f"<Router handlers={len(self._message_handlers)}>"
