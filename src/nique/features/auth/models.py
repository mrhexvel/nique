from __future__ import annotations

from enum import IntFlag

from pydantic import ConfigDict, SecretStr

from nique.shared.models import NiqueModel


class VKUserScope(IntFlag):
    NOTIFY = 1
    FRIENDS = 2
    PHOTOS = 4
    AUDIO = 8
    VIDEO = 16
    STORIES = 64
    PAGES = 128
    STATUS = 1024
    NOTES = 2048
    MESSAGES = 4096
    WALL = 8192
    ADS = 32768
    OFFLINE = 65536
    DOCS = 131072
    GROUPS = 262144
    NOTIFICATIONS = 524288
    STATS = 1048576
    EMAIL = 4194304
    MARKET = 134217728


class PasswordCredentials(NiqueModel):
    model_config = ConfigDict(frozen=True)

    login: str
    password: SecretStr


class VKApplication(NiqueModel):
    model_config = ConfigDict(frozen=True)

    app_id: int
    scope: VKUserScope | int
