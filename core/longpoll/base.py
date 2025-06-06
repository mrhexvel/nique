from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict


class LongPollProvider(ABC):
    @abstractmethod
    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Listen for events from the long poll server and yield them as they arrive.

        This is an asynchronous generator method that continuously listens for
        incoming events from the long poll server. Each event is yielded as a
        dictionary containing event data.

        :return: An asynchronous generator yielding event data dictionaries.
        """
        pass
