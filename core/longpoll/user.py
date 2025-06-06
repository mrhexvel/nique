from typing import Any, AsyncGenerator, Dict

from loguru import logger

from client.base import BaseClient
from core.longpoll.base import LongPollProvider


class UserLongPollProvider(LongPollProvider):
    def __init__(self, client: BaseClient):
        self.client = client

    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        while True:
            raw_events = await self.client.get_long_poll_events()
            for raw_event in raw_events:
                if raw_event[0] == 4:
                    message_id = raw_event[1]
                    full_message = await self.client.get_message_by_id(message_id)
                    yield full_message
