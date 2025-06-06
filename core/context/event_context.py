from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from models.events import NormalizedMessageEvent
from utils.random_id import generate_random_id

if TYPE_CHECKING:
    from client.base import BaseClient


class EventContext:
    __slots__ = ("event", "_client", "_full_message", "_raw_event")

    def __init__(
        self,
        event: NormalizedMessageEvent,
        client: BaseClient,
        raw_event: Optional[dict[str, Any]] = None,
    ) -> None:
        self.event = event
        self._client = client
        self._full_message: Optional[dict] = None
        self._raw_event = raw_event or {}

    @property
    def full_message(self) -> dict[str, Any]:
        """Returns the full message object, loading it from the VK API if necessary."""
        return self._full_message

    @property
    def message_id(self) -> int:
        """Message id of the message"""
        return self.event.message_id

    @property
    def text(self) -> str:
        """Text of the message"""
        return self.event.text

    @property
    def peer_id(self) -> int:
        """Peer id of the message"""
        return self.event.peer_id

    @property
    def from_id(self) -> int:
        """Sender id of the message"""
        return self.event.from_id

    @property
    def client(self) -> BaseClient:
        """VK API client instance"""
        return self._client

    @property
    def raw(self) -> dict[str, Any]:
        """Returns the raw event data as a dictionary."""
        return self._raw_event

    @property
    def is_group(self) -> bool:
        """Is the message from a group chat."""
        return self.event.is_group

    @property
    def is_user(self) -> bool:
        """Determines if the message is from a user rather than a group."""
        return not self.event.is_group

    @property
    def date(self) -> int:
        """Unix timestamp of the message"""
        return self.event.date

    @property
    def out(self) -> int:
        """
        1 if the message is outcoming (i.e. sent by the current user),
        0 if the message is incoming.
        """
        return self.event.out

    @property
    def conversation_message_id(self) -> int:
        """Conversation-specific message id"""
        return self.event.conversation_message_id

    @property
    def random_id(self) -> int:
        """Random id of the message."""
        return self.event.random_id

    @property
    def attachments(self) -> list[Any]:
        """
        List of attachments associated with the message, such as photos,
        videos, documents, etc.
        """
        return self.event.attachments

    @property
    def fwd_messages(self) -> list[Any]:
        """List of forwarded messages associated with the message."""
        return self.event.fwd_messages

    async def load_full_message(self):
        """
        Asynchronously loads the full message data from the VK API using the
        message id.

        This method retrieves the full message object by calling the VK API's
        `messages.getById` method and stores it in the `_full_message` attribute.
        If the client is not available or the event does not have a `message_id`
        attribute, the method returns without performing any action.
        """
        if not self.client or not hasattr(self.event, "message_id"):
            return
        self._full_message = await self.client.get_message_by_id(self.event.message_id)

    async def get_full_message(self) -> dict:
        """
        Lazy-loads full message object from `vk api` using messages.getById.
        """
        if self._full_message is not None:
            return self._full_message

        response = await self._client.get_message_by_id(self.event.message_id)
        self._full_message = response
        return self._full_message

    async def answer(self, text: str) -> None:
        """Send a text reply to the message sender"""
        await self._client.request(
            "messages.send",
            {
                "peer_id": self.peer_id,
                "message": text,
                "random_id": generate_random_id(),
            },
        )

    async def send_sticker(self, sticker_id: int) -> None:
        """Send a sticker to the message sender"""
        await self._client.request(
            "messages.send",
            {
                "peer_id": self.peer_id,
                "sticker_id": sticker_id,
                "random_id": generate_random_id(),
            },
        )

    async def send_photo(self, attachment: str, text: str = "") -> None:
        """Send a photo attachment (attachment in form of 'photo123_456')"""
        await self._client.request(
            "messages.send",
            {
                "peer_id": self.peer_id,
                "attachment": attachment,
                "message": text,
                "random_id": generate_random_id(),
            },
        )

    async def send_attachments(self, attachments: list[str], text: str = "") -> None:
        """Send multiple attachments (photo/audio/video/etc.)"""
        await self._client.request(
            "messages.send",
            {
                "peer_id": self.peer_id,
                "attachment": ",".join(attachments),
                "message": text,
                "random_id": generate_random_id(),
            },
        )
