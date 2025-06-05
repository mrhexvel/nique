from typing import TYPE_CHECKING

from models.events.message import MessageEvent
from utils.random_id import generate_random_id

if TYPE_CHECKING:
    from client.base import BaseClient


class MessageContext:
    __slots__ = ("event", "_client")

    def __init__(self, event: MessageEvent, client: "BaseClient") -> None:
        self.event = event
        self._client = client

    @property
    def text(self) -> str:
        """Text of the message

        :return: Text of the message
        """
        return self.event.text

    @property
    def peer_id(self) -> int:
        """Peer id of the message event

        :return: Peer id of the message event
        """
        return self.event.peer_id

    @property
    def client(self) -> "BaseClient":
        """The client associated with this message event.

        :return: The client associated with this message event
        """
        return self._client

    async def answer(self, text: str) -> None:
        """Send a message to the peer who sent the message event
        :param text: The text of the message to send
        """
        payload = {
            "peer_id": self.peer_id,
            "message": text,
            "random_id": generate_random_id(),
        }

        await self._client.request("messages.send", payload)
