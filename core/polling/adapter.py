from typing import Any, Optional, Union

from models.events import NormalizedMessageEvent

__all__ = ["normalize_event"]


def normalize_event(
    raw: Union[list[Any], dict[str, Any]], is_user: bool
) -> Optional[NormalizedMessageEvent]:
    """
    Normalize raw event data returned by VK Long Poll API into a
    `NormalizedMessageEvent` instance.

    :param raw: Raw event data returned by VK Long Poll API
    :param is_user: Whether the event is sent from a user or a group
    :return: Normalized event data as a `NormalizedMessageEvent` instance
    """
    message_id: Optional[int] = raw.get("id")
    peer_id: Optional[int] = raw.get("peer_id")
    text: Optional[str] = raw.get("text", "")
    from_id: Optional[int] = raw.get("from_id")
    date: Optional[int] = raw.get("date")
    out: Optional[int] = raw.get("out")
    conversation_message_id: Optional[int] = raw.get("conversation_message_id")
    random_id: Optional[int] = raw.get("random_id")
    attachments: Optional[list[Any]] = raw.get("attachments")
    fwd_messages: Optional[list[Any]] = raw.get("fwd_messages")

    if not message_id or not peer_id:
        return None

    return NormalizedMessageEvent(
        message_id=message_id,
        peer_id=peer_id,
        text=text,
        from_id=from_id,
        is_group=not is_user,
        raw=raw,
        date=date,
        out=out,
        conversation_message_id=conversation_message_id,
        random_id=random_id,
        attachments=attachments or [],
        fwd_messages=fwd_messages or [],
    )
