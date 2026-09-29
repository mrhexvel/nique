import asyncio

import niquests

from nique import Nique
from nique.http import NiquestsTransport


async def main() -> None:
    session = niquests.AsyncSession()
    try:
        async with Nique(transport=NiquestsTransport(session=session, owns_session=False)):
            pass
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
