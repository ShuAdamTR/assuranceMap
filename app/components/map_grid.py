from __future__ import annotations

from dataclasses import dataclass
from html import escape

import streamlit as st

from app.config.field_keys import (
    MAP_COLOR_LABELS,
    MAP_SYMBOL_LABELS,
    UNIVERSE_TYPE_LABELS,
)
from app.services.map_stats_service import compute_map_stats


@dataclass
class MapCellData:
    id: int
    name: str
    symbol: str
    color: str
    has_reviews: bool
    review_count: int = 0
    last_date: str | None = None


def _cell_label(cell: MapCellData) -> str:
    if cell.symbol:
        return f"{cell.symbol} {cell.name}"
    return cell.name


def _cell_tooltip(cell: MapCellData) -> str:
    color_txt = MAP_COLOR_LABELS.get(cell.color, "Durum bilinmiyor")
    symbol_txt = (
        MAP_SYMBOL_LABELS.get(cell.symbol, "")
        if cell.symbol
        else "Faaliyet sembolü yok"
    )
    lines = [
        cell.name,
        f"Renk: {color_txt}",
        f"Sembol: {symbol_txt}" if symbol_txt else "Sembol: —",
        f"İnceleme sayısı: {cell.review_count}",
    ]
    if cell.last_date:
        lines.append(f"Son inceleme: {cell.last_date}")
    lines.append("Tıklayın → detay popup")
    return "\n".join(lines)


def render_map_legend() -> None:
    st.markdown("#### Renk ve sembol efsanesi")
    st.caption(
        "Renklendirmede öncelikle son 3 yıllık durum dikkate alınır. "
        "Hücreye gelince özet; tıklayınca detay popup açılır."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Renkler**")
        for hex_color, label in MAP_COLOR_LABELS.items():
            st.markdown(
                f'<div class="am-map-legend-row">'
                f'<span class="am-map-swatch" style="background:{hex_color}"></span>'
                f'<span>{label}</span></div>',
                unsafe_allow_html=True,
            )
    with c2:
        st.markdown("**Semboller**")
        for symbol, label in MAP_SYMBOL_LABELS.items():
            st.markdown(f"**{symbol}** — {label}")


def render_map_section(
    *,
    universe_type: str,
    cells: list[MapCellData],
    columns: int = 5,
    key_prefix: str,
) -> int | None:
    """
    Clickable map cells as Streamlit buttons (main app, not iframe).
    Hover: help tooltip. Click: returns entity id for st.dialog popup.
    """
    title = UNIVERSE_TYPE_LABELS.get(universe_type, universe_type)
    stats = compute_map_stats(cells)
    type_noun = {
        "istirak": "iştirak",
        "mudurluk": "müdürlük",
        "urun": "ürün/uygulama",
    }.get(universe_type, "kayıt")

    grid_col, side_col = st.columns([5, 1], gap="small")
    selected_id: int | None = None

    with grid_col:
        st.markdown(
            f'<div class="am-map-header">{escape(title)}</div>',
            unsafe_allow_html=True,
        )
        if not cells:
            st.info("Bu evrende aktif kayıt yok.")
        else:
            style_rules: list[str] = [
                ".am-map-click-grid div[data-testid='stHorizontalBlock']{"
                "gap:1px!important;margin-bottom:1px!important;}",
                ".am-map-click-grid div[data-testid='column']{padding:0!important;}",
                ".am-map-click-grid div[data-testid='stButton']{margin:0!important;}",
            ]
            for cell in cells:
                key = f"{key_prefix}_cell_{cell.id}"
                style_rules.append(
                    f".st-key-{key} button{{"
                    f"background-color:{cell.color}!important;"
                    f"border:1px solid #9ca3af!important;"
                    f"color:#1a1a1a!important;"
                    f"font-size:0.72rem!important;"
                    f"font-weight:500!important;"
                    f"min-height:2.35rem!important;"
                    f"height:auto!important;"
                    f"padding:0.3rem 0.35rem!important;"
                    f"white-space:normal!important;"
                    f"line-height:1.2!important;"
                    f"border-radius:0!important;"
                    f"}}"
                    f".st-key-{key} button:hover{{"
                    f"filter:brightness(0.92);"
                    f"outline:2px solid #1e3a5f!important;"
                    f"outline-offset:-2px;"
                    f"}}"
                )
            st.markdown(
                "<style>" + "".join(style_rules) + "</style>",
                unsafe_allow_html=True,
            )

            with st.container():
                st.markdown(
                    '<div class="am-map-click-grid">',
                    unsafe_allow_html=True,
                )
                for i in range(0, len(cells), columns):
                    row = cells[i : i + columns]
                    cols = st.columns(len(row), gap="small")
                    for col, cell in zip(cols, row):
                        with col:
                            if st.button(
                                _cell_label(cell),
                                key=f"{key_prefix}_cell_{cell.id}",
                                help=_cell_tooltip(cell),
                                use_container_width=True,
                            ):
                                selected_id = cell.id
                st.markdown("</div>", unsafe_allow_html=True)

    with side_col:
        st.markdown(
            '<div class="am-map-total-title">Toplam</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="am-map-total-box">
              <div>Toplam {type_noun}: <strong>{stats.total}</strong></div>
              <div>İncelenen {type_noun}: <strong>{stats.reviewed}</strong></div>
              <div>İncelenme Oranı: <strong>{stats.rate_label}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_id
