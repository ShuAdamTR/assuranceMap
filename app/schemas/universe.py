from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UniverseCreate(BaseModel):
    universe_type: str
    name: str = Field(min_length=1, max_length=255)


class UniverseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class UniverseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    universe_type: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
