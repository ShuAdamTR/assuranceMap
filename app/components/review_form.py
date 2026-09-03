from __future__ import annotations

from datetime import date

import streamlit as st

from app.config.field_keys import (
    FIELD_ASSURANCE_LEVEL,
    FIELD_EXAMINATION_DEPTH,
    FIELD_KEY_LABELS,
    FIELD_REVIEW_STATUS,
    FIELD_RISK_LEVEL,
    FIELD_UNIT,
)
from app.schemas.review import ReviewUpdate
from app.services.field_option_service import FieldOptionService
from app.services.review_service import ReviewService, ReviewServiceError

_EDIT_SUFFIXES = (
    "_subject",
    "_covered",
    "_own",
    "_unit",
    "_date",
    "_ucount",
    "_status",
    "_assurance",
    "_risk",
    "_depth",
    "_save",
)


def clear_review_edit_keys(key_prefix: str) -> None:
    for suffix in _EDIT_SUFFIXES:
        st.session_state.pop(f"{key_prefix}{suffix}", None)


def _option_index(options: list, current_value: str) -> int:
    for i, opt in enumerate(options):
        if opt.value == current_value:
            return i
    return 0


def option_select_with_default(
    field_key: str,
    options: list,
    *,
    current_value: str | None,
    key: str,
    label: str | None = None,
) -> str | None:
    display_label = label or FIELD_KEY_LABELS.get(field_key, field_key)
    if not options:
        st.warning(f"'{display_label}' için Ayarlar'da aktif seçenek yok.")
        return None
    labels = [o.label for o in options]
    values = [o.value for o in options]
    # Prefer session state if user already changed the widget
    if key not in st.session_state:
        st.session_state[key] = _option_index(options, current_value or "")
    idx = st.selectbox(
        display_label,
        range(len(labels)),
        format_func=lambda i: labels[i],
        key=key,
    )
    return values[idx]


def render_review_edit_form(
    session,
    review,
    *,
    key_prefix: str,
    commit: bool = False,
) -> bool:
    """Edit form for an existing review. Returns True if saved successfully."""
    options = FieldOptionService(session)
    units = options.list_active(FIELD_UNIT)
    statuses = options.list_active(FIELD_REVIEW_STATUS)
    assurances = options.list_active(FIELD_ASSURANCE_LEVEL)
    risks = options.list_active(FIELD_RISK_LEVEL)
    depths = options.list_active(FIELD_EXAMINATION_DEPTH)

    def _ensure(opts: list, field_key: str, value: str) -> list:
        if any(o.value == value for o in opts):
            return opts
        found = options.repo.find(field_key, value)
        if found:
            return [found] + opts
        return opts

    units = _ensure(units, FIELD_UNIT, review.unit)
    statuses = _ensure(statuses, FIELD_REVIEW_STATUS, review.review_status)
    assurances = _ensure(assurances, FIELD_ASSURANCE_LEVEL, review.assurance_level)
    risks = _ensure(risks, FIELD_RISK_LEVEL, review.risk_level)
    depths = _ensure(depths, FIELD_EXAMINATION_DEPTH, review.examination_depth)

    subject_key = f"{key_prefix}_subject"
    covered_key = f"{key_prefix}_covered"
    own_key = f"{key_prefix}_own"
    date_key = f"{key_prefix}_date"
    ucount_key = f"{key_prefix}_ucount"

    if subject_key not in st.session_state:
        st.session_state[subject_key] = review.review_subject
    if covered_key not in st.session_state:
        st.session_state[covered_key] = int(review.covered_decision_count)
    if own_key not in st.session_state:
        st.session_state[own_key] = review.decision_ownership or ""
    if date_key not in st.session_state:
        st.session_state[date_key] = review.review_date
    if ucount_key not in st.session_state:
        st.session_state[ucount_key] = review.unit_decision_counts or ""

    subject = st.text_input("İnceleme Konusu", key=subject_key)
    covered = st.number_input(
        "Kapsama Alınan Karar Sayısı",
        min_value=0,
        step=1,
        key=covered_key,
    )
    ownership = st.text_input("Karar Sahipliği", key=own_key)
    unit = option_select_with_default(
        FIELD_UNIT, units, current_value=review.unit, key=f"{key_prefix}_unit"
    )
    review_date = st.date_input("İnceleme Tarihi", key=date_key)
    unit_counts = st.text_area("Birim Karar Sayıları", key=ucount_key)
    status = option_select_with_default(
        FIELD_REVIEW_STATUS,
        statuses,
        current_value=review.review_status,
        key=f"{key_prefix}_status",
    )
    assurance = option_select_with_default(
        FIELD_ASSURANCE_LEVEL,
        assurances,
        current_value=review.assurance_level,
        key=f"{key_prefix}_assurance",
    )
    risk = option_select_with_default(
        FIELD_RISK_LEVEL,
        risks,
        current_value=review.risk_level,
        key=f"{key_prefix}_risk",
    )
    depth = option_select_with_default(
        FIELD_EXAMINATION_DEPTH,
        depths,
        current_value=review.examination_depth,
        key=f"{key_prefix}_depth",
    )

    st.caption("Son Denetim/Kontrol Tarihi otomatik hesaplanır; burada girilmez.")

    if st.button("Değişiklikleri kaydet", key=f"{key_prefix}_save", type="primary"):
        if not all([subject, unit, status, assurance, risk, depth]):
            st.error("Zorunlu alanları doldurun.")
            return False
        try:
            ReviewService(session).update(
                review.id,
                ReviewUpdate(
                    review_subject=str(subject).strip(),
                    covered_decision_count=int(covered),
                    decision_ownership=ownership or "",
                    unit=unit,
                    review_date=review_date
                    if isinstance(review_date, date)
                    else review.review_date,
                    unit_decision_counts=unit_counts or "",
                    review_status=status,
                    assurance_level=assurance,
                    risk_level=risk,
                    examination_depth=depth,
                ),
            )
            if commit:
                session.commit()
            return True
        except ReviewServiceError as exc:
            st.error(str(exc))
            return False
    return False
