from __future__ import annotations

import streamlit as st

from app.components.review_form import clear_review_edit_keys, render_review_edit_form
from app.config.field_keys import (
    FIELD_ASSURANCE_LEVEL,
    FIELD_EXAMINATION_DEPTH,
    FIELD_REVIEW_STATUS,
    FIELD_RISK_LEVEL,
    FIELD_UNIT,
)
from app.database.session import session_scope
from app.services.field_option_service import FieldOptionService
from app.services.review_service import ReviewService, ReviewServiceError


def _kv(label: str, value: object) -> None:
    st.markdown(f"**{label}**")
    st.markdown(f"{'—' if value is None or value == '' else value}")


@st.dialog("İnceleme Detayı", width="large")
def show_entity_detail_dialog(
    *,
    entity_id: int,
    entity_name: str,
    nav_ids: list[int],
) -> None:
    st.markdown(f"## {entity_name}")

    # Clear edit widget keys on a fresh run (not after widgets were instantiated).
    pending_clear = st.session_state.pop("_pending_clear_edit_keys", None)
    if pending_clear:
        clear_review_edit_keys(pending_clear)

    with session_scope() as session:
        options = FieldOptionService(session)
        reviews = ReviewService(session).list_for_universe(entity_id)
        # Detach plain snapshots so UI does not depend on live ORM after mutate.
        review_rows = [
            {
                "id": r.id,
                "review_subject": r.review_subject,
                "review_date": r.review_date,
                "covered_decision_count": r.covered_decision_count,
                "decision_ownership": r.decision_ownership,
                "unit": r.unit,
                "unit_decision_counts": r.unit_decision_counts,
                "review_status": r.review_status,
                "assurance_level": r.assurance_level,
                "risk_level": r.risk_level,
                "examination_depth": r.examination_depth,
            }
            for r in reviews
        ]

        if not review_rows:
            st.info("Bu entity için henüz inceleme kaydı yok.")
        else:
            st.caption(f"{len(review_rows)} inceleme kaydı · yeniden eskiye")

        for row in review_rows:
            rid = row["id"]
            unit = options.resolve_label(FIELD_UNIT, row["unit"])
            status = options.resolve_label(FIELD_REVIEW_STATUS, row["review_status"])
            assurance = options.resolve_label(
                FIELD_ASSURANCE_LEVEL, row["assurance_level"]
            )
            risk = options.resolve_label(FIELD_RISK_LEVEL, row["risk_level"])
            depth = options.resolve_label(
                FIELD_EXAMINATION_DEPTH, row["examination_depth"]
            )

            with st.container(border=True):
                head_l, head_r = st.columns([4, 1])
                with head_l:
                    st.markdown(f"### {row['review_subject']}")
                with head_r:
                    st.markdown(f"**{row['review_date'].isoformat()}**")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Birim", unit)
                m2.metric("Durum", status)
                m3.metric("Risk", risk)
                m4.metric("Güvence", assurance)

                st.divider()
                detail_rows = [
                    ("İnceleme Konusu", row["review_subject"]),
                    ("Entity adı", entity_name),
                    ("İnceleme Tarihi", row["review_date"].isoformat()),
                    ("Kapsama Alınan Karar Sayısı", row["covered_decision_count"]),
                    ("Karar Sahipliği", row["decision_ownership"] or "—"),
                    ("Birim", unit),
                    ("Birim Karar Sayıları", row["unit_decision_counts"] or "—"),
                    ("İnceleme Durumu", status),
                    ("Güvence Seviyesi", assurance),
                    ("Risk Seviyesi", risk),
                    ("İnceleme Derinliği", depth),
                ]
                for i in range(0, len(detail_rows), 2):
                    cols = st.columns(2)
                    with cols[0]:
                        _kv(*detail_rows[i])
                    if i + 1 < len(detail_rows):
                        with cols[1]:
                            _kv(*detail_rows[i + 1])

                b1, b2 = st.columns(2)
                with b1:
                    if st.button(
                        "Düzenle",
                        key=f"dlg_edit_open_{rid}",
                        use_container_width=True,
                    ):
                        st.session_state[f"editing_review_{rid}"] = True
                        st.rerun()
                with b2:
                    if st.button(
                        "Sil",
                        key=f"dlg_del_{rid}",
                        use_container_width=True,
                    ):
                        try:
                            ReviewService(session).delete(rid)
                            session.commit()
                            st.session_state.pop(f"editing_review_{rid}", None)
                            st.session_state["_pending_clear_edit_keys"] = f"edit_{rid}"
                            st.toast("İnceleme silindi.")
                            st.rerun()
                        except ReviewServiceError as exc:
                            st.error(str(exc))

                if st.session_state.get(f"editing_review_{rid}"):
                    st.markdown("#### İncelemeyi düzenle")
                    review_orm = ReviewService(session).repo.get(rid)
                    if review_orm is None:
                        st.warning("Kayıt silinmiş olabilir; diyalogu yenileyin.")
                    else:
                        saved = render_review_edit_form(
                            session,
                            review_orm,
                            key_prefix=f"edit_{rid}",
                            commit=True,
                        )
                        if st.button(
                            "Düzenlemeyi kapat",
                            key=f"dlg_edit_close_{rid}",
                            use_container_width=True,
                        ):
                            st.session_state[f"editing_review_{rid}"] = False
                            st.session_state["_pending_clear_edit_keys"] = f"edit_{rid}"
                            st.rerun()
                        if saved:
                            st.session_state[f"editing_review_{rid}"] = False
                            st.session_state["_pending_clear_edit_keys"] = f"edit_{rid}"
                            st.toast("İnceleme güncellendi.")
                            st.rerun()

    try:
        idx = nav_ids.index(entity_id)
    except ValueError:
        idx = -1

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("← Önceki", disabled=idx <= 0, use_container_width=True):
            st.session_state["selected_entity_id"] = nav_ids[idx - 1]
            st.rerun()
    with c2:
        if st.button(
            "Sonraki →",
            disabled=idx < 0 or idx >= len(nav_ids) - 1,
            use_container_width=True,
        ):
            st.session_state["selected_entity_id"] = nav_ids[idx + 1]
            st.rerun()
    with c3:
        if st.button("Kapat", use_container_width=True):
            st.session_state["selected_entity_id"] = None
            st.rerun()
