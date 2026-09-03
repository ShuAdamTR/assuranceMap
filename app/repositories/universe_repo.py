from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.universe import Universe


class UniverseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, universe_id: int) -> Universe | None:
        return self.session.get(Universe, universe_id)

    def list_by_type(
        self,
        universe_type: str,
        *,
        active_only: bool = True,
    ) -> list[Universe]:
        stmt = select(Universe).where(Universe.universe_type == universe_type)
        if active_only:
            stmt = stmt.where(Universe.is_active.is_(True))
        stmt = stmt.order_by(Universe.name.asc())
        return list(self.session.scalars(stmt).all())

    def find_by_name(self, universe_type: str, name: str) -> Universe | None:
        stmt = select(Universe).where(
            Universe.universe_type == universe_type,
            Universe.name == name,
        )
        return self.session.scalar(stmt)

    def create(self, universe_type: str, name: str) -> Universe:
        entity = Universe(universe_type=universe_type, name=name.strip(), is_active=True)
        self.session.add(entity)
        self.session.flush()
        return entity

    def set_active(self, entity: Universe, is_active: bool) -> Universe:
        entity.is_active = is_active
        self.session.flush()
        return entity

    def rename(self, entity: Universe, name: str) -> Universe:
        entity.name = name.strip()
        self.session.flush()
        return entity

    def delete(self, entity: Universe) -> None:
        self.session.delete(entity)
        self.session.flush()

    def count_reviews(self, universe_id: int) -> int:
        from app.models.review import Review

        stmt = select(Review).where(Review.universe_id == universe_id)
        return len(list(self.session.scalars(stmt).all()))
