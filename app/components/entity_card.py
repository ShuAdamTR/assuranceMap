from __future__ import annotations

from datetime import date

import streamlit as st

from app.config.field_keys import STATUS_COLOR_LABELS
from app.services.status_color_service import EntityColorStatus


def render_entity_card(
    *,
    entity_id: int,
    name: str,
    status: EntityColorStatus,
    last_date: date | None,
    risk_level: str | None,
    risk_label: str | None,
) -> bool:
    """Returns True if card button clicked."""
    status_key = status.value
    last_txt = last_date.isoformat() if last_date else "—"
    risk_txt = risk_label or risk_level or "—"
    tip = f"{name} | {STATUS_COLOR_LABELS.get(status_key, status_key)} | Son: {last_txt} | Risk: {risk_txt}"

    st.markdown(
        f"""
        <div class="am-card status-{status_key}" title="{tip}">
          <span class="am-badge {status_key}">{STATUS_COLOR_LABELS.get(status_key, status_key)}</span>
          <div class="name">{name}</div>
          <div class="meta">Son inceleme: {last_txt}<br/>Risk: {risk_txt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.button("Detay", key=f"card_btn_{entity_id}", use_container_width=True)
