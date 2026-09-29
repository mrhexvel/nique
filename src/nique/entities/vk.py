from __future__ import annotations

from pydantic import Field

from nique.shared.models import VKObjectModel


class Message(VKObjectModel):
    id: int
    date: int
    peer_id: int
    from_id: int
    text: str = ""
    random_id: int = 0
    attachments: list[dict[str, object]] = Field(default_factory=list[dict[str, object]])
