import asyncio
import os
from pathlib import Path
from uuid import UUID

from nique import Nique, UserAccount
from nique.auth import JsonTokenStore, VerificationChallenge, VKApplication, VKUserScope


class ConsoleVerificationProvider:
    async def get_code(self, challenge: VerificationChallenge) -> str:
        return await asyncio.to_thread(
            input,
            f"Enter the {challenge.method.value} verification code: ",
        )


async def main() -> None:
    app = Nique(token_store=JsonTokenStore(Path(".nique/tokens.json")))
    app.add_account(
        UserAccount.from_credentials(
            name="main",
            login=os.environ["NIQUE_VK_LOGIN"],
            password=os.environ["NIQUE_VK_PASSWORD"],
            application=VKApplication(
                app_id=6222115,
                scope=VKUserScope.MESSAGES | VKUserScope.OFFLINE,
            ),
            verification_provider=ConsoleVerificationProvider(),
            id=UUID("d90b6520-30d9-4b48-926c-98f6705996aa"),
        )
    )
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
