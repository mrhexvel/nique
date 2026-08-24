from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from nique.shared.exceptions import TransportProtocolError


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """Backend-neutral buffered HTTP response."""

    status_code: int
    headers: Mapping[str, str]
    content: bytes
    url: str | None = None

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self) -> object:
        try:
            return json.loads(self.content)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise TransportProtocolError("Response body is not valid JSON") from error
