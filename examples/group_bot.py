import asyncio

from nique import GroupAccount, Nique, Router


async def main() -> None:
    app = Nique()
    app.include_router(Router())
    app.add_account(GroupAccount(name="community", token="YOUR_GROUP_TOKEN", group_id=123))
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
