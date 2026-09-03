from __future__ import annotations

import re
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

# Kullanıcıya gösterilen kabul edilen metin formatları
DATE_FORMAT_HINT = "GG.AA.YYYY veya GG/AA/YYYY (ör. 01.03.2026)"

_ACCEPTED_TEXT_FORMATS = (
    "%d.%m.%Y",
    "%d/%m/%Y",
)


def add_years(d: date, years: int) -> date:
    """Add calendar years; clamp Feb 29 → Feb 28 on non-leap targets."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + years)


def years_elapsed(start: date, end: date) -> float:
    """Approximate years between dates for display; color logic uses add_years."""
    delta = relativedelta(end, start)
    return delta.years + delta.months / 12.0 + delta.days / 365.25


def is_expired(last_date: date, as_of: date, validity_years: int) -> bool:
    """True when as_of is on/after last_date + validity_years (≥ N years → expired)."""
    threshold = add_years(last_date, validity_years)
    return as_of >= threshold


def format_date_tr(d: date | None) -> str:
    if d is None:
        return ""
    return d.strftime("%d.%m.%Y")


def normalize_to_date(value: object) -> date | None:
    """
    Kabul edilen girişler:
    - Excel hücre tarihi (date / datetime)
    - Metin: DD.MM.YYYY veya DD/MM/YYYY

    Diğer metin formatları (YYYY-MM-DD, '1 Ocak 26', yalnız yıl vb.) reddedilir.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none"}:
        return None

    # Zaman eki varsa at (01.03.2026 00:00:00) — yalnızca GG.AA/GG/AA kısmını dene
    if re.match(r"^\d{1,2}[./]\d{1,2}[./]\d{4}\s+", text):
        text = text.split()[0]

    for fmt in _ACCEPTED_TEXT_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def date_parse_error_message(raw: object | None = None) -> str:
    shown = ""
    if raw is not None and str(raw).strip() and str(raw).strip().lower() not in {
        "nan",
        "nat",
        "none",
    }:
        shown = f" (girilen: {str(raw).strip()})"
    return f"Geçersiz tarih formatı{shown}. Kabul edilen: {DATE_FORMAT_HINT}"
