from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    universe_id: int
    review_subject: str = Field(min_length=1, max_length=500)
    covered_decision_count: int = Field(ge=0)
    decision_ownership: str = Field(default="", max_length=255)
    unit: str = Field(min_length=1, max_length=64)
    review_date: date
    unit_decision_counts: str = ""
    review_status: str = Field(min_length=1, max_length=64)
    assurance_level: str = Field(min_length=1, max_length=64)
    risk_level: str = Field(min_length=1, max_length=64)
    examination_depth: str = Field(min_length=1, max_length=64)


class ReviewUpdate(BaseModel):
    review_subject: str | None = Field(default=None, min_length=1, max_length=500)
    covered_decision_count: int | None = Field(default=None, ge=0)
    decision_ownership: str | None = None
    unit: str | None = None
    review_date: date | None = None
    unit_decision_counts: str | None = None
    review_status: str | None = None
    assurance_level: str | None = None
    risk_level: str | None = None
    examination_depth: str | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    universe_id: int
    review_subject: str
    covered_decision_count: int
    decision_ownership: str
    unit: str
    review_date: date
    unit_decision_counts: str
    review_status: str
    assurance_level: str
    risk_level: str
    examination_depth: str
    created_at: datetime
    updated_at: datetime
