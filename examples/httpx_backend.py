import asyncio

from nique import Nique
from nique.http import HttpxTransport


async def main() -> None:
    async with Nique(transport=HttpxTransport()):
        pass


if __name__ == "__main__":
    asyncio.run(main())
