from __future__ import annotations

import json

import pytest
from pydantic import SecretStr

from nique.api.client import VKApiClient
from nique.api.errors import VKApiError
from nique.api.executor import VKApiExecutor
from nique.api.serialization import VKRequestSerializer
from nique.entities.tokens import AccessToken
from nique.shared.http.fake import FakeTransport
from nique.shared.http.response import HttpResponse


def response(payload: object) -> HttpResponse:
    return HttpResponse(200, {}, json.dumps(payload).encode())


def test_serializer_handles_vk_values() -> None:
    serializer = VKRequestSerializer()
    assert serializer.serialize(enabled=True, skipped=None, ids=[1, 2]) == {
        "enabled": 1,
        "ids": "1,2",
    }


@pytest.mark.asyncio
async def test_typed_and_raw_methods() -> None:
    transport = FakeTransport(
        [
            response({"response": [{"id": 1, "first_name": "Pavel", "last_name": "Durov"}]}),
            response({"response": {"future": True}}),
        ]
    )
    executor = VKApiExecutor(
        transport, AccessToken(value=SecretStr("secret")), api_version="5.199", timeout=1
    )
    api = VKApiClient(executor)

    users = await api.users.get(user_ids=[1])
    raw = await api.raw.call("future.method")

    assert users[0].id == 1
    assert raw == {"future": True}
    assert transport.requests[0].data == {
        "user_ids": "1",
        "access_token": "secret",
        "v": "5.199",
    }


@pytest.mark.asyncio
async def test_vk_error_is_typed() -> None:
    transport = FakeTransport([response({"error": {"error_code": 100, "error_msg": "bad"}})])
    executor = VKApiExecutor(
        transport, AccessToken(value=SecretStr("secret")), api_version="5.199", timeout=1
    )

    with pytest.raises(VKApiError) as captured:
        await executor.call("broken", {}, object)

    assert captured.value.payload.error_code == 100
    assert "secret" not in str(captured.value)
