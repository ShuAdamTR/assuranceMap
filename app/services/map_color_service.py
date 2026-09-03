"""Evren haritası renk kuralları (sabit 3 yıllık pencere)."""

from __future__ import annotations

from datetime import date
from typing import Sequence

from app.config.field_keys import (
    DEPTH_KISMI,
    DEPTH_TAM,
    MAP_COLOR_MULTI_FULL,
    MAP_COLOR_MULTI_MIXED,
    MAP_COLOR_NEVER,
    MAP_COLOR_OLD_ONLY,
    MAP_COLOR_ONCE_FULL,
    MAP_COLOR_ONCE_PARTIAL,
    MAP_WINDOW_YEARS,
)
from app.utils.dates import is_expired


def _in_window(review_date: date, as_of: date) -> bool:
    return not is_expired(review_date, as_of, MAP_WINDOW_YEARS)


def filter_reviews_by_unit(
    reviews: Sequence[object],
    unit_filter: str | None,
) -> list[object]:
    """
    unit_filter:
      None / all / hepsi → tüm incelemeler
      KBU / KBD → yalnızca o birim
      both / KBD-KBU / KBU-KBD → yalnızca her iki birimin de kaydı varsa
        KBU+KBD incelemeleri; yoksa boş liste
    """
    if not unit_filter or unit_filter in {"all", "hepsi", "tumu"}:
        return list(reviews)

    key = unit_filter.strip().casefold().replace(" ", "").replace("_", "-")
    if key in {"both", "kbd-kbu", "kbu-kbd", "kbdkbu", "kbukbd"}:
        by_unit: dict[str, list[object]] = {"kbu": [], "kbd": []}
        for r in reviews:
            u = (getattr(r, "unit", "") or "").strip().casefold()
            if u in by_unit:
                by_unit[u].append(r)
        if by_unit["kbu"] and by_unit["kbd"]:
            return by_unit["kbu"] + by_unit["kbd"]
        return []

    return [
        r
        for r in reviews
        if (getattr(r, "unit", "") or "").strip().casefold() == key
    ]


def resolve_map_color(
    reviews: Sequence[object],
    *,
    as_of: date | None = None,
    unit_filter: str | None = None,
) -> str:
    """
    Entity'nin incelemelerine göre harita arka plan rengi.

    Her review: .review_date (date), .examination_depth (str: tam|kismi)
    unit_filter: yalnızca o birimin incelemeleri (KBU/KBD) veya
    her iki birimin de incelediği kayıtlar (KBD-KBU).
    """
    as_of = as_of or date.today()
    scoped = filter_reviews_by_unit(reviews, unit_filter)
    if not scoped:
        return MAP_COLOR_NEVER

    recent = [r for r in scoped if _in_window(r.review_date, as_of)]
    if not recent:
        return MAP_COLOR_OLD_ONLY

    n = len(recent)
    depths = [getattr(r, "examination_depth", "") or "" for r in recent]
    all_full = all(d == DEPTH_TAM for d in depths)
    any_full = any(d == DEPTH_TAM for d in depths)
    any_partial = any(d == DEPTH_KISMI for d in depths)

    if n >= 2:
        if all_full:
            return MAP_COLOR_MULTI_FULL
        if any_full and any_partial:
            return MAP_COLOR_MULTI_MIXED
        # ≥2 hepsi kısmi → karışık yeşile yakın ton
        return MAP_COLOR_MULTI_MIXED

    # n == 1
    if depths[0] == DEPTH_TAM:
        return MAP_COLOR_ONCE_FULL
    return MAP_COLOR_ONCE_PARTIAL
