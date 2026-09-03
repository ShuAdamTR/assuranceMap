from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.field_keys import (
    DEFAULT_UNIT_ACTIVITY_MAP,
    DEFAULT_VALIDITY_YEARS,
    DEPTH_KISMI,
    DEPTH_TAM,
    FIELD_ASSURANCE_LEVEL,
    FIELD_EXAMINATION_DEPTH,
    FIELD_REVIEW_STATUS,
    FIELD_RISK_LEVEL,
    FIELD_UNIT,
    SETTING_UNIT_ACTIVITY_MAP,
    SETTING_VALIDITY_YEARS,
)
from app.database.session import session_scope
from app.models.field_option import FieldOption
from app.models.settings import AppSetting

# Seed: (field_key, value, label, sort_order)
DEFAULT_FIELD_OPTIONS: list[tuple[str, str, str, int]] = [
    (FIELD_UNIT, "KBU", "KBU", 1),
    (FIELD_UNIT, "KBD", "KBD", 2),
    (FIELD_REVIEW_STATUS, "planlandi", "Planlandı", 1),
    (FIELD_REVIEW_STATUS, "devam_ediyor", "Devam Ediyor", 2),
    (FIELD_REVIEW_STATUS, "tamamlandi", "Tamamlandı", 3),
    (FIELD_REVIEW_STATUS, "askida", "Askıda", 4),
    (FIELD_ASSURANCE_LEVEL, "yuksek", "Yüksek", 1),
    (FIELD_ASSURANCE_LEVEL, "makul", "Makul", 2),
    (FIELD_ASSURANCE_LEVEL, "sinirli", "Sınırlı", 3),
    (FIELD_ASSURANCE_LEVEL, "yetersiz", "Yetersiz", 4),
    (FIELD_RISK_LEVEL, "kritik", "Kritik", 1),
    (FIELD_RISK_LEVEL, "yuksek", "Yüksek", 2),
    (FIELD_RISK_LEVEL, "orta", "Orta", 3),
    (FIELD_RISK_LEVEL, "dusuk", "Düşük", 4),
    (FIELD_EXAMINATION_DEPTH, DEPTH_TAM, "Tam", 1),
    (FIELD_EXAMINATION_DEPTH, DEPTH_KISMI, "Kısmi", 2),
]


def seed_defaults(session: Session | None = None) -> None:
    if session is not None:
        _seed(session)
        return
    with session_scope() as s:
        _seed(s)


def _seed(session: Session) -> None:
    existing = session.scalar(
        select(AppSetting).where(AppSetting.key == SETTING_VALIDITY_YEARS)
    )
    if existing is None:
        session.add(
            AppSetting(key=SETTING_VALIDITY_YEARS, value=str(DEFAULT_VALIDITY_YEARS))
        )

    activity_map = session.scalar(
        select(AppSetting).where(AppSetting.key == SETTING_UNIT_ACTIVITY_MAP)
    )
    if activity_map is None:
        session.add(
            AppSetting(
                key=SETTING_UNIT_ACTIVITY_MAP,
                value=json.dumps(DEFAULT_UNIT_ACTIVITY_MAP, ensure_ascii=False),
            )
        )

    for field_key, value, label, sort_order in DEFAULT_FIELD_OPTIONS:
        found = session.scalar(
            select(FieldOption).where(
                FieldOption.field_key == field_key,
                FieldOption.value == value,
            )
        )
        if found is None:
            session.add(
                FieldOption(
                    field_key=field_key,
                    value=value,
                    label=label,
                    sort_order=sort_order,
                    is_active=True,
                )
            )
