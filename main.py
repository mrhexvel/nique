import asyncio
import os

from dotenv import load_dotenv
from loguru import logger

from client.api import API
from core.plugins.loader import Router
from module import Module

load_dotenv()

router = Router()


@router.on_startup()
async def startup():
    logger.info("Module successfully started")


module = Module(
    api=API(access_token=os.getenv("TOKEN")),
    plugins=["examples"],
)

module.add_router(router)


if __name__ == "__main__":
    asyncio.run(module.run_polling())
