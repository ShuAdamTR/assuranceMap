from __future__ import annotations

import streamlit as st

from app.config.field_keys import FIELD_KEY_LABELS


def option_select(
    field_key: str,
    options: list,
    *,
    label: str | None = None,
    key: str | None = None,
    include_empty: bool = False,
    empty_label: str = "Tümü",
) -> str | None:
    """Settings-driven selectbox. `options` = FieldOption listesi."""
    display_label = label or FIELD_KEY_LABELS.get(field_key, field_key)
    labels = [o.label for o in options]
    values = [o.value for o in options]
    if include_empty:
        labels = [empty_label] + labels
        values = [None] + values  # type: ignore[list-item]
    if not labels:
        st.warning(f"'{display_label}' için Ayarlar'da aktif seçenek yok.")
        return None
    idx = st.selectbox(
        display_label,
        range(len(labels)),
        format_func=lambda i: labels[i],
        key=key,
    )
    return values[idx]
