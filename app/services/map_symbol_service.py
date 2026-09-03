"""Evren haritası sembol kuralları (Birim → Uyum/Denetim)."""

from __future__ import annotations

from datetime import date
from typing import Mapping, Sequence

from app.config.field_keys import (
    ACTIVITY_DENETIM,
    ACTIVITY_UYUM,
    MAP_SYMBOL_BOTH_OLD,
    MAP_SYMBOL_BOTH_RECENT,
    MAP_SYMBOL_DENETIM_OLD,
    MAP_SYMBOL_DENETIM_RECENT,
    MAP_SYMBOL_UYUM_OLD,
    MAP_SYMBOL_UYUM_RECENT,
    MAP_WINDOW_YEARS,
)
from app.services.map_color_service import filter_reviews_by_unit
from app.utils.dates import is_expired


def _in_window(review_date: date, as_of: date) -> bool:
    return not is_expired(review_date, as_of, MAP_WINDOW_YEARS)


def resolve_map_symbol(
    reviews: Sequence[object],
    unit_activity_map: Mapping[str, str],
    *,
    as_of: date | None = None,
    unit_filter: str | None = None,
) -> str:
    """
    Entity incelemelerine göre önek sembolü (yoksa boş string).

    unit_activity_map: birim kodu → uyum|denetim
    unit_filter: yalnızca o birimin incelemeleri (KBU/KBD) dikkate alınır.
    """
    as_of = as_of or date.today()
    reviews = filter_reviews_by_unit(reviews, unit_filter)
    if not reviews:
        return ""

    def _activity(unit: str) -> str | None:
        if unit in unit_activity_map:
            return unit_activity_map[unit]
        for key, act in unit_activity_map.items():
            if key.lower() == unit.lower():
                return act
        return None

    recent_uyum = False
    recent_denetim = False
    old_uyum = False
    old_denetim = False

    for r in reviews:
        act = _activity(getattr(r, "unit", "") or "")
        if act is None:
            continue
        if _in_window(r.review_date, as_of):
            if act == ACTIVITY_UYUM:
                recent_uyum = True
            elif act == ACTIVITY_DENETIM:
                recent_denetim = True
        else:
            if act == ACTIVITY_UYUM:
                old_uyum = True
            elif act == ACTIVITY_DENETIM:
                old_denetim = True

    if recent_uyum and recent_denetim:
        return MAP_SYMBOL_BOTH_RECENT
    if recent_uyum:
        return MAP_SYMBOL_UYUM_RECENT
    if recent_denetim:
        return MAP_SYMBOL_DENETIM_RECENT
    if old_uyum and old_denetim:
        return MAP_SYMBOL_BOTH_OLD
    if old_uyum:
        return MAP_SYMBOL_UYUM_OLD
    if old_denetim:
        return MAP_SYMBOL_DENETIM_OLD
    return ""
