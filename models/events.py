from typing import Any

from pydantic import BaseModel


class NormalizedMessageEvent(BaseModel):
    message_id: int
    peer_id: int
    text: str
    from_id: int
    is_group: bool
    raw: dict
    date: int
    out: int
    conversation_message_id: int
    random_id: int
    attachments: list[Any]
    fwd_messages: list[Any]
