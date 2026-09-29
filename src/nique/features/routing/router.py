from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from nique.features.routing.context import MessageContext
from nique.features.routing.filters import Filter
from nique.features.routing.middleware import Middleware

MessageHandler = Callable[[MessageContext], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class HandlerRegistration:
    callback: MessageHandler
    filters: tuple[Filter, ...]


class Router:
    """Explicit collection of handlers and router-scoped middleware."""

    def __init__(self) -> None:
        self.handlers: list[HandlerRegistration] = []
        self.middleware: list[Middleware] = []

    def message(self, *filters: Filter) -> Callable[[MessageHandler], MessageHandler]:
        def register(callback: MessageHandler) -> MessageHandler:
            self.handlers.append(HandlerRegistration(callback, filters))
            return callback

        return register

    def use(self, middleware: Middleware) -> None:
        self.middleware.append(middleware)
