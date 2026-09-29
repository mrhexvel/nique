from __future__ import annotations

import base64
import hashlib
import secrets
import string

_DEVICE_ALPHABET = string.ascii_letters + string.digits + "-_"


class RandomDeviceIdProvider:
    """Generates the 21-character device identifier expected by VK ID."""

    def generate(self) -> str:
        return "".join(secrets.choice(_DEVICE_ALPHABET) for _ in range(21))


class StableDeviceIdProvider:
    """Derives a stable VK device identifier from an account-scoped identity."""

    def __init__(self, identity: str) -> None:
        self._identity = identity

    def generate(self) -> str:
        digest = hashlib.sha256(f"nique:device:{self._identity}".encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")[:21]
