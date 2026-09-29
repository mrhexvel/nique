from __future__ import annotations


def test_public_imports() -> None:
    from nique import GroupAccount, Nique, Router, UserAccount
    from nique.events import MessageContext
    from nique.filters import Command, Text
    from nique.http import HttpxTransport, NiquestsTransport

    assert all(
        item is not None
        for item in (
            GroupAccount,
            Nique,
            Router,
            UserAccount,
            MessageContext,
            Command,
            Text,
            HttpxTransport,
            NiquestsTransport,
        )
    )
