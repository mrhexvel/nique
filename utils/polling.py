import asyncio
from typing import AsyncGenerator

from client.base import BaseClient


async def poll_events(client: BaseClient) -> AsyncGenerator[dict, None]:
    while True:
        # ❗ не обессудьте, это для теста
        yield {
            "user_id": 715616525,
            "peer_id": 715616525,
            "text": "ping",
            "from_id": 715616525,
            "id": 1,
            "conversation_message_id": 1,
            "date": 1749085974,
        }
        await asyncio.sleep(1)
