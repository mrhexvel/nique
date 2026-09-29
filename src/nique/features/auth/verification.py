from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from nique.shared.models import NiqueModel


class VerificationMethod(StrEnum):
    PUSH = "push"
    EMAIL = "email"
    QR_CODE = "qr_code"
    CODE_GENERATOR = "codegen"
    SMS = "sms"
    CALL_RESET = "callreset"
    PASSWORD = "password"
    RESERVE_CODE = "reserve_code"
    PASSKEY = "passkey"


class VerificationChallenge(NiqueModel):
    method: VerificationMethod
    sid: str
    masked_destination: str | None = None


class VerificationProvider(Protocol):
    async def get_code(self, challenge: VerificationChallenge) -> str: ...


class AuthChallenge(NiqueModel):
    type: str
    sid: str | None = None
    url: str | None = None


class ChallengeResponse(NiqueModel):
    key: str | None = None
    success_token: str | None = None


class ChallengeProvider(Protocol):
    async def resolve(self, challenge: AuthChallenge) -> ChallengeResponse: ...
