from loguru import logger

from client.base import BaseClient
from core.context.event_context import EventContext
from core.dispatcher import dispatch_event
from core.longpoll.adapter import normalize_event
from core.longpoll.group import GroupLongPollProvider
from core.longpoll.user import UserLongPollProvider
from core.router import Router
from core.router_registry import get_all_routers


async def run_polling(
    client: BaseClient, routers: list[Router], load_full: bool = True
):
    """
    Start longpolling for the given client and routers.

    :param client: an instance of BaseClient
    :param routers: a list of Router instances
    :param load_full: if True, will load the full message before dispatching, defaults to True

    :return: None
    """
    token_type = await client.detect_token_type()

    if token_type == "user":
        poller = UserLongPollProvider(client)
    else:
        poller = GroupLongPollProvider(client)

    routers = get_all_routers()

    async for raw_event in poller.listen():
        try:
            event = normalize_event(raw_event, is_user=token_type == "user")
            if not event:
                continue

            ctx = EventContext(event, client, raw_event)

            if load_full:
                await ctx.load_full_message()

            await dispatch_event(ctx, client, routers)
        except Exception as e:
            logger.exception(f"Error while processing event: {e}")
