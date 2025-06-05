import asyncio
import os

from dotenv import load_dotenv

from client.base import BaseClient
from core.context.message_context import MessageContext, MessageEvent
from core.router import get_message_handlers, on_message

load_dotenv()


@on_message(text="привет")
async def handle_message(event: MessageContext):
    if event.text.lower() == "привет":
        await event.answer("приуэт")


async def fake_lp_event():
    return {
        "user_id": 715616525,
        "peer_id": 715616525,
        "text": "привет",
        "from_id": 715616525,
        "id": 1,
        "conversation_message_id": 1,
        "date": 1749085974,
    }


async def main():
    token = os.getenv("TOKEN")

    if not token:
        return

    client = BaseClient(token)

    while True:  # TODO: реализовать обработку ивентов для групп и пользователя под капотом библиотеки.
        raw_event = await fake_lp_event()

        event = MessageEvent(**raw_event)
        ctx = MessageContext(event, client)

        for handler in get_message_handlers():
            if handler.matches(ctx):
                await handler(ctx)

        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
