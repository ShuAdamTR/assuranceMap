from __future__ import annotations

import hashlib
from datetime import date

import pandas as pd
import streamlit as st

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
from app.schemas.import_preview import ImportPreviewResult
from app.services.field_option_service import FieldOptionService
from app.services.import_service import (
    COL_ASSURANCE,
    COL_COVERED,
    COL_DATE,
    COL_DEPTH,
    COL_OWNERSHIP,
    COL_RISK,
    COL_STATUS,
    COL_SUBJECT,
    COL_UNIT,
    COL_UNIT_COUNTS,
    ImportService,
    entity_column_name,
    ensure_templates,
    generate_template_bytes,
    required_columns_for,
)
from app.services.review_service import ReviewServiceError
from app.services.universe_service import UniverseService
from app.utils.dates import DATE_FORMAT_HINT, format_date_tr, normalize_to_date


def _file_fingerprint(name: str, data: bytes) -> str:
    return hashlib.sha256(f"{name}:{len(data)}:".encode() + data[:4096]).hexdigest()


def _option_labels(session, field_key: str) -> list[str]:
    return [o.label for o in FieldOptionService(session).list_active(field_key)]


def _clear_import_state() -> None:
    for key in list(st.session_state.keys()):
        if str(key).startswith("import_"):
            st.session_state.pop(key, None)


def _cell_str(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, date):
        return format_date_tr(value)
    text = str(value).strip()
    if text.lower() in {"nan", "nat", "none", "<na>"}:
        return ""
    # Excel float ints: 42.0 → 42
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return text


def _cell_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return int(float(str(value).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return None


def prepare_editor_dataframe(df: pd.DataFrame, universe_type: str) -> pd.DataFrame:
    """
    Build a fresh DataFrame with Python-native types Streamlit can edit:
    - text columns → plain str (object dtype)
    - covered → int | None
    - date → DD.MM.YYYY string (avoids DateColumn/dtype fights)
    """
    cols = required_columns_for(universe_type)
    entity_col = entity_column_name(universe_type)
    data: dict[str, list] = {c: [] for c in cols}

    working = df.copy()
    for col in cols:
        if col not in working.columns:
            working[col] = None

    for _, row in working.iterrows():
        for col in cols:
            raw = row.get(col)
            if col == COL_COVERED:
                data[col].append(_cell_int(raw))
            elif col == COL_DATE:
                parsed = normalize_to_date(raw)
                data[col].append(format_date_tr(parsed) if parsed else _cell_str(raw))
            else:
                data[col].append(_cell_str(raw))

    out = pd.DataFrame(data)
    # Explicit object dtype for all text-like columns (critical for Streamlit)
    for col in cols:
        if col == COL_COVERED:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
        else:
            out[col] = out[col].astype(object)
    # Ensure entity col name matches
    if entity_col not in out.columns and COL_SUBJECT in out.columns:
        pass
    return out


def _column_guide(universe_type: str) -> None:
    entity_col = entity_column_name(universe_type)
    type_label = UNIVERSE_TYPE_LABELS[universe_type]
    with st.expander("Excel sütun rehberi — ne yazmalıyım?", expanded=True):
        st.markdown(
            f"""
1. satır **başlık** olmalıdır. Veriler **2. satırdan** başlamalıdır.

| Sütun | Beklenen içerik |
|-------|-----------------|
| **İnceleme Konusu** | Serbest metin |
| **{entity_col}** | {type_label} adı (yoksa import sırasında oluşturulur) |
| **Kapsama Alınan Karar Sayısı** | Tam sayı (örn. `18`) — kısa ad `Kapsama Alınan Karar` de kabul |
| **Karar Sahipliği** | Serbest metin |
| **Birim** | Ayarlar'daki değerler (örn. `KBU`, `KBD`) |
| **İnceleme Tarihi** | `{DATE_FORMAT_HINT}` veya Excel tarih hücresi |
| **Birim Karar Sayıları** | Metin veya sayı (örn. `42` veya `KBU:10`) |
| **İnceleme Durumu** | Ayarlar'daki etiket (örn. `Tamamlandı`) |
| **Güvence Seviyesi** | Ayarlar'daki etiket (örn. `Makul`) |
| **Risk Seviyesi** | Ayarlar'daki etiket (örn. `Orta`) |
| **İnceleme Derinliği** | Ayarlar'daki etiket (`Tam` veya `Kısmi`) |
"""
        )


def _show_validation_errors(preview: ImportPreviewResult) -> None:
    error_rows = [r for r in preview.rows if not r.ok]
    if not error_rows:
        return
    st.subheader("Hata listesi")
    st.caption("Hangi satırda, hangi kolonda, neden sorun olduğu aşağıda.")
    flat: list[dict] = []
    for r in error_rows:
        for e in r.errors:
            flat.append(
                {
                    "Excel satırı": r.row_number,
                    "Kolon": e.field or "Genel",
                    "Kayıt": r.universe_name or "—",
                    "Sorun": e.message,
                }
            )
    st.dataframe(flat, use_container_width=True, hide_index=True)
    by_col: dict[str, int] = {}
    for item in flat:
        by_col[item["Kolon"]] = by_col.get(item["Kolon"], 0) + 1
    st.info(
        "Kolon özeti: "
        + " · ".join(f"**{col}** → {cnt} hata" for col, cnt in sorted(by_col.items()))
    )


def render() -> None:
    st.markdown('<div class="am-page-title">Excel Import</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="am-page-sub">Yükle → biçimle → önizle/düzenle → onayla</div>',
        unsafe_allow_html=True,
    )

    ensure_templates()
    types = list(UniverseType)
    labels = [UNIVERSE_TYPE_LABELS[t.value] for t in types]
    t_idx = st.selectbox(
        "Evren", range(len(types)), format_func=lambda i: labels[i], key="imp_type"
    )
    universe_type = types[t_idx].value
    type_label = UNIVERSE_TYPE_LABELS[universe_type]
    entity_col = entity_column_name(universe_type)

    _column_guide(universe_type)

    st.download_button(
        "Şablon indir",
        data=generate_template_bytes(universe_type),
        file_name=f"{universe_type}_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded = st.file_uploader("Excel dosyası (.xlsx)", type=["xlsx"], key="imp_file")
    if uploaded is None:
        _clear_import_state()
        return

    file_bytes = uploaded.getvalue()
    fp = _file_fingerprint(uploaded.name, file_bytes)

    try:
        with session_scope() as session:
            svc = ImportService(session)
            reload_needed = (
                st.session_state.get("import_file_fp") != fp
                or st.session_state.get("import_universe_type") != universe_type
            )
            if reload_needed:
                df, missing, extra, notes = svc.read_and_normalize(
                    universe_type, file_bytes
                )
                editor_df = prepare_editor_dataframe(df, universe_type) if not missing else df
                st.session_state["import_file_fp"] = fp
                st.session_state["import_universe_type"] = universe_type
                st.session_state["import_missing"] = missing
                st.session_state["import_extra"] = extra
                st.session_state["import_notes"] = notes
                st.session_state["import_edit_df"] = editor_df
                if not missing:
                    preview = svc.validate_dataframe(universe_type, editor_df)
                    preview.normalize_notes = notes
                    st.session_state["import_preview_result"] = preview.model_dump(
                        mode="json"
                    )
                else:
                    st.session_state.pop("import_preview_result", None)

            missing = st.session_state.get("import_missing") or []
            extra = st.session_state.get("import_extra") or []
            notes = st.session_state.get("import_notes") or []

            if missing:
                st.error(
                    "Excel’de şu zorunlu başlıklar eksik (1. satır başlık olmalı): "
                    + ", ".join(f"**{c}**" for c in missing)
                )
                return

            if extra and not str(extra[0]).startswith("Dosya okunamadı"):
                st.warning(
                    "Tanımlı şablonda olmayan sütunlar yok sayıldı: "
                    + ", ".join(extra)
                )

            if notes:
                with st.expander("Otomatik biçimlendirme notları", expanded=False):
                    for note in notes:
                        st.markdown(f"- {note}")

            unit_labels = _option_labels(session, FIELD_UNIT)
            status_labels = _option_labels(session, FIELD_REVIEW_STATUS)
            assurance_labels = _option_labels(session, FIELD_ASSURANCE_LEVEL)
            risk_labels = _option_labels(session, FIELD_RISK_LEVEL)
            depth_labels = _option_labels(session, FIELD_EXAMINATION_DEPTH)

            # Always rebuild clean frame from session (prevents stale int dtypes)
            raw_edit = st.session_state["import_edit_df"]
            base_df = prepare_editor_dataframe(raw_edit, universe_type)

            entities = UniverseService(session).list(universe_type, active_only=False)
            active_names = [e.name for e in entities if e.is_active]
            file_names = sorted(
                {
                    str(v).strip()
                    for v in base_df[entity_col].tolist()
                    if str(v).strip()
                }
            )
            entity_options = sorted(set(active_names) | set(file_names))

            st.subheader("Önizleme / düzenleme")
            st.caption(
                "1. satır başlık kabul edildi · veriler aşağıda. "
                "Düzenleyip doğrulayın, sonra onaylayın."
            )

            column_config = {
                entity_col: st.column_config.TextColumn(
                    entity_col,
                    required=True,
                    help=f"{type_label} adı. Listede yoksa import sırasında oluşturulur.",
                ),
                COL_SUBJECT: st.column_config.TextColumn(COL_SUBJECT, required=True),
                COL_COVERED: st.column_config.NumberColumn(
                    COL_COVERED,
                    min_value=0,
                    step=1,
                    required=True,
                    help="Tam sayı girin (örn. 18).",
                ),
                COL_OWNERSHIP: st.column_config.TextColumn(COL_OWNERSHIP),
                COL_UNIT: st.column_config.SelectboxColumn(
                    COL_UNIT, options=unit_labels or ["KBU", "KBD"], required=True
                ),
                COL_DATE: st.column_config.TextColumn(
                    COL_DATE,
                    required=True,
                    help=f"Tarih metni: {DATE_FORMAT_HINT}",
                ),
                COL_UNIT_COUNTS: st.column_config.TextColumn(
                    COL_UNIT_COUNTS,
                    help="Metin veya sayı olabilir (örn. 42 veya KBU:10).",
                ),
                COL_STATUS: st.column_config.SelectboxColumn(
                    COL_STATUS, options=status_labels, required=True
                ),
                COL_ASSURANCE: st.column_config.SelectboxColumn(
                    COL_ASSURANCE, options=assurance_labels, required=True
                ),
                COL_RISK: st.column_config.SelectboxColumn(
                    COL_RISK, options=risk_labels, required=True
                ),
                COL_DEPTH: st.column_config.SelectboxColumn(
                    COL_DEPTH, options=depth_labels, required=True
                ),
            }

            # Unique key per file → prevents Streamlit caching old INTEGER schema
            editor_key = f"import_editor_{fp[:12]}_{universe_type}"
            edited = st.data_editor(
                base_df,
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key=editor_key,
            )
            # Persist cleaned copy
            st.session_state["import_edit_df"] = prepare_editor_dataframe(
                edited, universe_type
            )

            b1, b2, b3 = st.columns(3)
            with b1:
                validate_clicked = st.button("Yeniden doğrula", use_container_width=True)
            with b2:
                commit_clicked = st.button(
                    "Onayla ve veritabanına yaz",
                    type="primary",
                    use_container_width=True,
                )
            with b3:
                if st.button("Önizlemeyi temizle", use_container_width=True):
                    _clear_import_state()
                    st.rerun()

            current_df = st.session_state["import_edit_df"]
            if validate_clicked or commit_clicked or not st.session_state.get(
                "import_preview_result"
            ):
                preview = svc.validate_dataframe(universe_type, current_df)
                preview.normalize_notes = notes
                st.session_state["import_preview_result"] = preview.model_dump(
                    mode="json"
                )
            else:
                preview = ImportPreviewResult.model_validate(
                    st.session_state["import_preview_result"]
                )

            if preview.entities_to_create:
                st.warning(
                    f"Şu {type_label} kayıtları henüz yok; import sırasında "
                    f"**oluşturulacak**: "
                    + ", ".join(f"**{n}**" for n in preview.entities_to_create)
                )
            if preview.entities_to_reactivate:
                st.warning(
                    f"Şu {type_label} kayıtları pasif; import sırasında "
                    f"**aktifleştirilecek**: "
                    + ", ".join(f"**{n}**" for n in preview.entities_to_reactivate)
                )

            st.write(
                f"Geçerli satır: **{preview.valid_count}** · "
                f"Hatalı satır: **{preview.error_count}**"
            )
            _show_validation_errors(preview)

            warn_rows = [r for r in preview.rows if r.ok and r.warnings]
            if warn_rows:
                with st.expander("Uyarılar (işlemi engellemez)", expanded=False):
                    for r in warn_rows:
                        for w in r.warnings:
                            st.markdown(f"- Excel satır {r.row_number}: {w}")

            if commit_clicked:
                preview = svc.validate_dataframe(universe_type, current_df)
                st.session_state["import_preview_result"] = preview.model_dump(
                    mode="json"
                )
                if not preview.can_commit:
                    st.error(
                        "İçe aktarma yapılamadı. Yukarıdaki hata listesinden "
                        "kolonları düzeltip tekrar deneyin."
                    )
                else:
                    try:
                        created = list(preview.entities_to_create)
                        count = svc.commit(preview)
                        session.commit()
                        msg = f"{count} inceleme kaydı içe aktarıldı."
                        if created:
                            msg += (
                                f" Yeni {type_label}: " + ", ".join(created) + "."
                            )
                        st.success(msg)
                        _clear_import_state()
                        st.rerun()
                    except ReviewServiceError as exc:
                        st.error(str(exc))
            elif preview.can_commit:
                st.success("Satırlar hazır. Onaylayarak içeri alabilirsiniz.")
            elif preview.error_count:
                st.warning("Hatalı satırlar var — kolonları düzeltip yeniden doğrulayın.")

    except Exception as exc:  # noqa: BLE001
        # Never dump traceback / StreamlitAPIException code to the user
        msg = str(exc)
        if "ColumnDataKind" in msg or "compatible" in msg.lower():
            st.error(
                "Excel kolon tipleri önizleme ile uyuşmadı. "
                "Sayfayı yenileyip dosyayı tekrar yükleyin. "
                "İpucu: 1. satır başlık olmalı; "
                f"tarihler {DATE_FORMAT_HINT}; "
                "Birim Karar Sayıları metin veya sayı olabilir."
            )
        else:
            st.error(
                "Dosya işlenirken bir sorun oluştu. "
                "Başlık satırını ve sütun rehberindeki formatları kontrol edip tekrar deneyin."
            )
        with st.expander("Teknik ayrıntı (geliştirici)", expanded=False):
            st.code(msg)
