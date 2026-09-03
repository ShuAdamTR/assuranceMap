from __future__ import annotations

import streamlit as st

from app.services.kpi_service import KpiResult


def render_kpi_cards(kpi: KpiResult, validity_years: int) -> None:
    html = f"""
    <div class="am-kpi-row">
      <div class="am-kpi"><div class="label">Toplam Evren</div><div class="value">{kpi.total}</div></div>
      <div class="am-kpi"><div class="label">Güncel İncelenen</div><div class="value">{kpi.current}</div></div>
      <div class="am-kpi"><div class="label">{validity_years}+ Yıl Geçen</div><div class="value">{kpi.overdue}</div></div>
      <div class="am-kpi"><div class="label">Hiç İncelenmeyen</div><div class="value">{kpi.never_reviewed}</div></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
