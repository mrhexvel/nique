import asyncio

from nique import Nique, UserAccount


async def main() -> None:
    async with Nique() as app:
        account = await app.create_account(UserAccount(name="sdk", token="YOUR_TOKEN"))
        print(await account.api.users.get(user_ids=[1]))


if __name__ == "__main__":
    asyncio.run(main())
