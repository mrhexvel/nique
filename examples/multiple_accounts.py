import asyncio

from nique import Nique, UserAccount


async def main() -> None:
    app = Nique()
    app.add_account(UserAccount(name="first", token="FIRST_TOKEN"))
    app.add_account(UserAccount(name="second", token="SECOND_TOKEN"))
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
