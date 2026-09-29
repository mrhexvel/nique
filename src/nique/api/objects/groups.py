from __future__ import annotations

from nique.shared.models import VKObjectModel


class Group(VKObjectModel):
    id: int
    name: str
    screen_name: str | None = None
    is_closed: int | None = None
    type: str | None = None
    photo_50: str | None = None
    photo_100: str | None = None
    photo_200: str | None = None
