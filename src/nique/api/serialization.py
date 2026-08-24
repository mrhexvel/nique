from __future__ import annotations

from collections.abc import Iterable
from enum import Enum, IntFlag
from typing import cast

from pydantic import BaseModel


class VKRequestSerializer:
    """Converts typed request models into VK form parameters."""

    def serialize(self, request: BaseModel | None = None, /, **params: object) -> dict[str, object]:
        source = (
            cast("dict[str, object]", request.model_dump(by_alias=True, exclude_none=True))
            if request
            else params
        )
        return {key: self._value(value) for key, value in source.items() if value is not None}

    def _value(self, value: object) -> object:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, IntFlag):
            return int(value)
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, BaseModel):
            nested = cast("dict[str, object]", value.model_dump(by_alias=True, exclude_none=True))
            return {key: self._value(item) for key, item in nested.items()}
        if isinstance(value, (list, tuple, set)):
            items = cast("Iterable[object]", value)
            return ",".join(str(self._value(item)) for item in items)
        return value
