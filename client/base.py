import asyncio
from typing import Any, Dict, Optional

import niquests
from loguru import logger

from config.logger import setup_logger

setup_logger()


class BaseClient:
    def __init__(
        self,
        access_token: str,
        session: Optional[niquests.AsyncSession] = None,
        api_version: str = "5.199",
        base_url: str = "https://api.vk.com/method",
        max_retries: int = 3,
        timeout_seconds: float = 10.0,
    ):
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.session = session or niquests.AsyncSession()

    async def __aenter__(self) -> "BaseClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.session.aclose()

    async def request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs a request to api.

        :param method: Method name
        :param params: Parameters for the request
        :return: Response of the request
        :raises Exception: If the request failed after max retries
        """
        copied_params = params.copy()
        copied_params["access_token"] = self.access_token
        copied_params["v"] = self.api_version

        for attempt in range(1, self.max_retries + 1):
            try:
                async with asyncio.timeout(self.timeout_seconds):
                    response = await self.session.post(
                        f"{self.base_url}/{method}", data=copied_params
                    )

                    if not response.ok:
                        raise Exception(
                            f"HTTP error {response.status}: {response.reason}"
                        )

                    data = response.json()

                if "error" in data:
                    error = data["error"]
                    raise Exception(
                        f"[VK API] error {error.get('error_code')}: {error.get('error_msg')}"
                    )

                logger.debug(
                    f"Response for method {method} with params {params}: {data}"
                )
                return data.get("response", {})

            except (asyncio.TimeoutError, niquests.exceptions.Timeout) as e:
                logger.warning(f"Attempt {attempt} failed due to network error: {e}")
                if attempt == self.max_retries:
                    logger.error(f"Max retries reached for method {method}")
                    raise
                await asyncio.sleep(1 * attempt)
            except Exception as e:
                logger.error(e)
                raise
