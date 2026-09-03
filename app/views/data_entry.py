from __future__ import annotations

from datetime import date

import streamlit as st

from app.components.option_select import option_select
from app.components.review_form import render_review_edit_form
from app.config.field_keys import (
    FIELD_ASSURANCE_LEVEL,
    FIELD_EXAMINATION_DEPTH,
    FIELD_REVIEW_STATUS,
    FIELD_RISK_LEVEL,
    FIELD_UNIT,
    UNIVERSE_TYPE_LABELS,
    UniverseType,
)
from app.database.session import session_scope
from app.schemas.review import ReviewCreate
from app.services.field_option_service import FieldOptionService
from app.services.review_service import ReviewService, ReviewServiceError
from app.services.universe_service import UniverseService


def render() -> None:
    st.markdown('<div class="am-page-title">Veri Girişi</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="am-page-sub">İnceleme kaydı ekleyin veya mevcut kayıtları düzenleyin.</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs([UNIVERSE_TYPE_LABELS[t.value] for t in UniverseType])
    for tab, utype in zip(tabs, UniverseType):
        with tab:
            _render_form(utype.value)


def _render_form(universe_type: str) -> None:
    with session_scope() as session:
        entities = UniverseService(session).list(universe_type, active_only=True)
        options = FieldOptionService(session)

        if not entities:
            st.warning("Bu evrende aktif entity yok. Önce Evren Yönetimi'nden ekleyin.")
            return

        entity_names = [e.name for e in entities]
        entity_ids = [e.id for e in entities]
        e_idx = st.selectbox(
            f"{UNIVERSE_TYPE_LABELS[universe_type]} Adı",
            range(len(entity_names)),
            format_func=lambda i: entity_names[i],
            key=f"de_entity_{universe_type}",
        )

        with st.expander("Yeni inceleme ekle", expanded=True):
            subject = st.text_input("İnceleme Konusu", key=f"de_subject_{universe_type}")
            covered = st.number_input(
                "Kapsama Alınan Karar Sayısı",
                min_value=0,
                step=1,
                key=f"de_covered_{universe_type}",
            )
            ownership = st.text_input("Karar Sahipliği", key=f"de_own_{universe_type}")
            unit = option_select(
                FIELD_UNIT,
                options.list_active(FIELD_UNIT),
                key=f"de_unit_{universe_type}",
            )
            review_date = st.date_input(
                "İnceleme Tarihi",
                value=date.today(),
                key=f"de_date_{universe_type}",
            )
            unit_counts = st.text_area(
                "Birim Karar Sayıları",
                key=f"de_ucount_{universe_type}",
            )
            status = option_select(
                FIELD_REVIEW_STATUS,
                options.list_active(FIELD_REVIEW_STATUS),
                key=f"de_status_{universe_type}",
            )
            assurance = option_select(
                FIELD_ASSURANCE_LEVEL,
                options.list_active(FIELD_ASSURANCE_LEVEL),
                key=f"de_assurance_{universe_type}",
            )
            risk = option_select(
                FIELD_RISK_LEVEL,
                options.list_active(FIELD_RISK_LEVEL),
                key=f"de_risk_{universe_type}",
            )
            depth = option_select(
                FIELD_EXAMINATION_DEPTH,
                options.list_active(FIELD_EXAMINATION_DEPTH),
                key=f"de_depth_{universe_type}",
            )

            st.caption(
                "Son Denetim/Kontrol Tarihi otomatik hesaplanır; manuel girilmez."
            )

            if st.button("Kaydet", key=f"de_save_{universe_type}", type="primary"):
                if not all([subject, unit, status, assurance, risk, depth]):
                    st.error("Zorunlu alanları doldurun / Ayarlar'da seçenek tanımlayın.")
                else:
                    try:
                        ReviewService(session).create(
                            ReviewCreate(
                                universe_id=entity_ids[e_idx],
                                review_subject=subject,
                                covered_decision_count=int(covered),
                                decision_ownership=ownership or "",
                                unit=unit,
                                review_date=review_date,
                                unit_decision_counts=unit_counts or "",
                                review_status=status,
                                assurance_level=assurance,
                                risk_level=risk,
                                examination_depth=depth,
                            )
                        )
                        st.success("İnceleme kaydı oluşturuldu.")
                        st.rerun()
                    except ReviewServiceError as exc:
                        st.error(str(exc))

        st.divider()
        st.subheader("Mevcut kayıtlar — düzenle / sil")
        selected_id = entity_ids[e_idx]
        rows = ReviewService(session).list_for_universe(selected_id)
        if not rows:
            st.info("Kayıt yok.")
            return

        for r in rows:
            label_unit = options.resolve_label(FIELD_UNIT, r.unit)
            label_status = options.resolve_label(FIELD_REVIEW_STATUS, r.review_status)
            label_risk = options.resolve_label(FIELD_RISK_LEVEL, r.risk_level)
            with st.expander(
                f"{r.review_date.isoformat()} — {r.review_subject} · {label_unit} · {label_status} · Risk: {label_risk}",
                expanded=False,
            ):
                if st.session_state.get(f"de_editing_{r.id}"):
                    saved = render_review_edit_form(
                        session, r, key_prefix=f"de_edit_{universe_type}_{r.id}"
                    )
                    if st.button("Vazgeç", key=f"de_cancel_{universe_type}_{r.id}"):
                        st.session_state[f"de_editing_{r.id}"] = False
                        st.rerun()
                    if saved:
                        st.session_state[f"de_editing_{r.id}"] = False
                        st.rerun()
                else:
                    info_cols = st.columns(2)
                    pairs = [
                        ("İnceleme Konusu", r.review_subject),
                        ("İnceleme Tarihi", r.review_date.isoformat()),
                        ("Birim", label_unit),
                        ("İnceleme Durumu", label_status),
                        ("Risk Seviyesi", label_risk),
                        (
                            "Güvence Seviyesi",
                            options.resolve_label(
                                FIELD_ASSURANCE_LEVEL, r.assurance_level
                            ),
                        ),
                        (
                            "İnceleme Derinliği",
                            options.resolve_label(
                                FIELD_EXAMINATION_DEPTH, r.examination_depth
                            ),
                        ),
                        ("Kapsama Alınan Karar Sayısı", r.covered_decision_count),
                        ("Karar Sahipliği", r.decision_ownership or "—"),
                        ("Birim Karar Sayıları", r.unit_decision_counts or "—"),
                    ]
                    for i, (lab, val) in enumerate(pairs):
                        with info_cols[i % 2]:
                            st.markdown(f"**{lab}**")
                            st.markdown(str(val))
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button(
                            "Düzenle",
                            key=f"de_edit_btn_{universe_type}_{r.id}",
                            use_container_width=True,
                        ):
                            st.session_state[f"de_editing_{r.id}"] = True
                            st.rerun()
                    with b2:
                        if st.button(
                            "Sil",
                            key=f"de_del_btn_{universe_type}_{r.id}",
                            use_container_width=True,
                        ):
                            try:
                                ReviewService(session).delete(r.id)
                                st.success("Silindi.")
                                st.rerun()
                            except ReviewServiceError as exc:
                                st.error(str(exc))
