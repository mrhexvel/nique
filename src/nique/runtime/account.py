from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from pydantic import SecretStr

from nique.features.auth.contracts import AccountId, TokenProvider
from nique.features.auth.models import PasswordCredentials, VKApplication, VKUserScope
from nique.features.auth.providers import StaticTokenProvider
from nique.features.auth.verification import ChallengeProvider, VerificationProvider
from nique.features.routing.router import Router


@dataclass(slots=True, kw_only=True)
class Account:
    """Immutable account configuration added to a NiQue application."""

    name: str
    token_provider: TokenProvider | None
    id: UUID = field(default_factory=uuid4)
    routers: list[Router] = field(default_factory=list[Router], repr=False, compare=False)

    @property
    def account_id(self) -> AccountId:
        return AccountId(str(self.id))

    def include_router(self, router: Router) -> None:
        self.routers.append(router)


@dataclass(slots=True, kw_only=True, init=False)
class UserAccount(Account):
    """VK user account configured by token or a custom token provider."""

    application: VKApplication | None = None
    credentials: PasswordCredentials | None = None
    verification_provider: VerificationProvider | None = None
    challenge_provider: ChallengeProvider | None = None

    def __init__(
        self,
        *,
        name: str,
        token: str | None = None,
        token_provider: TokenProvider | None = None,
        application: VKApplication | None = None,
        id: UUID | None = None,
    ) -> None:
        if (token is None) == (token_provider is None):
            raise ValueError("Provide exactly one of token or token_provider")
        object.__setattr__(self, "name", name)
        provider = token_provider or StaticTokenProvider(token or "")
        object.__setattr__(self, "token_provider", provider)
        object.__setattr__(self, "application", application)
        object.__setattr__(self, "credentials", None)
        object.__setattr__(self, "verification_provider", None)
        object.__setattr__(self, "challenge_provider", None)
        object.__setattr__(self, "id", id or uuid4())
        object.__setattr__(self, "routers", [])

    @classmethod
    def from_credentials(
        cls,
        *,
        name: str,
        login: str,
        password: str | SecretStr,
        application: VKApplication,
        verification_provider: VerificationProvider | None = None,
        challenge_provider: ChallengeProvider | None = None,
        id: UUID | None = None,
    ) -> UserAccount:
        credentials = PasswordCredentials(
            login=login,
            password=password if isinstance(password, SecretStr) else SecretStr(password),
        )
        account = cls.__new__(cls)
        object.__setattr__(account, "name", name)
        object.__setattr__(account, "token_provider", None)
        object.__setattr__(account, "application", application)
        object.__setattr__(account, "credentials", credentials)
        object.__setattr__(account, "verification_provider", verification_provider)
        object.__setattr__(account, "challenge_provider", challenge_provider)
        object.__setattr__(account, "id", id or uuid4())
        object.__setattr__(account, "routers", [])
        return account


@dataclass(slots=True, kw_only=True, init=False)
class GroupAccount(Account):
    """VK community account authenticated with a group token."""

    group_id: int

    def __init__(self, *, name: str, token: str, group_id: int, id: UUID | None = None) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "token_provider", StaticTokenProvider(token))
        object.__setattr__(self, "group_id", group_id)
        object.__setattr__(self, "id", id or uuid4())
        object.__setattr__(self, "routers", [])


DEFAULT_USER_SCOPE = VKUserScope.MESSAGES | VKUserScope.OFFLINE
