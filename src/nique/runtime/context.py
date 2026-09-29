from __future__ import annotations

from dataclasses import dataclass

from nique.api.client import VKApiClient
from nique.runtime.account import Account


@dataclass(frozen=True, slots=True)
class AccountContext:
    """Account-specific services exposed to SDK users and event handlers."""

    account: Account
    api: VKApiClient
