from __future__ import annotations

from nique.api.executor import VKApiExecutor
from nique.api.objects.groups import Group
from nique.api.serialization import VKRequestSerializer
from nique.shared.models import VKRequestModel, VKResponseModel


class GroupsGetByIdRequest(VKRequestModel):
    group_ids: list[int | str] | None = None
    group_id: int | str | None = None
    fields: list[str] | None = None


class GroupsGetByIdResponse(VKResponseModel):
    groups: list[Group]


class GroupsLongPollServer(VKResponseModel):
    key: str
    server: str
    ts: str


class GroupsMethods:
    def __init__(self, executor: VKApiExecutor, serializer: VKRequestSerializer) -> None:
        self._executor = executor
        self._serializer = serializer

    async def get_by_id(
        self,
        *,
        group_ids: list[int | str] | None = None,
        group_id: int | str | None = None,
        fields: list[str] | None = None,
    ) -> GroupsGetByIdResponse:
        request = GroupsGetByIdRequest(group_ids=group_ids, group_id=group_id, fields=fields)
        return await self._executor.call(
            "groups.getById", self._serializer.serialize(request), GroupsGetByIdResponse
        )

    async def get_long_poll_server(self, *, group_id: int) -> GroupsLongPollServer:
        return await self._executor.call(
            "groups.getLongPollServer", {"group_id": group_id}, GroupsLongPollServer
        )
