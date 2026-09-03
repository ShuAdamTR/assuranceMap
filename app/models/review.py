from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    universe_id: Mapped[int] = mapped_column(
        ForeignKey("universes.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    review_subject: Mapped[str] = mapped_column(String(500), nullable=False)
    covered_decision_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    decision_ownership: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    unit: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    unit_decision_counts: Mapped[str] = mapped_column(Text, nullable=False, default="")
    review_status: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    assurance_level: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    examination_depth: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default="tam"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    universe: Mapped["Universe"] = relationship(  # noqa: F821
        "Universe",
        back_populates="reviews",
    )
