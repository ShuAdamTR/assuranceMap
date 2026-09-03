"""Alan anahtar sabitleri — değer listeleri burada DEĞİL; FieldOption tablosunda yönetilir."""

from __future__ import annotations

from enum import Enum


class UniverseType(str, Enum):
    ISTIRAK = "istirak"
    MUDURLUK = "mudurluk"
    URUN = "urun"


UNIVERSE_TYPE_LABELS: dict[str, str] = {
    UniverseType.ISTIRAK.value: "İştirak",
    UniverseType.MUDURLUK.value: "Müdürlük",
    UniverseType.URUN.value: "Ürün",
}

# Whitelist ile yönetilen review alanları
FIELD_UNIT = "unit"
FIELD_REVIEW_STATUS = "review_status"
FIELD_ASSURANCE_LEVEL = "assurance_level"
FIELD_RISK_LEVEL = "risk_level"
FIELD_EXAMINATION_DEPTH = "examination_depth"

FIELD_KEYS: tuple[str, ...] = (
    FIELD_UNIT,
    FIELD_REVIEW_STATUS,
    FIELD_ASSURANCE_LEVEL,
    FIELD_RISK_LEVEL,
    FIELD_EXAMINATION_DEPTH,
)

FIELD_KEY_LABELS: dict[str, str] = {
    FIELD_UNIT: "Birim",
    FIELD_REVIEW_STATUS: "İnceleme Durumu",
    FIELD_ASSURANCE_LEVEL: "Güvence Seviyesi",
    FIELD_RISK_LEVEL: "Risk Seviyesi",
    FIELD_EXAMINATION_DEPTH: "İnceleme Derinliği",
}

DEPTH_TAM = "tam"
DEPTH_KISMI = "kismi"

SETTING_VALIDITY_YEARS = "review_validity_years"
DEFAULT_VALIDITY_YEARS = 4

SETTING_UNIT_ACTIVITY_MAP = "unit_activity_map"
DEFAULT_UNIT_ACTIVITY_MAP: dict[str, str] = {
    "KBU": "uyum",
    "KBD": "denetim",
}

ACTIVITY_UYUM = "uyum"
ACTIVITY_DENETIM = "denetim"
ACTIVITY_LABELS: dict[str, str] = {
    ACTIVITY_UYUM: "Uyum",
    ACTIVITY_DENETIM: "Denetim",
}

# Evren haritası — sabit 3 yıllık pencere
MAP_WINDOW_YEARS = 3

MAP_COLOR_MULTI_FULL = "#70AD47"
MAP_COLOR_MULTI_MIXED = "#A9D08E"
MAP_COLOR_ONCE_FULL = "#C6E0B4"
MAP_COLOR_ONCE_PARTIAL = "#E2EFDA"
MAP_COLOR_OLD_ONLY = "#FFD966"
MAP_COLOR_NEVER = "#D9D9D9"

MAP_COLOR_LABELS: dict[str, str] = {
    MAP_COLOR_MULTI_FULL: "Son 3 yılda birden fazla ve tam incelendi",
    MAP_COLOR_MULTI_MIXED: "Son 3 yılda birden fazla; tam + kısmi karışık",
    MAP_COLOR_ONCE_FULL: "Son 3 yılda bir defa ve tam incelendi",
    MAP_COLOR_ONCE_PARTIAL: "Son 3 yılda bir defa ve kısmi incelendi",
    MAP_COLOR_OLD_ONLY: "Yalnızca son 3 yıl dışında incelendi",
    MAP_COLOR_NEVER: "Hiç inceleme kapsamına alınmadı",
}

MAP_SYMBOL_BOTH_RECENT = "◆"
MAP_SYMBOL_BOTH_OLD = "◇"
MAP_SYMBOL_UYUM_RECENT = "■"
MAP_SYMBOL_UYUM_OLD = "□"
MAP_SYMBOL_DENETIM_RECENT = "▲"
MAP_SYMBOL_DENETIM_OLD = "△"

MAP_SYMBOL_LABELS: dict[str, str] = {
    MAP_SYMBOL_BOTH_RECENT: "Son 3 yılda hem Uyum hem Denetim (örtüşme)",
    MAP_SYMBOL_BOTH_OLD: "Son 3 yıldan önce hem Uyum hem Denetim (örtüşme)",
    MAP_SYMBOL_UYUM_RECENT: "Son 3 yılda Uyum",
    MAP_SYMBOL_UYUM_OLD: "Son 3 yıldan önce Uyum",
    MAP_SYMBOL_DENETIM_RECENT: "Son 3 yılda Denetim",
    MAP_SYMBOL_DENETIM_OLD: "Son 3 yıldan önce Denetim",
}

# Durum renkleri (dashboard)
STATUS_GRAY = "GRAY"
STATUS_GREEN = "GREEN"
STATUS_ORANGE = "ORANGE"

STATUS_COLOR_LABELS: dict[str, str] = {
    STATUS_GRAY: "Hiç İncelenmeyen",
    STATUS_GREEN: "Güncel",
    STATUS_ORANGE: "4+ Yıl Geçen",
}

STATUS_HEX: dict[str, str] = {
    STATUS_GRAY: "#9ca3af",
    STATUS_GREEN: "#16a34a",
    STATUS_ORANGE: "#ea580c",
}
