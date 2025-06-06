import asyncio
import os

from dotenv import load_dotenv

from core.context.message_context import MessageContext
from core.router import Router
from core.router_registry import load_router
from core.runner import run_polling

load_dotenv()
router = Router()


@router.on_message(text="ping")
async def handle_message(event: MessageContext):
    await event.answer("приуэт")


load_router(router)

if __name__ == "__main__":
    asyncio.run(run_polling(os.getenv("TOKEN")))
