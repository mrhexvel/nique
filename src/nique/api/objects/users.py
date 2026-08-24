from __future__ import annotations

from nique.shared.models import VKObjectModel


class User(VKObjectModel):
    id: int
    first_name: str
    last_name: str
    deactivated: str | None = None
    is_closed: bool | None = None
    can_access_closed: bool | None = None
