from __future__ import annotations

import json

import pytest
from pydantic import SecretStr

from nique.features.auth.models import PasswordCredentials, VKApplication, VKUserScope
from nique.features.auth.password import AuthState, PasswordTokenProvider, VKTokenValidator
from nique.features.auth.verification import (
    AuthChallenge,
    ChallengeResponse,
    VerificationChallenge,
)
from nique.shared.http.fake import FakeTransport
from nique.shared.http.response import HttpResponse


def json_response(payload: object, *, url: str | None = None) -> HttpResponse:
    return HttpResponse(200, {}, json.dumps(payload).encode(), url=url)


class FakeSessionFactory:
    def __init__(self, transport: FakeTransport) -> None:
        self.transport = transport

    def create(self) -> FakeTransport:
        return self.transport


class FakeChallengeProvider:
    async def resolve(self, challenge: AuthChallenge) -> ChallengeResponse:
        _ = challenge
        return ChallengeResponse(success_token="captcha-solved")


class FakeVerificationProvider:
    async def get_code(self, challenge: VerificationChallenge) -> str:
        _ = challenge
        return "123456"


@pytest.mark.asyncio
async def test_password_flow_returns_validated_token_and_closes_auth_session() -> None:
    init = {
        "auth": {
            "host_app_id": 1,
            "access_token": "bootstrap",
            "anonymous_token": "anonymous",
        },
        "data": {"uuid": "uuid"},
    }
    auth_transport = FakeTransport(
        [
            HttpResponse(200, {}, f"<script>window.init = {json.dumps(init)};</script>".encode()),
            json_response({"response": {"token": "anonymous"}}),
            json_response({"response": {"auth_token": "bootstrap"}}),
            json_response(
                {
                    "error": {
                        "error_code": 14,
                        "error_msg": "Captcha needed",
                        "captcha_sid": "captcha-sid",
                        "redirect_uri": "https://id.vk.ru/captcha",
                    }
                }
            ),
            json_response(
                {
                    "response": {
                        "sid": "sid",
                        "next_step": {
                            "verification_method": "sms",
                            "has_another_verification_methods": False,
                        },
                    }
                }
            ),
            json_response({"response": {"status": 1}}),
            json_response({"response": {"sid": "verified-sid", "can_skip_password": True}}),
            json_response({"type": "okay"}),
            json_response({}, url="https://oauth.vk.ru/blank.html#access_token=token&user_id=7"),
        ]
    )
    api_transport = FakeTransport(
        [json_response({"response": [{"id": 7, "first_name": "A", "last_name": "B"}]})]
    )
    credentials = PasswordCredentials(login="user", password=SecretStr("super-secret-value"))
    provider = PasswordTokenProvider(
        credentials=credentials,
        application=VKApplication(app_id=123, scope=VKUserScope.MESSAGES),
        session_factory=FakeSessionFactory(auth_transport),
        validator=VKTokenValidator(api_transport),
        challenge_provider=FakeChallengeProvider(),
        verification_provider=FakeVerificationProvider(),
    )

    token = await provider.get_token()

    assert token.value.get_secret_value() == "token"
    assert token.user_id == 7
    assert provider.state is AuthState.COMPLETED
    assert auth_transport.closed
    assert auth_transport.requests[0].url == "https://id.vk.ru/auth"
    assert auth_transport.requests[4].data is not None
    assert auth_transport.requests[4].data["success_token"] == "captcha-solved"
    assert auth_transport.requests[7].data is not None
    assert auth_transport.requests[7].data["password"] == ""
    assert "super-secret-value" not in repr(credentials)
    assert "token" not in repr(token)
