from typing import Any, AsyncGenerator, Dict

from loguru import logger

from client.api import API
from core.polling.base import LongPollProvider

{
    "group_id": 224391972,
    "type": "message_new",
    "event_id": "8bd6a82e64572cd9ca01de2dbadbca05256667b6",
    "v": "5.199",
    "object": {
        "client_info": {
            "button_actions": [
                "text",
                "vkpay",
                "open_app",
                "location",
                "open_link",
                "open_photo",
                "callback",
                "intent_subscribe",
                "intent_unsubscribe",
            ],
            "keyboard": True,
            "inline_keyboard": True,
            "carousel": True,
            "lang_id": 0,
        },
        "message": {
            "date": 1749346530,
            "from_id": 715616525,
            "id": 0,
            "version": 10010151,
            "out": 0,
            "fwd_messages": [],
            "important": False,
            "is_hidden": False,
            "attachments": [],
            "conversation_message_id": 147833,
            "text": "/stats",
            "is_unavailable": True,
            "peer_id": 2000000005,
            "random_id": 0,
        },
    },
}


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
