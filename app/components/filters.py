from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from app.config.field_keys import (
    FIELD_ASSURANCE_LEVEL,
    FIELD_RISK_LEVEL,
    FIELD_UNIT,
    STATUS_COLOR_LABELS,
    STATUS_GRAY,
    STATUS_GREEN,
    STATUS_ORANGE,
    UNIVERSE_TYPE_LABELS,
    UniverseType,
)
from app.components.option_select import option_select
from app.services.field_option_service import FieldOptionService


@dataclass
class DashboardFilters:
    universe_type: str
    color_status: str | None
    risk_level: str | None
    assurance_level: str | None
    unit: str | None
    review_subject: str
    entity_name: str
    search: str


def render_filters(session) -> DashboardFilters:
    options = FieldOptionService(session)
    types = list(UniverseType)
    type_labels = [UNIVERSE_TYPE_LABELS[t.value] for t in types]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        t_idx = st.selectbox(
            "Evren",
            range(len(types)),
            format_func=lambda i: type_labels[i],
            key="flt_universe",
        )
        universe_type = types[t_idx].value
    with col2:
        status_opts = [None, STATUS_GREEN, STATUS_ORANGE, STATUS_GRAY]
        status_labels = ["Tümü"] + [STATUS_COLOR_LABELS[s] for s in status_opts[1:]]
        s_idx = st.selectbox(
            "Durum",
            range(len(status_opts)),
            format_func=lambda i: status_labels[i],
            key="flt_status",
        )
        color_status = status_opts[s_idx]
    with col3:
        risk = option_select(
            FIELD_RISK_LEVEL,
            options.list_active(FIELD_RISK_LEVEL),
            include_empty=True,
            key="flt_risk",
        )
    with col4:
        assurance = option_select(
            FIELD_ASSURANCE_LEVEL,
            options.list_active(FIELD_ASSURANCE_LEVEL),
            include_empty=True,
            key="flt_assurance",
        )

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        unit = option_select(
            FIELD_UNIT,
            options.list_active(FIELD_UNIT),
            include_empty=True,
            key="flt_unit",
        )
    with col6:
        subject = st.text_input("İnceleme Konusu", key="flt_subject")
    with col7:
        entity_name = st.text_input("Entity adı", key="flt_entity")
    with col8:
        search = st.text_input("Arama", key="flt_search")

    return DashboardFilters(
        universe_type=universe_type,
        color_status=color_status,
        risk_level=risk,
        assurance_level=assurance,
        unit=unit,
        review_subject=subject.strip(),
        entity_name=entity_name.strip(),
        search=search.strip(),
    )
