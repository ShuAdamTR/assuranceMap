from __future__ import annotations

from datetime import date
from enum import Enum

from app.config.field_keys import STATUS_GRAY, STATUS_GREEN, STATUS_ORANGE
from app.utils.dates import is_expired


class EntityColorStatus(str, Enum):
    GRAY = STATUS_GRAY
    GREEN = STATUS_GREEN
    ORANGE = STATUS_ORANGE


def resolve_status(
    last_audit_date: date | None,
    *,
    as_of_date: date | None = None,
    validity_years: int = 4,
) -> EntityColorStatus:
    """
    - Hiç inceleme yok → GRAY
    - Son incelemeden validity_years'dan az geçmiş → GREEN
    - validity_years veya daha fazla geçmiş → ORANGE
    """
    as_of = as_of_date or date.today()
    if last_audit_date is None:
        return EntityColorStatus.GRAY
    if is_expired(last_audit_date, as_of, validity_years):
        return EntityColorStatus.ORANGE
    return EntityColorStatus.GREEN
