from __future__ import annotations

from pydantic import Field

from nique.shared.exceptions import NiqueError
from nique.shared.models import VKResponseModel


class VKRequestParameter(VKResponseModel):
    key: str
    value: str


class VKErrorPayload(VKResponseModel):
    error_code: int
    error_msg: str
    request_params: list[VKRequestParameter] = Field(default_factory=list[VKRequestParameter])
    redirect_uri: str | None = None
    captcha_sid: str | None = None
    captcha_img: str | None = None


class VKError(NiqueError):
    """Base exception for VK protocol and API failures."""


class VKApiError(VKError):
    """VK returned a structured API error payload."""

    def __init__(self, payload: VKErrorPayload) -> None:
        self.payload = payload
        super().__init__(f"VK API error {payload.error_code}: {payload.error_msg}")


class VKRateLimitError(VKApiError):
    """VK rejected a request because an API rate limit was reached."""


class VKAuthorizationError(VKApiError):
    """VK rejected or expired the access token."""
