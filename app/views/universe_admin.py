from __future__ import annotations

import streamlit as st

from app.config.field_keys import UNIVERSE_TYPE_LABELS, UniverseType
from app.database.session import session_scope
from app.schemas.universe import UniverseCreate
from app.services.universe_service import UniverseService, UniverseServiceError


def render() -> None:
    st.markdown('<div class="am-page-title">Evren Yönetimi</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="am-page-sub">İştirak / Müdürlük / Ürün master listeleri — ekle, düzenle, pasifleştir</div>',
        unsafe_allow_html=True,
    )

    types = list(UniverseType)
    labels = [UNIVERSE_TYPE_LABELS[t.value] for t in types]
    t_idx = st.selectbox("Evren tipi", range(len(types)), format_func=lambda i: labels[i])
    universe_type = types[t_idx].value

    with session_scope() as session:
        svc = UniverseService(session)

        with st.form("add_universe"):
            name = st.text_input("Yeni entity adı")
            submitted = st.form_submit_button("Ekle", type="primary")
            if submitted:
                try:
                    svc.create(UniverseCreate(universe_type=universe_type, name=name))
                    session.commit()
                    st.success(f"'{name}' eklendi.")
                    st.rerun()
                except UniverseServiceError as exc:
                    st.error(str(exc))

        st.divider()
        show_inactive = st.checkbox("Pasif kayıtları göster", value=False)
        entities = svc.list(universe_type, active_only=False if show_inactive else True)

        if not entities:
            st.info("Kayıt yok." if not show_inactive else "Pasif kayıt yok.")
            return

        for entity in entities:
            badge = "Aktif" if entity.is_active else "Pasif"
            with st.expander(f"{entity.name} · {badge}  #{entity.id}", expanded=False):
                new_name = st.text_input(
                    "Adı düzenle",
                    value=entity.name,
                    key=f"rename_input_{entity.id}",
                )
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button(
                        "Kaydet",
                        key=f"rename_save_{entity.id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            svc.rename(entity.id, new_name)
                            session.commit()
                            st.toast(f"'{new_name}' kaydedildi.")
                            st.rerun()
                        except UniverseServiceError as exc:
                            st.error(str(exc))
                with b2:
                    if entity.is_active:
                        if st.button(
                            "Pasife al",
                            key=f"deact_{entity.id}",
                            use_container_width=True,
                        ):
                            try:
                                svc.deactivate(entity.id)
                                session.commit()
                                st.toast(f"'{entity.name}' pasife alındı.")
                                st.rerun()
                            except UniverseServiceError as exc:
                                st.error(str(exc))
                    else:
                        if st.button(
                            "Aktife al",
                            key=f"act_{entity.id}",
                            use_container_width=True,
                        ):
                            try:
                                svc.activate(entity.id)
                                session.commit()
                                st.toast(f"'{entity.name}' aktife alındı.")
                                st.rerun()
                            except UniverseServiceError as exc:
                                st.error(str(exc))
                with b3:
                    if st.button("Sil", key=f"del_{entity.id}", use_container_width=True):
                        try:
                            svc.delete(entity.id)
                            session.commit()
                            st.toast("Silindi.")
                            st.rerun()
                        except UniverseServiceError as exc:
                            st.warning(str(exc))

        if not show_inactive:
            st.caption("Pasife alınan kayıtları görmek için yukarıdaki kutuyu işaretleyin.")
