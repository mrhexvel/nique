from typing import Awaitable, Callable

from core.dispatcher import MessageContext, MessageHandler

# TODO: implement router and middleware classes for decorators
_handlers: list[MessageHandler] = []


def on_message(**filters):
    """
    A decorator for registering a function as a message handler with optional filters.

    Args:
        filters: Arbitrary keyword arguments representing filter criteria
                   for message events. These filters are used to match the
                   attributes of a `MessageContext`.

    Returns:
        A decorator function that registers the provided function as a
        MessageHandler with the specified filters.
    """

    def decorator(func: Callable[[MessageContext], Awaitable[None]]):
        """A decorator for registering a function as a message handler with optional filters.

        Args:
            func: The function to register as a message handler.

        Returns:
            The original function, but now registered as a message handler.
        """

        handler = MessageHandler(func, filters)
        _handlers.append(handler)
        return func

    return decorator


def get_message_handlers() -> list[MessageHandler]:
    """
    Returns a list of all registered message handlers.

    Returns:
        A list of `MessageHandler` instances, each representing a registered
        message handler function with its associated filter criteria.
    """

    return _handlers
