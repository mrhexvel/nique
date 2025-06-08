import asyncio

from loguru import logger

from client.api import API

_send_queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()


async def enqueue_message(method: str, payload: dict) -> None:
    """
    Asynchronously enqueue a message to be sent to the VK API.

    :param method: The method to call on the VK API
    :param payload: The payload to pass to the VK API
    """
    await _send_queue.put((method, payload))


async def start_message_sender_worker(api: API, interval: float = 0.1) -> None:
    """
    Starts a worker that will send messages to the VK API.

    :param api: The API instance to use for sending messages
    :param interval: The interval in seconds between checks for new messages to send
    """

    async def worker():
        while True:
            if not _send_queue.empty():
                method, payload = await _send_queue.get()
                try:
                    await api.request(method, payload)
                except Exception as e:
                    logger.error(
                        f"Failed to send message: ({method}, {payload}) | Error: {e}"
                    )
            await asyncio.sleep(interval)

    asyncio.create_task(worker())
