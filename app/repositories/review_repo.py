from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate


class ReviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, review_id: int) -> Review | None:
        return self.session.get(Review, review_id)

    def list_by_universe(self, universe_id: int) -> list[Review]:
        stmt = (
            select(Review)
            .where(Review.universe_id == universe_id)
            .order_by(Review.review_date.desc(), Review.id.desc())
        )
        return list(self.session.scalars(stmt).all())

    def list_by_universe_ids(self, universe_ids: list[int]) -> list[Review]:
        if not universe_ids:
            return []
        stmt = (
            select(Review)
            .where(Review.universe_id.in_(universe_ids))
            .order_by(Review.review_date.desc(), Review.id.desc())
        )
        return list(self.session.scalars(stmt).all())

    def max_review_date(self, universe_id: int) -> date | None:
        stmt = select(func.max(Review.review_date)).where(Review.universe_id == universe_id)
        return self.session.scalar(stmt)

    def find_duplicate(
        self,
        universe_id: int,
        review_subject: str,
        review_date: date,
    ) -> Review | None:
        stmt = select(Review).where(
            Review.universe_id == universe_id,
            Review.review_subject == review_subject,
            Review.review_date == review_date,
        )
        return self.session.scalar(stmt)

    def create(self, data: ReviewCreate) -> Review:
        entity = Review(**data.model_dump())
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: Review, data: ReviewUpdate) -> Review:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def delete(self, entity: Review) -> None:
        self.session.delete(entity)
        self.session.flush()

    def is_option_in_use(self, field_key: str, value: str) -> bool:
        column_map = {
            "unit": Review.unit,
            "review_status": Review.review_status,
            "assurance_level": Review.assurance_level,
            "risk_level": Review.risk_level,
            "examination_depth": Review.examination_depth,
        }
        col = column_map.get(field_key)
        if col is None:
            return False
        stmt = select(Review.id).where(col == value).limit(1)
        return self.session.scalar(stmt) is not None
