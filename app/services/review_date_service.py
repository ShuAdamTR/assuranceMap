from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.repositories.review_repo import ReviewRepository


def get_last_audit_date(session: Session, universe_id: int) -> date | None:
    """Entity için tüm inceleme kayıtlarındaki en büyük İnceleme Tarihi."""
    return ReviewRepository(session).max_review_date(universe_id)


def get_last_audit_dates_bulk(
    session: Session,
    universe_ids: list[int],
) -> dict[int, date | None]:
    repo = ReviewRepository(session)
    result: dict[int, date | None] = {uid: None for uid in universe_ids}
    for uid in universe_ids:
        result[uid] = repo.max_review_date(uid)
    return result
