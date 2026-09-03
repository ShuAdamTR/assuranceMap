from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.field_keys import FIELD_KEYS, FIELD_KEY_LABELS
from app.models.field_option import FieldOption
from app.repositories.field_option_repo import FieldOptionRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.field_option import FieldOptionCreate, FieldOptionUpdate


class FieldOptionServiceError(Exception):
    pass


class FieldOptionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = FieldOptionRepository(session)
        self.review_repo = ReviewRepository(session)

    def list_active(self, field_key: str) -> list[FieldOption]:
        self._validate_key(field_key)
        return self.repo.list_by_key(field_key, active_only=True)

    def list_all(self, field_key: str) -> list[FieldOption]:
        self._validate_key(field_key)
        return self.repo.list_by_key(field_key, active_only=False)

    def assert_allowed(self, field_key: str, value: str) -> None:
        self._validate_key(field_key)
        option = self.repo.find(field_key, value)
        label = FIELD_KEY_LABELS.get(field_key, field_key)
        if option is None or not option.is_active:
            raise FieldOptionServiceError(
                f"'{value}' değeri '{label}' alanı için Ayarlar'da tanımlı/aktif değil."
            )

    def create(self, data: FieldOptionCreate) -> FieldOption:
        self._validate_key(data.field_key)
        value = data.value.strip()
        if not value:
            raise FieldOptionServiceError("Değer boş olamaz.")
        if self.repo.find(data.field_key, value) is not None:
            raise FieldOptionServiceError(f"'{value}' zaten mevcut.")
        return self.repo.create(data)

    def update(self, option_id: int, data: FieldOptionUpdate) -> FieldOption:
        entity = self._require(option_id)
        if data.is_active is False:
            active_count = self.repo.count_active(entity.field_key)
            if entity.is_active and active_count <= 1:
                raise FieldOptionServiceError(
                    "Her alanda en az bir aktif seçenek kalmalıdır."
                )
        return self.repo.update(entity, data)

    def deactivate(self, option_id: int) -> FieldOption:
        return self.update(option_id, FieldOptionUpdate(is_active=False))

    def resolve_label(self, field_key: str, value: str) -> str:
        option = self.repo.find(field_key, value)
        if option is None:
            return value
        return option.label

    def _require(self, option_id: int) -> FieldOption:
        entity = self.repo.get(option_id)
        if entity is None:
            raise FieldOptionServiceError("Seçenek bulunamadı.")
        return entity

    @staticmethod
    def _validate_key(field_key: str) -> None:
        if field_key not in FIELD_KEYS:
            raise FieldOptionServiceError(f"Geçersiz alan anahtarı: {field_key}")
