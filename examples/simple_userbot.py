import asyncio

from nique import Nique, Router, UserAccount
from nique.events import MessageContext
from nique.filters import Command

router = Router()


@router.message(Command("ping"))
async def ping(ctx: MessageContext) -> None:
    await ctx.answer("pong")


async def main() -> None:
    app = Nique()
    app.include_router(router)
    app.add_account(UserAccount(name="main", token="YOUR_USER_TOKEN"))
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
