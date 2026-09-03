from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FieldOptionCreate(BaseModel):
    field_key: str
    value: str = Field(min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=255)
    sort_order: int = 0


class FieldOptionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    sort_order: int | None = None
    is_active: bool | None = None


class FieldOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_key: str
    value: str
    label: str
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
