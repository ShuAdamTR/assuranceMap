from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.config.field_keys import (
    FIELD_ASSURANCE_LEVEL,
    FIELD_EXAMINATION_DEPTH,
    FIELD_REVIEW_STATUS,
    FIELD_RISK_LEVEL,
    FIELD_UNIT,
    UNIVERSE_TYPE_LABELS,
)
from app.config.settings import PROJECT_ROOT
from app.repositories.universe_repo import UniverseRepository
from app.schemas.import_preview import ImportPreviewResult, ImportRowError, ImportRowResult
from app.schemas.review import ReviewCreate
from app.services.field_option_service import FieldOptionService, FieldOptionServiceError
from app.services.review_service import ReviewService, ReviewServiceError
from app.utils.dates import date_parse_error_message, format_date_tr, normalize_to_date

# Excel kolon başlıkları (TR)
COL_SUBJECT = "İnceleme Konusu"
COL_ENTITY = "Entity Adı"
COL_COVERED = "Kapsama Alınan Karar Sayısı"
COL_OWNERSHIP = "Karar Sahipliği"
COL_UNIT = "Birim"
COL_DATE = "İnceleme Tarihi"
COL_UNIT_COUNTS = "Birim Karar Sayıları"
COL_STATUS = "İnceleme Durumu"
COL_ASSURANCE = "Güvence Seviyesi"
COL_RISK = "Risk Seviyesi"
COL_DEPTH = "İnceleme Derinliği"

REQUIRED_COLUMNS = [
    COL_SUBJECT,
    COL_ENTITY,
    COL_COVERED,
    COL_OWNERSHIP,
    COL_UNIT,
    COL_DATE,
    COL_UNIT_COUNTS,
    COL_STATUS,
    COL_ASSURANCE,
    COL_RISK,
    COL_DEPTH,
]

ENTITY_COLUMN_BY_TYPE = {
    "istirak": "İştirak Adı",
    "mudurluk": "Müdürlük Adı",
    "urun": "Ürün Adı",
}

OPTION_COLUMNS = {
    COL_UNIT: FIELD_UNIT,
    COL_STATUS: FIELD_REVIEW_STATUS,
    COL_ASSURANCE: FIELD_ASSURANCE_LEVEL,
    COL_RISK: FIELD_RISK_LEVEL,
    COL_DEPTH: FIELD_EXAMINATION_DEPTH,
}

# Flexible Excel header aliases → canonical column name
COLUMN_ALIASES: dict[str, str] = {
    "entity adı": COL_ENTITY,
    "entity adi": COL_ENTITY,
    "kapsama alınan karar": COL_COVERED,
    "kapsama alinan karar": COL_COVERED,
    "kapsama alınan karar sayısı": COL_COVERED,
    "kapsama alinan karar sayisi": COL_COVERED,
    "birim karar sayıları": COL_UNIT_COUNTS,
    "birim karar sayilari": COL_UNIT_COUNTS,
}


def _canon_header(name: str) -> str:
    return str(name).strip().casefold()


def apply_column_aliases(df: pd.DataFrame, universe_type: str) -> tuple[pd.DataFrame, list[str]]:
    """Rename known alternate headers to canonical names."""
    notes: list[str] = []
    entity_col = entity_column_name(universe_type)
    rename_map: dict[str, str] = {}
    for col in list(df.columns):
        key = _canon_header(col)
        if key in COLUMN_ALIASES:
            target = COLUMN_ALIASES[key]
            # Entity aliases resolved per universe type
            if target == COL_ENTITY:
                target = entity_col
            if col != target and target not in df.columns:
                rename_map[col] = target
        elif col == COL_ENTITY and entity_col not in df.columns:
            rename_map[col] = entity_col
    if rename_map:
        df = df.rename(columns=rename_map)
        for src, dst in rename_map.items():
            notes.append(f"'{src}' kolonu '{dst}' olarak eşlendi.")
    return df, notes


def entity_column_name(universe_type: str) -> str:
    return ENTITY_COLUMN_BY_TYPE.get(universe_type, COL_ENTITY)


def required_columns_for(universe_type: str) -> list[str]:
    cols = list(REQUIRED_COLUMNS)
    entity_col = entity_column_name(universe_type)
    return [entity_col if c == COL_ENTITY else c for c in cols]


def template_path(universe_type: str) -> Path:
    names = {
        "istirak": "istirak_template.xlsx",
        "mudurluk": "mudurluk_template.xlsx",
        "urun": "urun_template.xlsx",
    }
    return PROJECT_ROOT / "assets" / "templates" / names[universe_type]


def generate_template_bytes(universe_type: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = UNIVERSE_TYPE_LABELS.get(universe_type, universe_type)
    headers = required_columns_for(universe_type)
    ws.append(headers)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def ensure_templates() -> None:
    template_dir = PROJECT_ROOT / "assets" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    for ut in ("istirak", "mudurluk", "urun"):
        path = template_path(ut)
        path.write_bytes(generate_template_bytes(ut))


class ImportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.universe_repo = UniverseRepository(session)
        self.options = FieldOptionService(session)
        self.reviews = ReviewService(session)

    def preview(self, universe_type: str, file_bytes: bytes) -> ImportPreviewResult:
        df, missing, extra, notes = self.read_and_normalize(universe_type, file_bytes)
        if missing:
            return ImportPreviewResult(
                missing_columns=missing,
                extra_columns=extra,
                normalize_notes=notes,
                rows=[
                    ImportRowResult(
                        row_number=0,
                        ok=False,
                        errors=[
                            ImportRowError(
                                row_number=0,
                                message=f"Eksik kolonlar: {', '.join(missing)}",
                            )
                        ],
                    )
                ],
                error_count=1,
                can_commit=False,
            )
        result = self.validate_dataframe(universe_type, df)
        result.missing_columns = missing
        result.extra_columns = extra
        result.normalize_notes = notes
        return result

    def read_excel_dataframe(
        self, universe_type: str, file_bytes: bytes
    ) -> tuple[pd.DataFrame, list[str], list[str]]:
        df, missing, extra, _notes = self.read_and_normalize(universe_type, file_bytes)
        return df, missing, extra

    def read_and_normalize(
        self, universe_type: str, file_bytes: bytes
    ) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
        """Read Excel, then auto-normalize into import-ready shape."""
        ensure_templates()
        required = required_columns_for(universe_type)
        entity_col = entity_column_name(universe_type)
        notes: list[str] = []
        try:
            # header=0 → 1. satır başlık, veri 2. satırdan
            df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl", header=0)
        except Exception as exc:  # noqa: BLE001
            empty = pd.DataFrame(columns=required)
            return empty, required, [f"Dosya okunamadı: {exc}"], notes

        df.columns = [str(c).strip() for c in df.columns]
        df, alias_notes = apply_column_aliases(df, universe_type)
        notes.extend(alias_notes)

        present = list(df.columns)
        missing = [c for c in required if c not in present]
        extra = [c for c in present if c not in required]
        if missing:
            return df, missing, extra, notes

        df = df[required].copy()
        df = df.dropna(how="all").reset_index(drop=True)
        df, norm_notes = self.normalize_dataframe(universe_type, df)
        notes.extend(norm_notes)
        return df, missing, extra, notes

    def normalize_dataframe(
        self, universe_type: str, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, list[str]]:
        """Best-effort format cleanup for preview (does not raise)."""
        notes: list[str] = []
        entity_col = entity_column_name(universe_type)
        working = df.copy()

        # Trim text-like columns (skip date/number — handled below)
        for col in working.columns:
            if col in {COL_COVERED, COL_DATE}:
                continue
            working[col] = working[col].map(_soft_str)

        # Streamlit TextColumn requires string dtype (Excel often sends int)
        if COL_UNIT_COUNTS in working.columns:
            working[COL_UNIT_COUNTS] = working[COL_UNIT_COUNTS].map(
                lambda v: "" if v is None else str(v)
            )
            working[COL_UNIT_COUNTS] = working[COL_UNIT_COUNTS].astype("string")

        # Dates → date (Excel native date OK; text only DD.MM.YYYY / DD/MM/YYYY)
        if COL_DATE in working.columns:
            raw_non_null = int(working[COL_DATE].notna().sum())
            working[COL_DATE] = working[COL_DATE].map(normalize_to_date)
            after_ok = int(working[COL_DATE].notna().sum())
            notes.append(
                "İnceleme tarihleri kontrol edildi "
                "(kabul: GG.AA.YYYY, GG/AA/YYYY veya Excel tarih hücresi)."
            )
            failed = raw_non_null - after_ok
            if failed > 0:
                notes.append(
                    f"{failed} satırda İnceleme Tarihi okunamadı — "
                    "beklenen format: GG.AA.YYYY veya GG/AA/YYYY."
                )

        # Covered → int
        if COL_COVERED in working.columns:
            def _to_int(v: object) -> int | None:
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return None
                try:
                    return int(float(str(v).strip().replace(",", ".")))
                except (TypeError, ValueError):
                    return None

            working[COL_COVERED] = working[COL_COVERED].map(_to_int)
            notes.append("Kapsama alınan karar sayıları sayısal formata alındı.")

        # Option columns → canonical labels when matchable
        for col, field_key in OPTION_COLUMNS.items():
            if col not in working.columns:
                continue
            mapped = 0
            new_vals: list[str | None] = []
            for raw in working[col].tolist():
                text = _soft_str(raw)
                if not text:
                    new_vals.append(None)
                    continue
                resolved = self._match_option_label(field_key, text)
                if resolved and resolved != text:
                    mapped += 1
                    new_vals.append(resolved)
                else:
                    new_vals.append(resolved or text)
            working[col] = new_vals
            if mapped:
                notes.append(
                    f"'{col}' alanında {mapped} değer Ayarlar etiketine normalize edildi."
                )

        if entity_col in working.columns:
            working[entity_col] = working[entity_col].map(_soft_str)

        if COL_SUBJECT in working.columns:
            working[COL_SUBJECT] = working[COL_SUBJECT].map(_soft_str)

        # Ensure text columns stay string for Streamlit data_editor
        for col in (
            entity_col,
            COL_SUBJECT,
            COL_OWNERSHIP,
            COL_UNIT,
            COL_UNIT_COUNTS,
            COL_STATUS,
            COL_ASSURANCE,
            COL_RISK,
            COL_DEPTH,
        ):
            if col in working.columns:
                working[col] = working[col].map(
                    lambda v: None if v is None else str(v)
                )
                working[col] = working[col].astype("string")

        return working, notes

    def validate_dataframe(
        self, universe_type: str, df: pd.DataFrame
    ) -> ImportPreviewResult:
        ensure_templates()
        required = required_columns_for(universe_type)
        entity_col = entity_column_name(universe_type)
        type_label = UNIVERSE_TYPE_LABELS.get(universe_type, universe_type)

        working = df.copy()
        working.columns = [str(c).strip() for c in working.columns]
        if COL_ENTITY in working.columns and entity_col not in working.columns:
            working = working.rename(columns={COL_ENTITY: entity_col})

        # Normalize again so editor edits also get cleaned
        working, _ = self.normalize_dataframe(universe_type, working)

        present = list(working.columns)
        missing = [c for c in required if c not in present]
        extra = [c for c in present if c not in required]
        result = ImportPreviewResult(missing_columns=missing, extra_columns=extra)
        if missing:
            result.error_count = 1
            result.can_commit = False
            result.rows.append(
                ImportRowResult(
                    row_number=0,
                    ok=False,
                    errors=[
                        ImportRowError(
                            row_number=0,
                            message=f"Eksik kolonlar: {', '.join(missing)}",
                        )
                    ],
                )
            )
            return result

        working = working[required].copy()
        working = working.dropna(how="all").reset_index(drop=True)
        seen_keys: set[tuple[str, str, date]] = set()
        to_create: set[str] = set()
        to_reactivate: set[str] = set()

        for idx, row in working.iterrows():
            row_number = int(idx) + 2
            errors: list[ImportRowError] = []
            warnings: list[str] = []

            def cell(col: str) -> object:
                val = row.get(col)
                if pd.isna(val):
                    return None
                return val

            entity_name = _as_str(cell(entity_col))
            subject = _as_str(cell(COL_SUBJECT))
            ownership = _as_str(cell(COL_OWNERSHIP)) or ""
            unit = _as_str(cell(COL_UNIT))
            unit_counts = _as_str(cell(COL_UNIT_COUNTS)) or ""
            status = _as_str(cell(COL_STATUS))
            assurance = _as_str(cell(COL_ASSURANCE))
            risk = _as_str(cell(COL_RISK))
            depth = _as_str(cell(COL_DEPTH))
            covered_raw = cell(COL_COVERED)
            date_raw = cell(COL_DATE)

            if not entity_name:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=entity_col,
                        message="Bu alan zorunludur; boş bırakılamaz.",
                    )
                )
            if not subject:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=COL_SUBJECT,
                        message="Bu alan zorunludur; boş bırakılamaz.",
                    )
                )
            if not unit:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=COL_UNIT,
                        message="Bu alan zorunludur; Ayarlar'daki Birim değerlerinden biri seçilmeli.",
                    )
                )
            if not status:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=COL_STATUS,
                        message="Bu alan zorunludur; Ayarlar'daki İnceleme Durumu değerlerinden biri seçilmeli.",
                    )
                )
            if not assurance:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=COL_ASSURANCE,
                        message="Bu alan zorunludur; Ayarlar'daki Güvence Seviyesi değerlerinden biri seçilmeli.",
                    )
                )
            if not risk:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=COL_RISK,
                        message="Bu alan zorunludur; Ayarlar'daki Risk Seviyesi değerlerinden biri seçilmeli.",
                    )
                )
            if not depth:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=COL_DEPTH,
                        message="Bu alan zorunludur; Ayarlar'daki İnceleme Derinliği değerlerinden biri seçilmeli (Tam/Kısmi).",
                    )
                )

            review_date = normalize_to_date(date_raw)
            if review_date is None:
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=COL_DATE,
                        message=date_parse_error_message(date_raw),
                    )
                )

            try:
                covered = int(float(covered_raw)) if covered_raw is not None else None
                if covered is None or covered < 0:
                    raise ValueError
            except (TypeError, ValueError):
                covered = None
                errors.append(
                    ImportRowError(
                        row_number=row_number,
                        field=COL_COVERED,
                        message="Geçersiz sayı; 0 veya pozitif bir tam sayı girin.",
                    )
                )

            universe = None
            will_create = False
            if entity_name:
                universe = self.universe_repo.find_by_name(universe_type, entity_name)
                if universe is None:
                    will_create = True
                    to_create.add(entity_name)
                    warnings.append(
                        f"'{entity_name}' {type_label} evreninde yok; import sırasında oluşturulacak."
                    )
                elif not universe.is_active:
                    will_create = False
                    to_reactivate.add(entity_name)
                    warnings.append(
                        f"'{entity_name}' pasif; import sırasında yeniden aktifleştirilecek."
                    )

            unit_val = self._resolve_option_value(FIELD_UNIT, unit, row_number, COL_UNIT, errors)
            status_val = self._resolve_option_value(
                FIELD_REVIEW_STATUS, status, row_number, COL_STATUS, errors
            )
            assurance_val = self._resolve_option_value(
                FIELD_ASSURANCE_LEVEL, assurance, row_number, COL_ASSURANCE, errors
            )
            risk_val = self._resolve_option_value(
                FIELD_RISK_LEVEL, risk, row_number, COL_RISK, errors
            )
            depth_val = self._resolve_option_value(
                FIELD_EXAMINATION_DEPTH, depth, row_number, COL_DEPTH, errors
            )

            if entity_name and subject and review_date:
                key = (entity_name, subject, review_date)
                if key in seen_keys:
                    errors.append(
                        ImportRowError(
                            row_number=row_number,
                            field=None,
                            message="Aynı entity + konu + tarih bu dosyada birden fazla kez geçiyor (yinelenen satır).",
                        )
                    )
                else:
                    seen_keys.add(key)
                    if universe is not None and universe.is_active:
                        dup = self.reviews.repo.find_duplicate(
                            universe.id, subject, review_date
                        )
                        if dup is not None:
                            errors.append(
                                ImportRowError(
                                    row_number=row_number,
                                    field=None,
                                    message="Bu entity için aynı konu ve tarihle kayıt zaten sistemde var.",
                                )
                            )

            ok = len(errors) == 0
            payload = None
            if ok and entity_name and covered is not None and review_date is not None:
                payload = {
                    "universe_id": universe.id if universe is not None else None,
                    "entity_name": entity_name,
                    "universe_type": universe_type,
                    "review_subject": subject,
                    "covered_decision_count": covered,
                    "decision_ownership": ownership,
                    "unit": unit_val,
                    "review_date": review_date.isoformat(),
                    "unit_decision_counts": unit_counts,
                    "review_status": status_val,
                    "assurance_level": assurance_val,
                    "risk_level": risk_val,
                    "examination_depth": depth_val,
                    "will_create_entity": will_create,
                    "will_reactivate_entity": bool(
                        universe is not None and not universe.is_active
                    ),
                }

            result.rows.append(
                ImportRowResult(
                    row_number=row_number,
                    ok=ok,
                    errors=errors,
                    warnings=warnings,
                    universe_name=entity_name,
                    review_subject=subject,
                    review_date=review_date,
                    will_create_entity=will_create,
                    payload=payload,
                )
            )

        result.entities_to_create = sorted(to_create)
        result.entities_to_reactivate = sorted(to_reactivate)
        result.valid_count = sum(1 for r in result.rows if r.ok)
        result.error_count = sum(1 for r in result.rows if not r.ok)
        result.can_commit = (
            len(result.rows) > 0
            and result.valid_count == len(result.rows)
            and result.error_count == 0
            and not missing
        )
        return result

    def commit(self, preview: ImportPreviewResult) -> int:
        if not preview.can_commit:
            raise ReviewServiceError("Önizleme hatalı; commit yapılamaz.")
        count = 0
        for row in preview.rows:
            if not row.ok or not row.payload:
                continue
            payload = dict(row.payload)
            universe_type = payload.pop("universe_type")
            entity_name = payload.pop("entity_name")
            payload.pop("will_create_entity", False)
            payload.pop("will_reactivate_entity", False)
            payload.pop("universe_id", None)

            universe = self.universe_repo.find_by_name(universe_type, entity_name)
            if universe is None:
                universe = self.universe_repo.create(universe_type, entity_name)
            elif not universe.is_active:
                universe = self.universe_repo.set_active(universe, True)

            payload["universe_id"] = universe.id
            payload["review_date"] = date.fromisoformat(payload["review_date"])
            self.reviews.create(ReviewCreate(**payload))
            count += 1
        return count

    def _match_option_label(self, field_key: str, raw: str) -> str | None:
        """Return display label for a matching active option, else None."""
        for opt in self.options.list_active(field_key):
            if opt.value.lower() == raw.lower() or opt.label.lower() == raw.lower():
                return opt.label
        return None

    def _resolve_option_value(
        self,
        field_key: str,
        raw: str | None,
        row_number: int,
        field_label: str,
        errors: list[ImportRowError],
    ) -> str | None:
        if not raw:
            return None
        try:
            self.options.assert_allowed(field_key, raw)
            return raw
        except FieldOptionServiceError:
            pass
        for opt in self.options.list_active(field_key):
            if opt.label.lower() == raw.lower() or opt.value.lower() == raw.lower():
                try:
                    self.options.assert_allowed(field_key, opt.value)
                    return opt.value
                except FieldOptionServiceError:
                    break
        errors.append(
            ImportRowError(
                row_number=row_number,
                field=field_label,
                message=(
                    f"'{raw}' değeri Ayarlar'da tanımlı değil. "
                    f"Lütfen '{field_label}' için geçerli bir seçenek girin."
                ),
            )
        )
        return None


def _as_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _soft_str(value: object) -> str | None:
    return _as_str(value)
