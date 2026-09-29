from __future__ import annotations

import asyncio
import logging
from enum import Enum

from nique.api.client import VKApiClient
from nique.api.executor import VKApiExecutor
from nique.app.settings import NiqueSettings
from nique.entities.events import MessageNew
from nique.features.auth.contracts import TokenStore
from nique.features.auth.device import StableDeviceIdProvider
from nique.features.auth.password import PasswordTokenProvider, VKTokenValidator
from nique.features.auth.providers import CachedTokenProvider
from nique.features.auth.storage import MemoryTokenStore
from nique.features.polling.group import GroupLongPollEventSource
from nique.features.polling.user import UserLongPollEventSource
from nique.features.routing.context import EventAccount, EventAccountId, MessageContext
from nique.features.routing.dispatcher import Dispatcher
from nique.features.routing.router import Router
from nique.runtime.account import Account, GroupAccount, UserAccount
from nique.runtime.context import AccountContext
from nique.shared.exceptions import LifecycleError
from nique.shared.http.contracts import HttpTransport
from nique.shared.http.niquests import NiquestsSessionFactory, NiquestsTransport

logger = logging.getLogger("nique.runtime")


class _ShutdownRequested(Exception):
    pass


class ApplicationState(Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


class Nique:
    """Application facade for SDK-only and multi-account framework usage."""

    def __init__(
        self,
        *,
        settings: NiqueSettings | None = None,
        transport: HttpTransport | None = None,
        token_store: TokenStore | None = None,
    ) -> None:
        self.settings = settings or NiqueSettings()
        self._provided_transport = transport
        self._token_store = token_store or MemoryTokenStore()
        self._transport: HttpTransport | None = None
        self._accounts: list[Account] = []
        self._contexts: dict[str, AccountContext] = {}
        self._routers: list[Router] = []
        self._dispatcher = Dispatcher()
        self._stop_event: asyncio.Event | None = None
        self._login_semaphore: asyncio.Semaphore | None = None
        self.state = ApplicationState.CREATED

    def add_account(self, account: Account) -> Account:
        if self.state not in {ApplicationState.CREATED, ApplicationState.STOPPED}:
            raise LifecycleError("Accounts cannot be added while the application is running")
        if any(item.name == account.name for item in self._accounts):
            raise ValueError(f"Account name {account.name!r} is already registered")
        self._accounts.append(account)
        return account

    def include_router(self, router: Router) -> None:
        if self.state not in {ApplicationState.CREATED, ApplicationState.STOPPED}:
            raise LifecycleError("Routers cannot be added while the application is running")
        self._routers.append(router)

    @property
    def account_contexts(self) -> tuple[AccountContext, ...]:
        return tuple(self._contexts.values())

    async def create_account(self, account: Account) -> AccountContext:
        if self.state is not ApplicationState.RUNNING:
            raise LifecycleError("Application must be started before creating an account")
        if account not in self._accounts:
            self._accounts.append(account)
        return await self._create_context(account)

    async def start(self) -> None:
        if self.state is ApplicationState.RUNNING:
            return
        if self.state is ApplicationState.STOPPING:
            raise LifecycleError("Application is stopping")
        self.state = ApplicationState.STARTING
        self._transport = self._provided_transport or NiquestsTransport()
        self._stop_event = asyncio.Event()
        self._login_semaphore = asyncio.Semaphore(self.settings.max_concurrent_logins)
        startup_errors: list[Exception] = []
        try:
            async with asyncio.TaskGroup() as group:
                for account in self._accounts:
                    group.create_task(self._start_account(account, startup_errors))
            if self._accounts and not self._contexts:
                raise ExceptionGroup("All account startups failed", startup_errors)
        except BaseException:
            await self._transport.aclose()
            self._transport = None
            self.state = ApplicationState.STOPPED
            raise
        self.state = ApplicationState.RUNNING

    async def stop(self) -> None:
        if self.state in {ApplicationState.CREATED, ApplicationState.STOPPED}:
            self.state = ApplicationState.STOPPED
            return
        if self.state is ApplicationState.STOPPING:
            return
        self.state = ApplicationState.STOPPING
        if self._stop_event is not None:
            self._stop_event.set()
        if self._transport is not None:
            await self._transport.aclose()
        self._transport = None
        self._contexts.clear()
        self.state = ApplicationState.STOPPED

    async def run(self) -> None:
        await self.start()
        if self._stop_event is None:
            raise LifecycleError("Application stop event was not initialized")
        try:
            try:
                async with asyncio.TaskGroup() as group:
                    for context in self._contexts.values():
                        group.create_task(self._supervise_account(context))
                    await self._stop_event.wait()
                    raise _ShutdownRequested
            except* _ShutdownRequested:
                pass
        finally:
            await self.stop()

    async def __aenter__(self) -> Nique:
        await self.start()
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.stop()

    async def _create_context(self, account: Account) -> AccountContext:
        if self._transport is None:
            raise LifecycleError("HTTP transport is unavailable")
        provider = account.token_provider
        if provider is None:
            if not isinstance(account, UserAccount):
                raise LifecycleError("Account has no token provider")
            if account.credentials is None or account.application is None:
                raise LifecycleError("Password account is missing credentials or VK application")
            if self._login_semaphore is None:
                raise LifecycleError("Authentication concurrency policy is unavailable")
            validator = VKTokenValidator(
                self._transport,
                api_version=self.settings.vk_api_version,
                timeout=self.settings.request_timeout,
            )
            password_provider = PasswordTokenProvider(
                credentials=account.credentials,
                application=account.application,
                session_factory=NiquestsSessionFactory(),
                validator=validator,
                verification_provider=account.verification_provider,
                challenge_provider=account.challenge_provider,
                device_id_provider=StableDeviceIdProvider(str(account.id)),
                login_semaphore=self._login_semaphore,
            )
            provider = CachedTokenProvider(
                account.account_id,
                self._token_store,
                password_provider,
                validator,
            )
        token = await provider.get_token()
        executor = VKApiExecutor(
            self._transport,
            token,
            api_version=self.settings.vk_api_version,
            timeout=self.settings.request_timeout,
        )
        context = AccountContext(account=account, api=VKApiClient(executor))
        self._contexts[str(account.id)] = context
        return context

    async def _start_account(self, account: Account, startup_errors: list[Exception]) -> None:
        try:
            await self._create_context(account)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            startup_errors.append(error)
            logger.exception("Account startup failed", extra={"account": account.name})

    async def _supervise_account(self, context: AccountContext) -> None:
        try:
            await self._run_account(context)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Account runtime failed", extra={"account": context.account.name})

    async def _run_account(self, context: AccountContext) -> None:
        if self._transport is None:
            raise LifecycleError("HTTP transport is unavailable")
        if isinstance(context.account, GroupAccount):
            source = GroupLongPollEventSource(
                context.api,
                self._transport,
                context.account.group_id,
                wait=self.settings.long_poll_wait,
            )
        else:
            source = UserLongPollEventSource(
                context.api, self._transport, wait=self.settings.long_poll_wait
            )
        routers = [*self._routers, *context.account.routers]
        async for event in source.listen():
            if not isinstance(event, MessageNew):
                continue
            message_context = MessageContext(
                event=event,
                account=EventAccount(EventAccountId(str(context.account.id)), context.account.name),
                api=context.api,
            )
            await self._dispatcher.dispatch(message_context, routers)
