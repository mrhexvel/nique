from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field, SecretStr

from nique.shared.models import NiqueModel


class AccessToken(NiqueModel):
    """Validated VK API access token with redacted representation."""

    value: SecretStr = Field(repr=False)
    user_id: int | None = None
    expires_in: int | None = None
    app_id: int | None = None
    scope: int | None = None
    obtained_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
