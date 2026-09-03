from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.field_keys import (
    FIELD_ASSURANCE_LEVEL,
    FIELD_EXAMINATION_DEPTH,
    FIELD_REVIEW_STATUS,
    FIELD_RISK_LEVEL,
    FIELD_UNIT,
)
from app.models.review import Review
from app.repositories.review_repo import ReviewRepository
from app.repositories.universe_repo import UniverseRepository
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.field_option_service import FieldOptionService, FieldOptionServiceError


class ReviewServiceError(Exception):
    pass


class ReviewService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = ReviewRepository(session)
        self.universe_repo = UniverseRepository(session)
        self.options = FieldOptionService(session)

    def list_for_universe(self, universe_id: int) -> list[Review]:
        return self.repo.list_by_universe(universe_id)

    def create(self, data: ReviewCreate) -> Review:
        universe = self.universe_repo.get(data.universe_id)
        if universe is None or not universe.is_active:
            raise ReviewServiceError("Aktif evren kaydı bulunamadı.")
        self._assert_whitelists(data)
        dup = self.repo.find_duplicate(
            data.universe_id, data.review_subject.strip(), data.review_date
        )
        if dup is not None:
            raise ReviewServiceError(
                "Aynı entity, konu ve tarih için kayıt zaten var (duplicate)."
            )
        payload = data.model_copy(
            update={"review_subject": data.review_subject.strip()}
        )
        return self.repo.create(payload)

    def update(self, review_id: int, data: ReviewUpdate) -> Review:
        entity = self.repo.get(review_id)
        if entity is None:
            raise ReviewServiceError("İnceleme kaydı bulunamadı.")
        merged = ReviewCreate(
            universe_id=entity.universe_id,
            review_subject=data.review_subject or entity.review_subject,
            covered_decision_count=(
                data.covered_decision_count
                if data.covered_decision_count is not None
                else entity.covered_decision_count
            ),
            decision_ownership=(
                data.decision_ownership
                if data.decision_ownership is not None
                else entity.decision_ownership
            ),
            unit=data.unit or entity.unit,
            review_date=data.review_date or entity.review_date,
            unit_decision_counts=(
                data.unit_decision_counts
                if data.unit_decision_counts is not None
                else entity.unit_decision_counts
            ),
            review_status=data.review_status or entity.review_status,
            assurance_level=data.assurance_level or entity.assurance_level,
            risk_level=data.risk_level or entity.risk_level,
            examination_depth=data.examination_depth or entity.examination_depth,
        )
        self._assert_whitelists(merged)
        return self.repo.update(entity, data)

    def delete(self, review_id: int) -> None:
        entity = self.repo.get(review_id)
        if entity is None:
            raise ReviewServiceError("İnceleme kaydı bulunamadı.")
        self.repo.delete(entity)

    def _assert_whitelists(self, data: ReviewCreate) -> None:
        try:
            self.options.assert_allowed(FIELD_UNIT, data.unit)
            self.options.assert_allowed(FIELD_REVIEW_STATUS, data.review_status)
            self.options.assert_allowed(FIELD_ASSURANCE_LEVEL, data.assurance_level)
            self.options.assert_allowed(FIELD_RISK_LEVEL, data.risk_level)
            self.options.assert_allowed(FIELD_EXAMINATION_DEPTH, data.examination_depth)
        except FieldOptionServiceError as exc:
            raise ReviewServiceError(str(exc)) from exc
