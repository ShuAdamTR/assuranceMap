from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.field_keys import FIELD_KEYS, UNIVERSE_TYPE_LABELS, UniverseType
from app.models.universe import Universe
from app.repositories.universe_repo import UniverseRepository
from app.schemas.universe import UniverseCreate, UniverseUpdate


class UniverseServiceError(Exception):
    pass


class UniverseService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = UniverseRepository(session)

    def list(self, universe_type: str, *, active_only: bool = True) -> list[Universe]:
        self._validate_type(universe_type)
        return self.repo.list_by_type(universe_type, active_only=active_only)

    def create(self, data: UniverseCreate) -> Universe:
        self._validate_type(data.universe_type)
        name = data.name.strip()
        if not name:
            raise UniverseServiceError("Evren adı boş olamaz.")
        existing = self.repo.find_by_name(data.universe_type, name)
        if existing is not None:
            raise UniverseServiceError(
                f"Bu evren tipinde '{name}' zaten tanımlı."
            )
        return self.repo.create(data.universe_type, name)

    def deactivate(self, universe_id: int) -> Universe:
        entity = self._require(universe_id)
        return self.repo.set_active(entity, False)

    def activate(self, universe_id: int) -> Universe:
        entity = self._require(universe_id)
        return self.repo.set_active(entity, True)

    def rename(self, universe_id: int, new_name: str) -> Universe:
        entity = self._require(universe_id)
        name = new_name.strip()
        if not name:
            raise UniverseServiceError("Evren adı boş olamaz.")
        existing = self.repo.find_by_name(entity.universe_type, name)
        if existing is not None and existing.id != universe_id:
            raise UniverseServiceError(
                f"Bu evren tipinde '{name}' zaten tanımlı."
            )
        return self.repo.rename(entity, name)

    def update(self, universe_id: int, data: UniverseUpdate) -> Universe:
        entity = self._require(universe_id)
        if data.name is not None:
            self.rename(universe_id, data.name)
            entity = self._require(universe_id)
        if data.is_active is not None:
            entity = self.repo.set_active(entity, data.is_active)
        return entity

    def delete(self, universe_id: int) -> None:
        entity = self._require(universe_id)
        if self.repo.count_reviews(universe_id) > 0:
            raise UniverseServiceError(
                "İnceleme kaydı olan entity hard-delete edilemez. Pasifleştirin."
            )
        self.repo.delete(entity)

    def _require(self, universe_id: int) -> Universe:
        entity = self.repo.get(universe_id)
        if entity is None:
            raise UniverseServiceError("Evren kaydı bulunamadı.")
        return entity

    @staticmethod
    def _validate_type(universe_type: str) -> None:
        valid = {t.value for t in UniverseType}
        if universe_type not in valid:
            raise UniverseServiceError(
                f"Geçersiz evren tipi. Geçerli: {', '.join(UNIVERSE_TYPE_LABELS.values())}"
            )
