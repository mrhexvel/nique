from typing import List

from loguru import logger

from client.api import API
from core.context.event_context import EventContext
from core.dispatcher import dispatch_event
from core.polling.adapter import normalize_event
from core.polling.group import GroupLongPollProvider
from core.polling.user import UserLongPollProvider
from core.routers.router import Router


class PollingRunner:
    def __init__(self, api: API, routers: List[Router]):
        self.api = api
        self.routers = routers

    async def start(self):
        """
        Start longpolling for the given client and routers.

        :param client: an instance of BaseClient
        :param routers: a list of Router instances
        :param load_full: if True, will load the full message before dispatching, defaults to True

        :return: None
        """
        token_type = await self.api.detect_token_type()

        if token_type == "user":
            poller = UserLongPollProvider(self.api)
        else:
            poller = GroupLongPollProvider(self.api)

        for router in self.routers:
            for handler in router.get_startup_handlers():
                try:
                    await handler()
                except Exception as e:
                    logger.exception(f"Error in on_startup handler: {e}")

        async for raw_event in poller.listen():
            try:
                event = normalize_event(raw_event, is_user=token_type == "user")

                if not event:
                    continue

                ctx = EventContext(event, self.api)
                await dispatch_event(ctx, self.routers)

            except Exception as e:
                logger.exception(f"Error while processing event: {e}")
