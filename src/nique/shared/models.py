from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NiqueModel(BaseModel):
    """Base model for NiQue-owned data."""

    model_config = ConfigDict(validate_assignment=True)


class VKRequestModel(BaseModel):
    """Strict request payload sent to VK."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class VKObjectModel(BaseModel):
    """Forward-compatible object returned by VK."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class VKResponseModel(VKObjectModel):
    """Base model for a typed VK method response."""
