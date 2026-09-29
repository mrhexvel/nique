from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
from time import perf_counter
from typing import cast
from urllib.parse import parse_qs, urlparse

from nique.features.auth.errors import AuthProtocolError, CaptchaRequiredError
from nique.features.auth.verification import AuthChallenge, ChallengeResponse
from nique.shared.http.contracts import HttpTransport

_POW_INPUT_PATTERN = re.compile(r'const\s+powInput\s*=\s*"([^"]*)"')
_DIFFICULTY_PATTERN = re.compile(r"const\s+difficulty\s*=\s*(\d+)")
_OBFUSCATED_POW_PATTERN = re.compile(
    r"}\(\s*['\"]([^'\"]+)['\"]\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*,"
    r"\s*['\"][^'\"]*['\"]\s*\)\s*\)\s*;?\s*</script>",
    re.DOTALL,
)


class VKNotRobotChallengeProvider:
    """Solves VK's proof-of-work not-robot challenge using an auth transport."""

    def __init__(
        self,
        transport: HttpTransport,
        *,
        api_version: str = "5.207",
        timeout: float = 30.0,
        max_difficulty: int = 8,
    ) -> None:
        self._transport = transport
        self._api_version = api_version
        self._timeout = timeout
        self._max_difficulty = max_difficulty

    async def resolve(self, challenge: AuthChallenge) -> ChallengeResponse:
        if challenge.url is None or "not_robot_captcha" not in challenge.url:
            raise CaptchaRequiredError(sid=challenge.sid, url=challenge.url)
        query = parse_qs(urlparse(challenge.url).query)
        session_token = self._required_query_value(query, "session_token")
        domain = query.get("domain", ["vk.com"])[0]

        async with asyncio.timeout(self._timeout):
            response = await self._transport.request("GET", challenge.url, timeout=self._timeout)
            pow_input, difficulty = self.extract_pow_details(response.text)
            if difficulty > self._max_difficulty:
                raise AuthProtocolError(
                    f"Captcha proof-of-work difficulty {difficulty} exceeds the safety limit"
                )
            started_at = perf_counter()
            hash_value, nonce = await self.perform_pow(pow_input, difficulty)
            duration_ms = round((perf_counter() - started_at) * 1000)
            pow_result = self.encode_pow_result(hash_value, nonce, duration_ms)
            base_data: dict[str, object] = {
                "session_token": session_token,
                "domain": domain,
            }
            await self._call("captchaNotRobot.componentDone", base_data)
            settings = await self._call("captchaNotRobot.settings", base_data)
            raw_sensor_list = settings.get("bridge_sensors_list")
            if not isinstance(raw_sensor_list, list):
                raise AuthProtocolError("Captcha settings contain no valid sensor list")
            sensor_list = cast("list[object]", raw_sensor_list)
            if not all(isinstance(item, str) for item in sensor_list):
                raise AuthProtocolError("Captcha settings contain no valid sensor list")
            sensors = {sensor: "[]" for sensor in sensor_list if isinstance(sensor, str)}
            result = await self._call(
                "captchaNotRobot.check",
                {
                    **base_data,
                    **sensors,
                    "hash": pow_result,
                    "answer": "e30=",
                },
            )
            success_token = result.get("success_token")
            if not isinstance(success_token, str) or not success_token:
                raise AuthProtocolError("Captcha check returned no success token")
            await self._call("captchaNotRobot.endSession", base_data)

            await asyncio.sleep(2)
            return ChallengeResponse(success_token=success_token)

    @staticmethod
    def extract_pow_details(text: str) -> tuple[str, int]:
        input_match = _POW_INPUT_PATTERN.search(text)
        difficulty_match = _DIFFICULTY_PATTERN.search(text)
        if input_match is not None and difficulty_match is not None:
            return input_match.group(1), int(difficulty_match.group(1))
        script_match = _OBFUSCATED_POW_PATTERN.search(text)
        if script_match is not None:
            return script_match.group(1), int(script_match.group(2), 0)
        raise AuthProtocolError("Captcha page contains no proof-of-work parameters")

    @staticmethod
    def calculate_hash(input_value: str, nonce: int) -> str:
        return hashlib.sha256(f"{input_value}{nonce}".encode()).hexdigest()

    @classmethod
    async def perform_pow(cls, input_value: str, difficulty: int) -> tuple[str, int]:
        prefix = "0" * difficulty
        nonce = 0
        while True:
            hash_value = cls.calculate_hash(input_value, nonce)
            if hash_value.startswith(prefix):
                return hash_value, nonce
            nonce += 1
            if nonce % 10_000 == 0:
                await asyncio.sleep(0)

    @staticmethod
    def encode_pow_result(hash_value: str, nonce: int, duration_ms: int) -> str:
        payload = json.dumps(
            {
                "hash": hash_value,
                "nonce": nonce,
                "duration_ms": duration_ms,
                "telemetry": {},
                "tel_hash": "",
            },
            separators=(",", ":"),
        ).encode()
        return "v2." + base64.b64encode(payload).decode()

    async def _call(self, method: str, data: dict[str, object]) -> dict[str, object]:
        response = await self._transport.request(
            "POST",
            f"https://api.vk.ru/method/{method}",
            data={**data, "access_token": "", "v": self._api_version},
            timeout=self._timeout,
        )
        payload = response.json()
        if not isinstance(payload, dict):
            raise AuthProtocolError(f"Captcha method {method} returned an invalid envelope")
        envelope = cast("dict[str, object]", payload)
        if "error" in envelope:
            error = envelope["error"]
            if isinstance(error, dict):
                typed_error = cast("dict[str, object]", error)
                code = typed_error.get("error_code")
                message = typed_error.get("error_msg")
                raise AuthProtocolError(f"Captcha method {method} failed ({code}: {message})")
            raise AuthProtocolError(f"Captcha method {method} failed")
        result = envelope.get("response")
        if result is None:
            return {}
        if not isinstance(result, dict):
            return {}
        return cast("dict[str, object]", result)

    @staticmethod
    def _required_query_value(query: dict[str, list[str]], key: str) -> str:
        value = query.get(key, [None])[0]
        if not isinstance(value, str) or not value:
            raise AuthProtocolError(f"Captcha URL contains no {key}")
        return value
