from __future__ import annotations

from typing import Protocol

from pydantic import SecretStr

from nique.entities.tokens import AccessToken
from nique.features.auth.contracts import AccountId, TokenProvider, TokenStore
from nique.features.auth.errors import TokenValidationError


class StaticTokenProvider:
    """Returns a token supplied directly by the user."""

    def __init__(self, token: str | AccessToken) -> None:
        self._token = (
            token if isinstance(token, AccessToken) else AccessToken(value=SecretStr(token))
        )

    async def get_token(self) -> AccessToken:
        return self._token


class CachedTokenProvider:
    """Uses a validated cached token before invoking the fallback provider."""

    def __init__(
        self,
        account_id: AccountId,
        store: TokenStore,
        fallback: TokenProvider,
        validator: TokenValidatorProtocol,
    ) -> None:
        self._account_id = account_id
        self._store = store
        self._fallback = fallback
        self._validator = validator

    async def get_token(self) -> AccessToken:
        cached = await self._store.get(self._account_id)
        if cached is not None and await self._validator.validate(cached):
            return cached
        token = await self._fallback.get_token()
        if not await self._validator.validate(token):
            raise TokenValidationError("Token validation failed")
        await self._store.set(self._account_id, token)
        return token


class TokenValidatorProtocol(Protocol):
    async def validate(self, token: AccessToken) -> bool: ...
