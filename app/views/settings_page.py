from __future__ import annotations

import streamlit as st

from app.config.field_keys import (
    ACTIVITY_DENETIM,
    ACTIVITY_LABELS,
    ACTIVITY_UYUM,
    FIELD_KEYS,
    FIELD_KEY_LABELS,
    FIELD_UNIT,
)
from app.database.session import session_scope
from app.schemas.field_option import FieldOptionCreate, FieldOptionUpdate
from app.services.field_option_service import FieldOptionService, FieldOptionServiceError
from app.services.settings_service import AppSettingsService


def render() -> None:
    st.markdown('<div class="am-page-title">Ayarlar</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="am-page-sub">Geçerlilik süresi, harita birim eşlemesi ve form alan seçenekleri</div>',
        unsafe_allow_html=True,
    )

    with session_scope() as session:
        settings = AppSettingsService(session)
        years = settings.get_validity_years()
        new_years = st.number_input(
            "İnceleme geçerlilik süresi (yıl)",
            min_value=1,
            max_value=50,
            value=years,
            step=1,
        )
        if st.button("Geçerlilik süresini kaydet"):
            try:
                settings.set_validity_years(int(new_years))
                st.success("Kaydedildi.")
            except ValueError as exc:
                st.error(str(exc))

        st.divider()
        st.subheader("Harita — Birim → Faaliyet türü")
        st.caption(
            "Evren haritası sembolleri için: KBU=Uyum, KBD=Denetim (varsayılan). "
            "Yeni birimler burada eşlenir. Harita zaman penceresi sabittir (3 yıl)."
        )
        options_svc = FieldOptionService(session)
        units = options_svc.list_active(FIELD_UNIT)
        current_map = settings.get_unit_activity_map()
        activity_choices = [ACTIVITY_UYUM, ACTIVITY_DENETIM]
        updated: dict[str, str] = {}
        if not units:
            st.warning("Aktif birim seçeneği yok.")
        else:
            for unit in units:
                default_act = current_map.get(unit.value, ACTIVITY_UYUM)
                if default_act not in activity_choices:
                    default_act = ACTIVITY_UYUM
                idx = activity_choices.index(default_act)
                choice = st.selectbox(
                    f"{unit.label} (`{unit.value}`)",
                    activity_choices,
                    index=idx,
                    format_func=lambda v: ACTIVITY_LABELS.get(v, v),
                    key=f"unit_act_{unit.value}",
                )
                updated[unit.value] = choice
            if st.button("Birim eşlemesini kaydet", type="primary"):
                try:
                    settings.set_unit_activity_map(updated)
                    st.success("Birim → faaliyet eşlemesi kaydedildi.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        st.divider()
        st.subheader("Alan seçenekleri")
        st.caption(
            "Veri girişi ve Excel import yalnızca burada tanımlı aktif değerlere izin verir."
        )

        for field_key in FIELD_KEYS:
            with st.expander(FIELD_KEY_LABELS[field_key], expanded=False):
                rows = options_svc.list_all(field_key)
                for opt in rows:
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    with c1:
                        st.write(f"`{opt.value}`")
                    with c2:
                        st.write(opt.label + (" · Pasif" if not opt.is_active else ""))
                    with c3:
                        if opt.is_active:
                            if st.button("Pasifleştir", key=f"opt_off_{opt.id}"):
                                try:
                                    options_svc.deactivate(opt.id)
                                    st.rerun()
                                except FieldOptionServiceError as exc:
                                    st.error(str(exc))
                        else:
                            if st.button("Aktifleştir", key=f"opt_on_{opt.id}"):
                                try:
                                    options_svc.update(
                                        opt.id, FieldOptionUpdate(is_active=True)
                                    )
                                    st.rerun()
                                except FieldOptionServiceError as exc:
                                    st.error(str(exc))
                    with c4:
                        st.caption(f"sıra {opt.sort_order}")

                st.markdown("**Yeni seçenek**")
                with st.form(f"add_opt_{field_key}"):
                    value = st.text_input("Değer (kod)", key=f"v_{field_key}")
                    label = st.text_input("Etiket", key=f"l_{field_key}")
                    sort_order = st.number_input(
                        "Sıra", min_value=0, value=len(rows) + 1, key=f"s_{field_key}"
                    )
                    if st.form_submit_button("Ekle"):
                        try:
                            options_svc.create(
                                FieldOptionCreate(
                                    field_key=field_key,
                                    value=value,
                                    label=label or value,
                                    sort_order=int(sort_order),
                                )
                            )
                            st.success("Eklendi.")
                            st.rerun()
                        except FieldOptionServiceError as exc:
                            st.error(str(exc))
