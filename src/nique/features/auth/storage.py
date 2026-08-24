from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import cast

import aiofiles
import aiofiles.os
from pydantic import SecretStr

from nique.entities.tokens import AccessToken
from nique.features.auth.contracts import AccountId
from nique.features.auth.errors import AuthProtocolError


def _secure_opener(path: str, flags: int) -> int:
    return os.open(path, flags, 0o600)


class MemoryTokenStore:
    """Application-local concurrent token store."""

    def __init__(self) -> None:
        self._tokens: dict[AccountId, AccessToken] = {}
        self._lock = asyncio.Lock()

    async def get(self, account_id: AccountId) -> AccessToken | None:
        async with self._lock:
            return self._tokens.get(account_id)

    async def set(self, account_id: AccountId, token: AccessToken) -> None:
        async with self._lock:
            self._tokens[account_id] = token

    async def delete(self, account_id: AccountId) -> None:
        async with self._lock:
            self._tokens.pop(account_id, None)


class JsonTokenStore:
    """Application-owned JSON token store using atomic, owner-only files."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = asyncio.Lock()

    async def get(self, account_id: AccountId) -> AccessToken | None:
        async with self._lock:
            data = await self._read()
            raw = data.get(str(account_id))
            if raw is None:
                return None
            try:
                return AccessToken(
                    value=SecretStr(str(raw["value"])),
                    user_id=self._optional_int(raw.get("user_id")),
                    expires_in=self._optional_int(raw.get("expires_in")),
                    app_id=self._optional_int(raw.get("app_id")),
                    scope=self._optional_int(raw.get("scope")),
                    obtained_at=datetime.fromisoformat(str(raw["obtained_at"])),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise AuthProtocolError("Stored access token data is invalid") from error

    async def set(self, account_id: AccountId, token: AccessToken) -> None:
        async with self._lock:
            data = await self._read()
            data[str(account_id)] = {
                "value": token.value.get_secret_value(),
                "user_id": token.user_id,
                "expires_in": token.expires_in,
                "app_id": token.app_id,
                "scope": token.scope,
                "obtained_at": token.obtained_at.isoformat(),
            }
            await self._write(data)

    async def delete(self, account_id: AccountId) -> None:
        async with self._lock:
            data = await self._read()
            if data.pop(str(account_id), None) is not None:
                await self._write(data)

    async def _read(self) -> dict[str, dict[str, object]]:
        try:
            async with aiofiles.open(self._path, encoding="utf-8") as file:
                raw = json.loads(await file.read())
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as error:
            raise AuthProtocolError("Token store cannot be read") from error
        if not isinstance(raw, dict):
            raise AuthProtocolError("Token store root must be an object")
        result: dict[str, dict[str, object]] = {}
        for key, value in cast("dict[object, object]", raw).items():
            if isinstance(key, str) and isinstance(value, dict):
                result[key] = cast("dict[str, object]", value)
        return result

    async def _write(self, data: dict[str, dict[str, object]]) -> None:
        await aiofiles.os.makedirs(self._path.parent, mode=0o700, exist_ok=True)
        temporary = self._path.with_suffix(f"{self._path.suffix}.tmp")
        try:
            async with aiofiles.open(
                temporary,
                "w",
                encoding="utf-8",
                opener=_secure_opener,
            ) as file:
                await file.write(json.dumps(data, indent=2, sort_keys=True))
            await aiofiles.os.replace(temporary, self._path)
        except OSError as error:
            raise AuthProtocolError("Token store cannot be written") from error

    @staticmethod
    def _optional_int(value: object) -> int | None:
        return value if isinstance(value, int) else None
