from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from nique.entities.events import NormalizedEvent


class EventSource(Protocol):
    async def listen(self) -> AsyncIterator[NormalizedEvent]: ...
