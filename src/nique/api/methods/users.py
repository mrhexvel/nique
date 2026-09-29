from __future__ import annotations

from nique.api.executor import VKApiExecutor
from nique.api.objects.users import User
from nique.api.serialization import VKRequestSerializer
from nique.shared.models import VKRequestModel


class UsersGetRequest(VKRequestModel):
    user_ids: list[int | str] | None = None
    fields: list[str] | None = None
    name_case: str | None = None


class UsersMethods:
    def __init__(self, executor: VKApiExecutor, serializer: VKRequestSerializer) -> None:
        self._executor = executor
        self._serializer = serializer

    async def get(
        self,
        *,
        user_ids: list[int | str] | None = None,
        fields: list[str] | None = None,
        name_case: str | None = None,
    ) -> list[User]:
        request = UsersGetRequest(user_ids=user_ids, fields=fields, name_case=name_case)
        return await self._executor.call(
            "users.get", self._serializer.serialize(request), list[User]
        )
