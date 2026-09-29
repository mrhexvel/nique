from __future__ import annotations

from nique import Nique, UserAccount
from nique.app.application import ApplicationState
from nique.entities.tokens import AccessToken
from nique.shared.http.fake import FakeTransport


async def test_lifecycle_and_external_transport() -> None:
    transport = FakeTransport()
    app = Nique(transport=transport)
    app.add_account(UserAccount(name="main", token="token"))

    await app.start()
    assert app.state is ApplicationState.RUNNING
    await app.stop()
    await app.stop()

    assert app.state is ApplicationState.STOPPED
    assert transport.closed


class FailingProvider:
    async def get_token(self) -> AccessToken:
        raise RuntimeError("isolated failure")


async def test_account_startup_failure_is_isolated() -> None:
    app = Nique(transport=FakeTransport())
    app.add_account(UserAccount(name="broken", token_provider=FailingProvider()))
    app.add_account(UserAccount(name="healthy", token="token"))

    await app.start()

    assert app.state is ApplicationState.RUNNING
    assert [context.account.name for context in app.account_contexts] == ["healthy"]
    await app.stop()
