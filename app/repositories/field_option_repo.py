from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.field_option import FieldOption
from app.schemas.field_option import FieldOptionCreate, FieldOptionUpdate


class FieldOptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, option_id: int) -> FieldOption | None:
        return self.session.get(FieldOption, option_id)

    def list_by_key(
        self,
        field_key: str,
        *,
        active_only: bool = False,
    ) -> list[FieldOption]:
        stmt = select(FieldOption).where(FieldOption.field_key == field_key)
        if active_only:
            stmt = stmt.where(FieldOption.is_active.is_(True))
        stmt = stmt.order_by(FieldOption.sort_order.asc(), FieldOption.label.asc())
        return list(self.session.scalars(stmt).all())

    def find(self, field_key: str, value: str) -> FieldOption | None:
        stmt = select(FieldOption).where(
            FieldOption.field_key == field_key,
            FieldOption.value == value,
        )
        return self.session.scalar(stmt)

    def count_active(self, field_key: str) -> int:
        return len(self.list_by_key(field_key, active_only=True))

    def create(self, data: FieldOptionCreate) -> FieldOption:
        entity = FieldOption(
            field_key=data.field_key,
            value=data.value.strip(),
            label=data.label.strip(),
            sort_order=data.sort_order,
            is_active=True,
        )
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: FieldOption, data: FieldOptionUpdate) -> FieldOption:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, key, value)
        self.session.flush()
        return entity
