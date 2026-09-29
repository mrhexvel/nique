from __future__ import annotations

import asyncio
import json
import re
from enum import Enum
from typing import cast
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from pydantic import SecretStr

from nique.api.errors import VKApiError
from nique.api.executor import VKApiExecutor
from nique.entities.tokens import AccessToken
from nique.features.auth.captcha import VKNotRobotChallengeProvider
from nique.features.auth.contracts import DeviceIdProvider
from nique.features.auth.device import RandomDeviceIdProvider
from nique.features.auth.errors import (
    AccountBlockedError,
    AccountNotFoundError,
    AuthFloodControlError,
    AuthProtocolError,
    CaptchaRequiredError,
    InvalidCredentialsError,
    OAuthTokenError,
    TokenValidationError,
    UnsupportedVerificationError,
)
from nique.features.auth.models import PasswordCredentials, VKApplication
from nique.features.auth.verification import (
    AuthChallenge,
    ChallengeProvider,
    VerificationChallenge,
    VerificationMethod,
    VerificationProvider,
)
from nique.shared.http.contracts import HttpSessionFactory, HttpTransport

_INIT_PATTERN = re.compile(r"window\.init\s*=\s*({.*?})\s*;", re.DOTALL)
_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"
}
# Public client identifier used by VK's own mobile-web login entry point.
_VK_ID_MOBILE_WEB_APP_ID = 7_934_655
_VK_MOBILE_WEB_ORIGIN = "https://m.vk.ru"


class AuthState(Enum):
    CREATED = "created"
    BOOTSTRAPPING = "bootstrapping"
    VALIDATING_ACCOUNT = "validating_account"
    WAITING_VERIFICATION = "waiting_verification"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    REQUESTING_OAUTH_TOKEN = "requesting_oauth_token"
    VALIDATING_TOKEN = "validating_token"
    COMPLETED = "completed"
    FAILED = "failed"


class VKTokenValidator:
    """Validates a user token through users.get without exposing it."""

    def __init__(
        self, transport: HttpTransport, *, api_version: str = "5.199", timeout: float = 15.0
    ) -> None:
        self._transport = transport
        self._api_version = api_version
        self._timeout = timeout

    async def validate(self, token: AccessToken) -> bool:
        executor = VKApiExecutor(
            self._transport,
            token,
            api_version=self._api_version,
            timeout=self._timeout,
        )
        try:
            users = await executor.call("users.get", {}, list[dict[str, object]])
        except VKApiError:
            return False
        if not users or not isinstance(users[0].get("id"), int):
            return False
        token.user_id = cast("int", users[0]["id"])
        return True


class PasswordTokenProvider:
    """Native-async VK ID password flow yielding a validated VK API token."""

    def __init__(
        self,
        *,
        credentials: PasswordCredentials,
        application: VKApplication,
        session_factory: HttpSessionFactory,
        validator: VKTokenValidator,
        verification_provider: VerificationProvider | None = None,
        challenge_provider: ChallengeProvider | None = None,
        device_id_provider: DeviceIdProvider | None = None,
        login_semaphore: asyncio.Semaphore | None = None,
        auth_api_version: str = "5.207",
        timeout: float = 20.0,
    ) -> None:
        self._credentials = credentials
        self._application = application
        self._session_factory = session_factory
        self._validator = validator
        self._verification_provider = verification_provider
        self._challenge_provider = challenge_provider
        self._device_id_provider = device_id_provider or RandomDeviceIdProvider()
        self._semaphore = login_semaphore or asyncio.Semaphore(2)
        self._auth_api_version = auth_api_version
        self._timeout = timeout
        self.state = AuthState.CREATED

    async def get_token(self) -> AccessToken:
        async with self._semaphore:
            transport = self._session_factory.create()
            try:
                token = await self._authorize(transport)
                self.state = AuthState.VALIDATING_TOKEN
                if not await self._validator.validate(token):
                    raise TokenValidationError("VK rejected the acquired access token")
                self.state = AuthState.COMPLETED
                return token
            except BaseException:
                self.state = AuthState.FAILED
                raise
            finally:
                await transport.aclose()

    async def _authorize(self, transport: HttpTransport) -> AccessToken:
        self.state = AuthState.BOOTSTRAPPING
        device_id = self._device_id_provider.generate()
        bootstrap = await self._bootstrap(transport, device_id)
        self.state = AuthState.VALIDATING_ACCOUNT
        validation = await self._vk_method(
            transport,
            "auth.validateAccount",
            {
                "v": self._auth_api_version,
                "client_id": bootstrap["host_app_id"],
                "login": self._credentials.login,
                "sid": "",
                "device_id": device_id,
                "auth_token": bootstrap["access_token"],
                "super_app_token": "",
                "supported_ways": ",".join(item.value for item in VerificationMethod),
                "is_switcher_flow": "0",
                "is_edu_flow": "",
                "is_registration": "",
                "access_token": "",
            },
        )
        sid = validation.get("sid")
        if not isinstance(sid, str) or not sid:
            raise AccountNotFoundError("VK account was not found")
        sid, can_skip_password = await self._verify_if_needed(
            transport, bootstrap, validation, sid, device_id
        )
        self.state = AuthState.AUTHENTICATING
        login = await self._post_json(
            transport,
            "https://login.vk.ru/?act=connect_authorize",
            {
                "username": self._credentials.login,
                "password": (
                    "" if can_skip_password else self._credentials.password.get_secret_value()
                ),
                "auth_token": bootstrap["access_token"],
                "sid": sid,
                "uuid": bootstrap["uuid"],
                "device_id": device_id,
                "app_id": bootstrap["host_app_id"],
                "v": self._auth_api_version,
                "service_group": "",
                "save_user": "1",
                "version": "1",
            },
            headers={
                **_BROWSER_HEADERS,
                "Origin": "https://id.vk.ru",
                "Referer": "https://id.vk.ru/",
            },
        )
        if login.get("type") == "captcha":
            raise CaptchaRequiredError()
        if login.get("error_code") == "incorrect_password":
            raise InvalidCredentialsError("VK rejected the account credentials")
        if login.get("error_code") == "password_bruteforce":
            raise AuthFloodControlError("VK temporarily blocked password authorization attempts")
        if login.get("is_user_banned"):
            raise AccountBlockedError("VK account is blocked")
        if login.get("type") != "okay":
            response_type = login.get("type")
            error_code = login.get("error_code")
            keys = ", ".join(sorted(login))
            raise AuthProtocolError(
                "VK login response did not confirm authentication "
                f"(type={response_type!r}, error_code={error_code!r}, keys=[{keys}])"
            )
        self.state = AuthState.AUTHENTICATED
        return await self._oauth(transport)

    async def _bootstrap(self, transport: HttpTransport, device_id: str) -> dict[str, str]:
        request_uuid = str(uuid4())
        page_params: dict[str, object] = {
            "app_id": _VK_ID_MOBILE_WEB_APP_ID,
            "origin": _VK_MOBILE_WEB_ORIGIN,
            "redirect_uri": f"{_VK_MOBILE_WEB_ORIGIN}/login",
            "response_type": "token",
            "uuid": request_uuid,
            "device_id": device_id,
        }
        await transport.request(
            "GET",
            "https://id.vk.ru/auth",
            params=page_params,
            headers=_BROWSER_HEADERS,
            timeout=self._timeout,
        )
        anonymous = await self._vk_method(
            transport,
            "auth.getAnonymToken",
            {
                "client_id": _VK_ID_MOBILE_WEB_APP_ID,
                "device_id": device_id,
                "v": self._auth_api_version,
            },
        )
        initial_uri = "https://id.vk.ru/auth?" + "&".join(
            f"{key}={value}" for key, value in page_params.items()
        )
        auth_data = await self._vk_method(
            transport,
            "auth.getAuthData",
            {
                **page_params,
                "initial_uri": initial_uri,
                "lang": 0,
                "v": self._auth_api_version,
            },
        )
        required = {
            "host_app_id": _VK_ID_MOBILE_WEB_APP_ID,
            "access_token": auth_data.get("auth_token"),
            "anonymous_token": anonymous.get("token"),
            "uuid": request_uuid,
        }
        if not isinstance(required["host_app_id"], (str, int)) or not all(
            isinstance(required[key], str) and required[key] for key in ("access_token", "uuid")
        ):
            raise AuthProtocolError("VK ID bootstrap response is missing required fields")
        return {key: str(value) for key, value in required.items()}

    async def _verify_if_needed(
        self,
        transport: HttpTransport,
        bootstrap: dict[str, str],
        validation: dict[str, object],
        sid: str,
        device_id: str,
    ) -> tuple[str, bool]:
        next_step = validation.get("next_step")
        if not isinstance(next_step, dict):
            return sid, False
        typed_next_step = cast("dict[str, object]", next_step)
        method_value = typed_next_step.get("verification_method")
        if method_value in {None, VerificationMethod.PASSWORD.value}:
            return sid, False
        try:
            method = VerificationMethod(str(method_value))
        except ValueError as error:
            raise UnsupportedVerificationError(
                "VK requested an unsupported verification method"
            ) from error
        if typed_next_step.get("has_another_verification_methods") and await self._password_allowed(
            transport, bootstrap, sid, device_id
        ):
            return sid, False
        if self._verification_provider is None:
            raise UnsupportedVerificationError(
                f"VK requires {method.value} verification but no provider was configured"
            )
        self.state = AuthState.WAITING_VERIFICATION
        send_methods = {
            VerificationMethod.EMAIL: "ecosystem.sendOtpEmail",
            VerificationMethod.PUSH: "ecosystem.sendOtpPush",
            VerificationMethod.SMS: "ecosystem.sendOtpSms",
            VerificationMethod.CALL_RESET: "ecosystem.sendOtpCallReset",
        }
        send_method = send_methods.get(method)
        if send_method is not None:
            await self._vk_method(
                transport,
                send_method,
                {
                    "v": self._auth_api_version,
                    "client_id": bootstrap["host_app_id"],
                    "sid": sid,
                    "device_id": device_id,
                    "anonymous_token": bootstrap["anonymous_token"],
                    "access_token": "",
                },
            )
        code = await self._verification_provider.get_code(
            VerificationChallenge(method=method, sid=sid)
        )
        checked = await self._vk_method(
            transport,
            "ecosystem.checkOtp",
            {
                "v": self._auth_api_version,
                "client_id": bootstrap["host_app_id"],
                "sid": sid,
                "device_id": device_id,
                "code": code,
                "verification_method": method.value,
                "anonymous_token": bootstrap["anonymous_token"],
                "access_token": "",
            },
        )
        new_sid = checked.get("sid")
        if not isinstance(new_sid, str) or not new_sid:
            raise AuthProtocolError("VK verification response has no session identifier")
        return new_sid, checked.get("can_skip_password") is True

    async def _password_allowed(
        self,
        transport: HttpTransport,
        bootstrap: dict[str, str],
        sid: str,
        device_id: str,
    ) -> bool:
        result = await self._vk_method(
            transport,
            "ecosystem.getVerificationMethods",
            {
                "v": self._auth_api_version,
                "client_id": bootstrap["host_app_id"],
                "sid": sid,
                "device_id": device_id,
                "anonymous_token": bootstrap["anonymous_token"],
                "access_token": "",
            },
        )
        methods = result.get("methods")
        if not isinstance(methods, list):
            raise AuthProtocolError("VK verification methods response contains no methods list")
        for raw_method in cast("list[object]", methods):
            if not isinstance(raw_method, dict):
                continue
            method_data = cast("dict[str, object]", raw_method)
            if method_data.get("name") == VerificationMethod.PASSWORD.value:
                return True
        return False

    async def _oauth(self, transport: HttpTransport) -> AccessToken:
        self.state = AuthState.REQUESTING_OAUTH_TOKEN
        response = await transport.request(
            "GET",
            "https://oauth.vk.ru/authorize",
            params={
                "client_id": self._application.app_id,
                "scope": int(self._application.scope),
                "response_type": "token",
            },
            headers=_BROWSER_HEADERS,
            timeout=self._timeout,
        )
        token_data = self._token_from_url(response.url)
        if token_data is None:
            token_data = self._token_from_url(response.text)
        if token_data is None:
            token_data = await self._seamless_oauth(transport, response.text)
        value = token_data.get("access_token", [None])[0]
        if not isinstance(value, str) or not value:
            raise OAuthTokenError("VK OAuth returned an empty access token")
        return AccessToken(
            value=SecretStr(value),
            user_id=self._optional_int(token_data, "user_id"),
            expires_in=self._optional_int(token_data, "expires_in"),
            app_id=self._application.app_id,
            scope=int(self._application.scope),
        )

    async def _seamless_oauth(
        self, transport: HttpTransport, response_text: str
    ) -> dict[str, list[str]]:
        init = self._parse_init(response_text)
        data = self._mapping(init.get("data"), "OAuth bootstrap data")
        hashes = self._mapping(data.get("hash"), "OAuth bootstrap hashes")
        return_auth = hashes.get("return_auth")
        if not isinstance(return_auth, str) or not return_auth:
            raise OAuthTokenError("VK OAuth response did not contain an authorization hash")
        internal = await self._post_json(
            transport,
            "https://login.vk.ru/?act=connect_internal",
            {
                "return_auth_hash": return_auth,
                "app_id": self._application.app_id,
                "uuid": "",
                "service_group": "",
                "version": "1",
            },
        )
        temporary_token = internal.get("access_token")
        auth_user_hash = internal.get("auth_user_hash")
        if not isinstance(temporary_token, str) or not isinstance(auth_user_hash, str):
            raise OAuthTokenError("VK internal authorization response is incomplete")
        result = await self._vk_method(
            transport,
            "auth.getOauthToken",
            {
                "hash": return_auth,
                "auth_user_hash": auth_user_hash,
                "app_id": self._application.app_id,
                "client_id": self._application.app_id,
                "scope": int(self._application.scope),
                "access_token": temporary_token,
                "is_seamless_auth": 1,
                "v": self._auth_api_version,
            },
        )
        token = result.get("access_token")
        if not isinstance(token, str) or not token:
            raise OAuthTokenError("VK OAuth token response is incomplete")
        values: dict[str, list[str]] = {"access_token": [token]}
        for key in ("user_id", "expires_in"):
            value = result.get(key)
            if isinstance(value, (str, int)):
                values[key] = [str(value)]
        return values

    async def _vk_method(
        self, transport: HttpTransport, method: str, data: dict[str, object]
    ) -> dict[str, object]:
        request_data = dict(data)
        for _attempt in range(3):
            envelope = await self._post_json(
                transport, f"https://api.vk.ru/method/{method}", request_data
            )
            if "error" not in envelope:
                return self._mapping(envelope.get("response"), f"{method} response")
            error = self._mapping(envelope["error"], f"{method} error")
            code = error.get("error_code")
            message = error.get("error_msg")
            if code == 14:
                sid = error.get("captcha_sid")
                url = error.get("redirect_uri") or error.get("captcha_img")
                typed_sid = sid if isinstance(sid, str) else None
                typed_url = url if isinstance(url, str) else None
                provider = self._challenge_provider
                if provider is None and typed_url and "not_robot_captcha" in typed_url:
                    provider = VKNotRobotChallengeProvider(
                        transport,
                        api_version=self._auth_api_version,
                        timeout=self._timeout,
                    )
                if provider is None:
                    raise CaptchaRequiredError(sid=typed_sid, url=typed_url)
                solution = await provider.resolve(
                    AuthChallenge(type="captcha", sid=typed_sid, url=typed_url)
                )
                if solution.success_token:
                    request_data["success_token"] = solution.success_token
                    continue
                if solution.key and typed_sid:
                    request_data["captcha_sid"] = typed_sid
                    request_data["captcha_key"] = solution.key
                    continue
                raise AuthProtocolError("Captcha provider returned no usable solution")
            raise AuthProtocolError(f"VK authorization method {method} failed ({code}: {message})")
        raise AuthProtocolError(f"VK authorization method {method} exceeded challenge retries")

    async def _post_json(
        self,
        transport: HttpTransport,
        url: str,
        data: dict[str, object],
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        response = await transport.request(
            "POST",
            url,
            data=data,
            headers=headers or _BROWSER_HEADERS,
            timeout=self._timeout,
        )
        return self._mapping(response.json(), "authorization response")

    @staticmethod
    def _parse_init(text: str) -> dict[str, object]:
        match = _INIT_PATTERN.search(text)
        if match is None:
            raise AuthProtocolError("VK ID bootstrap data was not found")
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError as error:
            raise AuthProtocolError("VK ID bootstrap data is invalid") from error
        return PasswordTokenProvider._mapping(value, "VK ID bootstrap")

    @staticmethod
    def _mapping(value: object, name: str) -> dict[str, object]:
        if not isinstance(value, dict):
            raise AuthProtocolError(f"{name} must be an object")
        return cast("dict[str, object]", value)

    @staticmethod
    def _token_from_url(value: str | None) -> dict[str, list[str]] | None:
        if not value or "access_token=" not in value:
            return None
        parsed = urlparse(value)
        values = parse_qs(parsed.fragment or parsed.query)
        return values if "access_token" in values else None

    @staticmethod
    def _optional_int(values: dict[str, list[str]], key: str) -> int | None:
        value = values.get(key, [None])[0]
        return int(value) if isinstance(value, str) and value.isdigit() else None
