from loguru import logger

from client.base import BaseClient
from core.context.message_context import MessageContext
from core.router_registry import get_all_handlers
from models.events.message import MessageEvent
from utils.polling import poll_events


# TODO: Improve the logic of event handling
async def run_polling(access_token: str) -> None:
    client = BaseClient(access_token)

    handlers = get_all_handlers()

    async for raw_event in poll_events(client):
        try:
            event = MessageEvent(**raw_event)
            ctx = MessageContext(event, client)

            for handler in handlers:
                if handler.matches(ctx):
                    await handler(ctx)

        except Exception as e:
            logger.exception(f"Error while handling event: {e}")
