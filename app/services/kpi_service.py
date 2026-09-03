from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.config.field_keys import DEFAULT_VALIDITY_YEARS, SETTING_VALIDITY_YEARS
from app.repositories.settings_repo import SettingsRepository
from app.repositories.universe_repo import UniverseRepository
from app.services.review_date_service import get_last_audit_date
from app.services.status_color_service import EntityColorStatus, resolve_status


@dataclass
class KpiResult:
    total: int
    current: int
    overdue: int
    never_reviewed: int


def get_validity_years(session: Session) -> int:
    raw = SettingsRepository(session).get_value(
        SETTING_VALIDITY_YEARS, str(DEFAULT_VALIDITY_YEARS)
    )
    try:
        return max(1, int(raw or DEFAULT_VALIDITY_YEARS))
    except ValueError:
        return DEFAULT_VALIDITY_YEARS


def compute_kpis(
    session: Session,
    universe_type: str,
    *,
    as_of_date: date | None = None,
) -> KpiResult:
    entities = UniverseRepository(session).list_by_type(universe_type, active_only=True)
    validity = get_validity_years(session)
    as_of = as_of_date or date.today()

    current = overdue = never_reviewed = 0
    for entity in entities:
        last = get_last_audit_date(session, entity.id)
        status = resolve_status(last, as_of_date=as_of, validity_years=validity)
        if status == EntityColorStatus.GREEN:
            current += 1
        elif status == EntityColorStatus.ORANGE:
            overdue += 1
        else:
            never_reviewed += 1

    return KpiResult(
        total=len(entities),
        current=current,
        overdue=overdue,
        never_reviewed=never_reviewed,
    )
