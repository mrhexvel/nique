import asyncio
import os

from dotenv import load_dotenv
from loguru import logger

from client.base import BaseClient
from core.context.event_context import EventContext
from core.router import Router
from core.router_registry import get_all_routers, load_router
from core.runner import run_polling

load_dotenv()
router = Router()


@router.on_message(text="ping")
async def handle_message(event: EventContext):
    await event.answer("pong")
    await event.get_full_message()

    logger.debug(event.full_message)


async def main():
    load_router(router)
    client = BaseClient(access_token=os.getenv("TOKEN"))
    await run_polling(client, get_all_routers(), load_full=False)


if __name__ == "__main__":
    asyncio.run(main())
