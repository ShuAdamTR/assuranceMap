from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import streamlit as st

from app.components.entity_card import render_entity_card
from app.services.status_color_service import EntityColorStatus


@dataclass
class EntityCardData:
    id: int
    name: str
    status: EntityColorStatus
    last_date: date | None
    risk_level: str | None
    risk_label: str | None


def render_entity_grid(cards: list[EntityCardData]) -> int | None:
    if not cards:
        st.info("Filtreye uygun entity bulunamadı.")
        return None

    clicked: int | None = None
    cols_per_row = 3
    for i in range(0, len(cards), cols_per_row):
        row = cards[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, card in zip(cols, row):
            with col:
                if render_entity_card(
                    entity_id=card.id,
                    name=card.name,
                    status=card.status,
                    last_date=card.last_date,
                    risk_level=card.risk_level,
                    risk_label=card.risk_label,
                ):
                    clicked = card.id
    return clicked
