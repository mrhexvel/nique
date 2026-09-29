from __future__ import annotations

from typing import Literal

from nique.entities.vk import Message
from nique.shared.models import NiqueModel


class MessageNew(NiqueModel):
    type: Literal["message_new"] = "message_new"
    message: Message
    group_id: int | None = None


class MessageEdit(NiqueModel):
    type: Literal["message_edit"] = "message_edit"
    message: Message
    group_id: int | None = None


type NormalizedEvent = MessageNew | MessageEdit
