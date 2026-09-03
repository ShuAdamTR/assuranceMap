from __future__ import annotations

from datetime import date

import streamlit as st

from app.components.detail_modal import show_entity_detail_dialog
from app.components.entity_grid import EntityCardData, render_entity_grid
from app.components.filters import render_filters
from app.components.kpi_cards import render_kpi_cards
from app.config.field_keys import FIELD_RISK_LEVEL
from app.database.session import session_scope
from app.repositories.review_repo import ReviewRepository
from app.repositories.universe_repo import UniverseRepository
from app.services.field_option_service import FieldOptionService
from app.services.kpi_service import compute_kpis, get_validity_years
from app.services.review_date_service import get_last_audit_date
from app.services.status_color_service import resolve_status


def render() -> None:
    st.markdown('<div class="am-page-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="am-page-sub">Evren bazlı inceleme durumu ve entity kartları</div>',
        unsafe_allow_html=True,
    )

    with session_scope() as session:
        filters = render_filters(session)
        validity = get_validity_years(session)
        kpi = compute_kpis(session, filters.universe_type)
        render_kpi_cards(kpi, validity)

        entities = UniverseRepository(session).list_by_type(
            filters.universe_type, active_only=True
        )
        options = FieldOptionService(session)
        review_repo = ReviewRepository(session)
        as_of = date.today()

        cards: list[EntityCardData] = []
        for entity in entities:
            last = get_last_audit_date(session, entity.id)
            status = resolve_status(last, as_of_date=as_of, validity_years=validity)
            reviews = review_repo.list_by_universe(entity.id)
            latest = reviews[0] if reviews else None
            risk_level = latest.risk_level if latest else None
            risk_label = (
                options.resolve_label(FIELD_RISK_LEVEL, risk_level) if risk_level else None
            )

            # Filters (AND)
            if filters.color_status and status.value != filters.color_status:
                continue
            if filters.entity_name and filters.entity_name.lower() not in entity.name.lower():
                continue
            if filters.search and filters.search.lower() not in entity.name.lower():
                # also search subjects
                subjects = " ".join(r.review_subject for r in reviews)
                if filters.search.lower() not in subjects.lower():
                    continue
            if filters.review_subject:
                if not any(
                    filters.review_subject.lower() in r.review_subject.lower() for r in reviews
                ):
                    continue
            if filters.risk_level:
                if not any(r.risk_level == filters.risk_level for r in reviews):
                    continue
            if filters.assurance_level:
                if not any(r.assurance_level == filters.assurance_level for r in reviews):
                    continue
            if filters.unit:
                if not any(r.unit == filters.unit for r in reviews):
                    continue

            cards.append(
                EntityCardData(
                    id=entity.id,
                    name=entity.name,
                    status=status,
                    last_date=last,
                    risk_level=risk_level,
                    risk_label=risk_label,
                )
            )

        nav_ids = [c.id for c in cards]
        st.session_state["entity_nav_ids"] = nav_ids
        name_map = {c.id: c.name for c in cards}

    # Close DB session before dialog mutations (SQLite + nested sessions broke Sil/Düzenle).
    clicked = render_entity_grid(cards)
    if clicked is not None:
        st.session_state["selected_entity_id"] = clicked

    selected = st.session_state.get("selected_entity_id")
    if selected and selected in name_map:
        show_entity_detail_dialog(
            entity_id=selected,
            entity_name=name_map[selected],
            nav_ids=nav_ids,
        )
