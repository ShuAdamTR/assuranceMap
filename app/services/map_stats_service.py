"""Evren haritası özet istatistikleri."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class MapStats:
    total: int
    reviewed: int
    rate_pct: int

    @property
    def rate_label(self) -> str:
        return f"%{self.rate_pct}"


def compute_map_stats(cells: Sequence[object]) -> MapStats:
    """
    cells: .has_reviews (bool) veya .color / .review_count ile incelenen tespiti.

    Prefer .has_reviews; fallback: color != never gray handled by caller via has_reviews.
    """
    total = len(cells)
    reviewed = sum(1 for c in cells if getattr(c, "has_reviews", False))
    rate = int(round(100 * reviewed / total)) if total else 0
    return MapStats(total=total, reviewed=reviewed, rate_pct=rate)
