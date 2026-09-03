from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when launched via `streamlit run app/main.py`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.components.sidebar import render_sidebar
from app.database.engine import init_db
from app.services.import_service import ensure_templates
from app.utils.css_loader import load_app_css
from app.views import (
    dashboard,
    data_entry,
    excel_import,
    map_view,
    settings_page,
    universe_admin,
)

st.set_page_config(
    page_title="assuranceMap",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def bootstrap() -> bool:
    init_db()
    ensure_templates()
    return True


def main() -> None:
    bootstrap()
    load_app_css()
    page = render_sidebar()

    routes = {
        "dashboard": dashboard.render,
        "map": map_view.render,
        "data_entry": data_entry.render,
        "universe_admin": universe_admin.render,
        "excel_import": excel_import.render,
        "settings": settings_page.render,
    }
    routes.get(page, dashboard.render)()


if __name__ == "__main__":
    main()
