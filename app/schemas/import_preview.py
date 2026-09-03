from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ImportRowError(BaseModel):
    row_number: int
    field: str | None = None
    message: str


class ImportRowResult(BaseModel):
    row_number: int
    ok: bool
    errors: list[ImportRowError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    universe_name: str | None = None
    review_subject: str | None = None
    review_date: date | None = None
    will_create_entity: bool = False
    payload: dict | None = None


class ImportPreviewResult(BaseModel):
    missing_columns: list[str] = Field(default_factory=list)
    extra_columns: list[str] = Field(default_factory=list)
    rows: list[ImportRowResult] = Field(default_factory=list)
    valid_count: int = 0
    error_count: int = 0
    can_commit: bool = False
    entities_to_create: list[str] = Field(default_factory=list)
    entities_to_reactivate: list[str] = Field(default_factory=list)
    normalize_notes: list[str] = Field(default_factory=list)
