from typing import Any, AsyncGenerator, Dict

from client.base import BaseClient
from core.longpoll.base import LongPollProvider


class GroupLongPollProvider(LongPollProvider):
    def __init__(self, client: BaseClient):
        self.client = client

    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        while True:
            events = await self.client.get_long_poll_events()
            for event in events:
                if event.get("type") == "message_new":
                    message_id = event["object"]["message"]["id"]
                    full_message = await self.client.get_message_by_id(message_id)
                    yield full_message
