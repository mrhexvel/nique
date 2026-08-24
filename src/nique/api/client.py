from __future__ import annotations

from nique.api.executor import VKApiExecutor
from nique.api.methods.groups import GroupsMethods
from nique.api.methods.messages import MessagesMethods
from nique.api.methods.users import UsersMethods
from nique.api.raw import RawMethods
from nique.api.serialization import VKRequestSerializer


class VKApiClient:
    """Account-scoped typed facade for VK API methods."""

    def __init__(self, executor: VKApiExecutor) -> None:
        serializer = VKRequestSerializer()
        self.users = UsersMethods(executor, serializer)
        self.messages = MessagesMethods(executor, serializer)
        self.groups = GroupsMethods(executor, serializer)
        self.raw = RawMethods(executor)
