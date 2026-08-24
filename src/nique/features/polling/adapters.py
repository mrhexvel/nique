from __future__ import annotations

from typing import cast

from nique.api.objects.messages import Message
from nique.entities.events import MessageEdit, MessageNew, NormalizedEvent


def adapt_group_event(raw: object) -> NormalizedEvent | None:
    if not isinstance(raw, dict):
        return None
    event = cast("dict[str, object]", raw)
    event_type = event.get("type")
    if event_type not in {"message_new", "message_edit"}:
        return None
    object_data = event.get("object")
    if not isinstance(object_data, dict):
        return None
    typed_object = cast("dict[str, object]", object_data)
    message_data = typed_object.get("message", typed_object)
    if not isinstance(message_data, dict):
        return None
    message = Message.model_validate(message_data)
    group_id = event.get("group_id")
    parsed_group_id = group_id if isinstance(group_id, int) else None
    if event_type == "message_new":
        return MessageNew(message=message, group_id=parsed_group_id)
    return MessageEdit(message=message, group_id=parsed_group_id)


def adapt_user_event(raw: object) -> NormalizedEvent | None:
    if not isinstance(raw, list):
        return None
    values = cast("list[object]", raw)
    if len(values) < 7 or values[0] != 4:
        return None
    if not all(isinstance(values[index], int) for index in (1, 3, 4)):
        return None
    typed_extra = cast("dict[str, object]", values[6]) if isinstance(values[6], dict) else {}
    from_id = typed_extra.get("from")
    message = Message(
        id=cast("int", values[1]),
        date=cast("int", values[4]),
        peer_id=cast("int", values[3]),
        from_id=int(from_id) if isinstance(from_id, (str, int)) else cast("int", values[3]),
        text=values[5] if isinstance(values[5], str) else "",
    )
    return MessageNew(message=message)
