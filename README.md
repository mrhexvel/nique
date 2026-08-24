# NiQue

NiQue is a typed, asynchronous Python SDK and framework for VK API applications. It supports
user and group accounts, typed API namespaces, User and Group Long Poll, routers, filters,
middleware, and isolated multi-account runtimes.

NiQue requires Python 3.12 or newer and uses `asyncio`, Pydantic v2, and Niquests by default.

## Installation

```bash
uv add git+https://github.com/mrhexvel/nique
```

HTTPX is optional:

```bash
uv add "nique[httpx] @ git+https://github.com/mrhexvel/nique"
```

## Userbot

```python
import asyncio

from nique import Nique, Router, UserAccount
from nique.events import MessageContext
from nique.filters import Command

router = Router()


@router.message(Command("ping"))
async def ping(ctx: MessageContext) -> None:
    await ctx.answer("pong")


async def main() -> None:
    app = Nique()
    app.include_router(router)
    app.add_account(UserAccount(name="main", token="vk1.a..."))
    await app.run()


asyncio.run(main())
```

## Group bot

```python
app = Nique()
app.include_router(router)
app.add_account(GroupAccount(name="community", token="...", group_id=123))
await app.run()
```

## Multiple accounts

```python
app = Nique()
app.include_router(router)
app.add_account(UserAccount(name="first", token="..."))
app.add_account(UserAccount(name="second", token="..."))
await app.run()
```

Each account owns its API client and Long Poll state. Authentication failures and polling
failures are contained at the account runtime boundary.

## SDK-only usage

```python
async with Nique() as app:
    account = await app.create_account(UserAccount(name="sdk", token="..."))
    users = await account.api.users.get(user_ids=[1])
```

Typed methods currently include `users.get`, `groups.getById`, `messages.send`,
`messages.getById`, `messages.getLongPollServer`, and `groups.getLongPollServer`.

Methods not yet wrapped remain available through the raw boundary:

```python
result = await account.api.raw.call("some.newMethod", params={"foo": "bar"})
```

## Password authorization

Password authorization follows the current VK ID web flow and requires a target VK application
that you own or are permitted to use. NiQue does not ship third-party application credentials.

```python
from nique.auth import VKApplication, VKUserScope

account = UserAccount.from_credentials(
    name="secondary",
    login="+79990000000",
    password="secret",
    application=VKApplication(
        app_id=123456,
        scope=VKUserScope.MESSAGES | VKUserScope.OFFLINE,
    ),
)
app.add_account(account)
```

The flow uses a separate cookie session per login, obtains an API access token, validates it,
then closes the temporary auth session. Push, QR/passkey, captcha, and other non-code challenges
require additional challenge-provider support and can be rejected explicitly.

Requested scope does not guarantee capabilities. VK may restrict methods by token type,
application, policy, account state, and API version.

## Transports and ownership

Niquests is the default transport. Existing sessions can be borrowed explicitly:

```python
import niquests

from nique import Nique
from nique.http import NiquestsTransport

session = niquests.AsyncSession()
app = Nique(transport=NiquestsTransport(session=session, owns_session=False))
```

NiQue closes its transport during shutdown. A transport configured with a borrowed client does
not close that client.

HTTPX usage:

```python
from nique import Nique
from nique.http import HttpxTransport

app = Nique(transport=HttpxTransport())
```

## Lifecycle

NiQue supports `async with Nique()`, explicit `start()` / `stop()`, and framework `run()`.
Network resources are created at startup, not during import or construction. `stop()` is
idempotent.

## Architecture

The package follows one-way layers: `app -> runtime -> features -> api -> entities -> shared`.
The application is the composition root. API transports are application-scoped, API clients and
Long Poll state are account-scoped, and message contexts are event-scoped values. There is no
process-global container, queue, router registry, session, or mutable account state.

## Security

Do not commit credentials or tokens. Passwords and tokens use Pydantic `SecretStr` and are not
included in normal representations or framework errors. NiQue never reads `.env` automatically
and does not configure process-wide logging.
