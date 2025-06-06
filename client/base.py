import asyncio
from typing import Any, Dict, Literal, Optional

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

        self._is_group_token: Optional[bool] = None
        self._lp_data: Optional[dict] = None

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

                return data.get("response", {})

            except (asyncio.TimeoutError, niquests.exceptions.Timeout) as e:
                logger.warning(f"Attempt {attempt} failed due to network error: {e}")
                if attempt == self.max_retries:
                    logger.error(f"Max retries reached for method {method}")
                    raise
                await asyncio.sleep(1 * attempt)
            except Exception as e:
                logger.error(e, exc_info=True)
                raise

    # TODO: потом перенести в другой модуль
    async def get_message_by_id(
        self, message_id: int, extended: int = 1
    ) -> dict[str, Any]:
        params = {
            "message_ids": str(message_id),
            "extended": str(extended),
        }
        response = await self.request("messages.getById", params)
        if response.get("items"):
            return response["items"][0]
        else:
            return {}

    async def detect_token_type(self) -> Literal["group", "user"]:
        """
        Determines the type of token being used, either 'group' or 'user'.

        This method checks if the token has already been identified. If it has,
        it returns the cached result. If not, it attempts to determine the token
        type by making a request to the VK API. If the request to 'groups.getById'
        succeeds, the token is identified as a 'group' token; otherwise, it is
        considered a 'user' token.

        Returns:
            Literal["group", "user"]: The type of token, either 'group' or 'user'.
        """
        if self._is_group_token is not None:
            return "group" if self._is_group_token else "user"

        try:
            await self.request("groups.getById", {})
            self._is_group_token = True
        except Exception:
            self._is_group_token = False

        return "group" if self._is_group_token else "user"

    async def init_long_poll(self):
        """
        Initializes long poll server data for the token.

        :return: None
        """
        token_type = await self.detect_token_type()

        if token_type == "group":
            group_id = (await self.request("groups.getById", {}))[0]["id"]
            data = await self.request(
                "groups.getLongPollServer", {"group_id": group_id}
            )
        else:
            data = await self.request("messages.getLongPollServer", {"lp_version": 3})

        self._lp_data = {
            "server": data["server"],
            "key": data["key"],
            "ts": data["ts"],
        }

    async def get_long_poll_events(self) -> list[dict] | list[list]:
        """Retrieves long poll events from the long poll server.

        If the long poll server data has not been initialized yet, it is
        initialized before retrieving events. If the initialization fails,
        the function will retry until the server data is initialized.

        If the server returns a failed response, the function will retry if
        the failure is due to an outdated timestamp (failed == 1). Otherwise,
        the function will retry until the server data is reinitialized.

        :return: A list of long poll events. The format of each event depends
            on the type of token used.
        """
        if not self._lp_data:
            await self.init_long_poll()

        params = {
            "act": "a_check",
            "key": self._lp_data["key"],
            "ts": self._lp_data["ts"],
            "wait": 25,
        }

        response = await self.session.get(
            f"https://{self._lp_data['server']}", params=params
        )

        data = response.json()

        if "failed" in data:
            if data["failed"] == 1:
                self._lp_data["ts"] = data["ts"]
            else:
                self._lp_data = None
                return await self.get_long_poll_events()  # retry
        else:
            self._lp_data["ts"] = data["ts"]
            return data["updates"]
