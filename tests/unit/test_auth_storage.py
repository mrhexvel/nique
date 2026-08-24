from __future__ import annotations

import json
import stat
from pathlib import Path
from uuid import UUID

from pydantic import SecretStr

from nique import Nique, UserAccount
from nique.entities.tokens import AccessToken
from nique.features.auth.contracts import AccountId
from nique.features.auth.device import StableDeviceIdProvider
from nique.features.auth.models import VKApplication, VKUserScope
from nique.features.auth.storage import JsonTokenStore, MemoryTokenStore
from nique.shared.http.fake import FakeTransport
from nique.shared.http.response import HttpResponse


async def test_json_token_store_round_trip_and_permissions(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    account_id = AccountId("account-id")
    token = AccessToken(
        value=SecretStr("secret-token"),
        user_id=7,
        app_id=123,
        scope=4096,
    )

    await JsonTokenStore(path).set(account_id, token)
    restored = await JsonTokenStore(path).get(account_id)

    assert restored is not None
    assert restored.value.get_secret_value() == "secret-token"
    assert restored.user_id == 7
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_stable_device_id_is_deterministic() -> None:
    first = StableDeviceIdProvider("account-id").generate()
    second = StableDeviceIdProvider("account-id").generate()

    assert first == second
    assert len(first) == 21


async def test_application_uses_valid_cached_token() -> None:
    account_id = UUID("d90b6520-30d9-4b48-926c-98f6705996aa")
    store = MemoryTokenStore()
    account = UserAccount.from_credentials(
        name="main",
        login="login",
        password="password",
        application=VKApplication(app_id=123, scope=VKUserScope.MESSAGES),
        id=account_id,
    )
    await store.set(account.account_id, AccessToken(value=SecretStr("cached")))
    transport = FakeTransport(
        [
            HttpResponse(
                200,
                {},
                json.dumps(
                    {"response": [{"id": 7, "first_name": "A", "last_name": "B"}]}
                ).encode(),
            )
        ]
    )
    app = Nique(transport=transport, token_store=store)
    app.add_account(account)

    await app.start()

    assert [context.account.name for context in app.account_contexts] == ["main"]
    assert len(transport.requests) == 1
    assert transport.requests[0].url.endswith("/users.get")
    await app.stop()
