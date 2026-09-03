from __future__ import annotations

from datetime import date

import streamlit as st

from app.components.detail_modal import show_entity_detail_dialog
from app.components.map_grid import MapCellData, render_map_legend, render_map_section
from app.config.field_keys import UNIVERSE_TYPE_LABELS, UniverseType
from app.database.session import session_scope
from app.repositories.review_repo import ReviewRepository
from app.repositories.universe_repo import UniverseRepository
from app.services.map_color_service import filter_reviews_by_unit, resolve_map_color
from app.services.map_symbol_service import resolve_map_symbol
from app.services.settings_service import AppSettingsService

# Harita birim filtresi: Hepsi / KBD / KBU / KBD-KBU
_UNIT_FILTER_OPTIONS = [
    ("all", "Hepsi"),
    ("KBD", "KBD"),
    ("KBU", "KBU"),
    ("KBD-KBU", "KBD-KBU"),
]


def _build_cells(
    session,
    universe_type: str,
    *,
    as_of: date,
    unit_map: dict[str, str],
    unit_filter: str | None,
) -> list[MapCellData]:
    entities = UniverseRepository(session).list_by_type(
        universe_type, active_only=True
    )
    review_repo = ReviewRepository(session)
    cells: list[MapCellData] = []
    for entity in entities:
        reviews = review_repo.list_by_universe(entity.id)
        scoped = filter_reviews_by_unit(reviews, unit_filter)
        color = resolve_map_color(
            reviews, as_of=as_of, unit_filter=unit_filter
        )
        symbol = resolve_map_symbol(
            reviews, unit_map, as_of=as_of, unit_filter=unit_filter
        )
        last = max((r.review_date for r in scoped), default=None)
        cells.append(
            MapCellData(
                id=entity.id,
                name=entity.name,
                symbol=symbol,
                color=color,
                has_reviews=bool(scoped),
                review_count=len(scoped),
                last_date=last.isoformat() if last else None,
            )
        )
    cells.sort(key=lambda c: c.name.casefold())
    return cells


def render() -> None:
    st.markdown('<div class="am-page-title">Evren Haritası</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="am-page-sub">'
        "İştirak / Müdürlük / Ürün kapsam haritası — renk (derinlik & sıklık) "
        "ve sembol (Uyum / Denetim, son 3 yıl). "
        "Hücreye gelince özet, tıklayınca detay popup."
        "</div>",
        unsafe_allow_html=True,
    )

    if "map_entity" in st.query_params:
        del st.query_params["map_entity"]

    view_labels = ["Tümü"] + [UNIVERSE_TYPE_LABELS[t.value] for t in UniverseType]
    view_keys = ["all"] + [t.value for t in UniverseType]
    unit_labels = [label for _, label in _UNIT_FILTER_OPTIONS]
    unit_keys = [key for key, _ in _UNIT_FILTER_OPTIONS]

    col_view, col_unit = st.columns(2)
    with col_view:
        choice = st.radio(
            "Görünüm",
            view_labels,
            horizontal=True,
            key="map_view_mode",
        )
    with col_unit:
        unit_choice = st.radio(
            "Birim (Hepsi / KBD / KBU / KBD-KBU)",
            unit_labels,
            horizontal=True,
            key="map_unit_filter_v2",
            help=(
                "Hepsi: tüm incelemeler. "
                "KBD veya KBU: yalnızca o birim. "
                "KBD-KBU: her iki birimin de incelediği kayıtlar (örtüşme)."
            ),
        )
    view_key = view_keys[view_labels.index(choice)]
    unit_filter = unit_keys[unit_labels.index(unit_choice)]
    if unit_filter == "all":
        unit_filter = None

    as_of = date.today()
    sections: list[tuple[str, list[MapCellData]]] = []
    name_map: dict[int, str] = {}
    nav_ids: list[int] = []

    with session_scope() as session:
        unit_map = AppSettingsService(session).get_unit_activity_map()
        types = (
            [t.value for t in UniverseType]
            if view_key == "all"
            else [view_key]
        )
        for ut in types:
            cells = _build_cells(
                session,
                ut,
                as_of=as_of,
                unit_map=unit_map,
                unit_filter=unit_filter,
            )
            sections.append((ut, cells))
            for c in cells:
                name_map[c.id] = c.name
                nav_ids.append(c.id)

    clicked: int | None = None
    for ut, cells in sections:
        selected = render_map_section(
            universe_type=ut,
            cells=cells,
            key_prefix=f"map_{ut}",
        )
        if selected is not None:
            clicked = selected
        st.markdown("")

    if clicked is not None:
        st.session_state["selected_entity_id"] = clicked

    selected = st.session_state.get("selected_entity_id")
    if selected and selected in name_map:
        show_entity_detail_dialog(
            entity_id=selected,
            entity_name=name_map[selected],
            nav_ids=nav_ids,
        )

    st.divider()
    render_map_legend()
