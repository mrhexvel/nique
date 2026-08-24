from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from nique.features.routing.context import MessageContext


class Filter(ABC):
    @abstractmethod
    async def check(self, context: MessageContext) -> bool: ...

    def __and__(self, other: Filter) -> Filter:
        return _And(self, other)

    def __or__(self, other: Filter) -> Filter:
        return _Or(self, other)

    def __invert__(self) -> Filter:
        return _Not(self)


@dataclass(frozen=True, slots=True)
class Text(Filter):
    value: str
    ignore_case: bool = False

    async def check(self, context: MessageContext) -> bool:
        actual = context.event.message.text
        if self.ignore_case:
            return actual.casefold() == self.value.casefold()
        return actual == self.value


@dataclass(frozen=True, slots=True)
class Command(Filter):
    command: str
    prefixes: tuple[str, ...] = ("/", "!")

    async def check(self, context: MessageContext) -> bool:
        first = context.event.message.text.strip().split(maxsplit=1)[0]
        return any(
            first.casefold() == f"{prefix}{self.command}".casefold() for prefix in self.prefixes
        )


@dataclass(frozen=True, slots=True)
class FromUser(Filter):
    user_id: int | None = None

    async def check(self, context: MessageContext) -> bool:
        sender = context.event.message.from_id
        return sender > 0 and (self.user_id is None or sender == self.user_id)


@dataclass(frozen=True, slots=True)
class _Binary(Filter):
    left: Filter
    right: Filter


class _And(_Binary):
    async def check(self, context: MessageContext) -> bool:
        return await self.left.check(context) and await self.right.check(context)


class _Or(_Binary):
    async def check(self, context: MessageContext) -> bool:
        return await self.left.check(context) or await self.right.check(context)


@dataclass(frozen=True, slots=True)
class _Not(Filter):
    value: Filter

    async def check(self, context: MessageContext) -> bool:
        return not await self.value.check(context)
