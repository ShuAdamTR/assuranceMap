from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.config.settings import PROJECT_ROOT


def load_app_css() -> None:
    css_path = PROJECT_ROOT / "assets" / "css" / "app.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
