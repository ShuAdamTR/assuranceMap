from __future__ import annotations

import streamlit as st

NAV_ITEMS = [
    ("dashboard", "Dashboard"),
    ("map", "Harita"),
    ("data_entry", "Veri Girişi"),
    ("universe_admin", "Evren Yönetimi"),
    ("excel_import", "Excel Import"),
    ("settings", "Ayarlar"),
]


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown('<div class="am-brand">assuranceMap</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="am-brand-sub">İç Denetim İnceleme Haritası</div>',
            unsafe_allow_html=True,
        )
        labels = [label for _, label in NAV_ITEMS]
        keys = [key for key, _ in NAV_ITEMS]
        current = st.session_state.get("nav_page", "dashboard")
        if current not in keys:
            current = "dashboard"
        default_idx = keys.index(current)
        choice = st.radio(
            "Navigasyon",
            labels,
            index=default_idx,
            label_visibility="collapsed",
        )
        page = keys[labels.index(choice)]
        st.session_state["nav_page"] = page
        st.divider()
        st.caption("Kurumsal iç uygulama · v1.0")
    return page
