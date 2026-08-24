from __future__ import annotations

from pydantic import ConfigDict, Field

from nique.shared.models import NiqueModel


class NiqueSettings(NiqueModel):
    """Canonical application settings; no environment is read implicitly."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    vk_api_version: str = "5.199"
    request_timeout: float = Field(default=15.0, gt=0)
    long_poll_wait: int = Field(default=25, ge=1, le=90)
    event_queue_size: int = Field(default=1000, ge=1)
    max_concurrent_logins: int = Field(default=2, ge=1)
