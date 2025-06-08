from typing import Any, AsyncGenerator, Dict

from client.api import API
from core.polling.base import LongPollProvider


class GroupLongPollProvider(LongPollProvider):
    def __init__(self, client: API):
        self.client = client

    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        while True:
            events = await self.client.get_long_poll_events()
            for event in events:
                if event.get("type") == "message_new":
                    full_message = await self.client.get_message_by_id(
                        peer_id=event["object"]["message"]["peer_id"],
                        cmids=event["object"]["message"]["conversation_message_id"],
                    )
                    yield full_message
