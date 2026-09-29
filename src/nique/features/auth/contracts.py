from __future__ import annotations

from typing import NewType, Protocol

from nique.entities.tokens import AccessToken

AccountId = NewType("AccountId", str)


class TokenProvider(Protocol):
    async def get_token(self) -> AccessToken: ...


class TokenStore(Protocol):
    async def get(self, account_id: AccountId) -> AccessToken | None: ...

    async def set(self, account_id: AccountId, token: AccessToken) -> None: ...

    async def delete(self, account_id: AccountId) -> None: ...


class DeviceIdProvider(Protocol):
    def generate(self) -> str: ...
