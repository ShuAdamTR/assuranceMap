from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settings import AppSetting


class SettingsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, key: str) -> AppSetting | None:
        return self.session.get(AppSetting, key)

    def get_value(self, key: str, default: str | None = None) -> str | None:
        row = self.get(key)
        if row is None:
            return default
        return row.value

    def set_value(self, key: str, value: str) -> AppSetting:
        row = self.get(key)
        if row is None:
            row = AppSetting(key=key, value=value)
            self.session.add(row)
        else:
            row.value = value
        self.session.flush()
        return row

    def list_all(self) -> list[AppSetting]:
        return list(self.session.scalars(select(AppSetting)).all())
