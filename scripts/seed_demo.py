"""Demo seed — örnek evren ve inceleme kayıtları."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database.engine import init_db
from app.database.session import session_scope
from app.schemas.review import ReviewCreate
from app.schemas.universe import UniverseCreate
from app.services.review_service import ReviewService
from app.services.universe_service import UniverseService


def main() -> None:
    init_db()
    with session_scope() as session:
        u_svc = UniverseService(session)
        r_svc = ReviewService(session)

        samples = {
            "istirak": ["İştirak A", "İştirak B", "İştirak C"],
            "mudurluk": ["Müdürlük A", "Müdürlük B"],
            "urun": ["Ürün A", "Ürün B"],
        }
        created = {}
        for utype, names in samples.items():
            for name in names:
                existing = u_svc.repo.find_by_name(utype, name)
                if existing:
                    created[(utype, name)] = existing
                else:
                    created[(utype, name)] = u_svc.create(
                        UniverseCreate(universe_type=utype, name=name)
                    )

        # A: multiple reviews → last 2025 (green-ish depending on today)
        a = created[("istirak", "İştirak A")]
        if not r_svc.list_for_universe(a.id):
            for y in (2020, 2022, 2025):
                r_svc.create(
                    ReviewCreate(
                        universe_id=a.id,
                        review_subject=f"Periyodik inceleme {y}",
                        covered_decision_count=10,
                        decision_ownership="KBU",
                        unit="KBU",
                        review_date=date(y, 3, 15),
                        unit_decision_counts="KBU:10",
                        review_status="tamamlandi",
                        assurance_level="makul",
                        risk_level="orta",
                        examination_depth="tam",
                    )
                )

        # B: old review → orange
        b = created[("istirak", "İştirak B")]
        if not r_svc.list_for_universe(b.id):
            r_svc.create(
                ReviewCreate(
                    universe_id=b.id,
                    review_subject="Eski inceleme",
                    covered_decision_count=3,
                    decision_ownership="KBD",
                    unit="KBD",
                    review_date=date(2019, 1, 10),
                    unit_decision_counts="",
                    review_status="tamamlandi",
                    assurance_level="sinirli",
                    risk_level="yuksek",
                    examination_depth="tam",
                )
            )

        # C: no reviews → gray
        print("Demo seed tamamlandı.")


if __name__ == "__main__":
    main()
