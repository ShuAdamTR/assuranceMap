from __future__ import annotations



import json



from sqlalchemy.orm import Session



from app.config.field_keys import (

    ACTIVITY_DENETIM,

    ACTIVITY_UYUM,

    DEFAULT_UNIT_ACTIVITY_MAP,

    DEFAULT_VALIDITY_YEARS,

    SETTING_UNIT_ACTIVITY_MAP,

    SETTING_VALIDITY_YEARS,

)

from app.repositories.settings_repo import SettingsRepository





class AppSettingsService:

    def __init__(self, session: Session) -> None:

        self.repo = SettingsRepository(session)



    def get_validity_years(self) -> int:

        raw = self.repo.get_value(SETTING_VALIDITY_YEARS, str(DEFAULT_VALIDITY_YEARS))

        try:

            return max(1, int(raw or DEFAULT_VALIDITY_YEARS))

        except ValueError:

            return DEFAULT_VALIDITY_YEARS



    def set_validity_years(self, years: int) -> None:

        if years < 1 or years > 50:

            raise ValueError("Geçerlilik süresi 1–50 arasında olmalıdır.")

        self.repo.set_value(SETTING_VALIDITY_YEARS, str(years))



    def get_unit_activity_map(self) -> dict[str, str]:

        raw = self.repo.get_value(SETTING_UNIT_ACTIVITY_MAP, None)

        if not raw:

            return dict(DEFAULT_UNIT_ACTIVITY_MAP)

        try:

            data = json.loads(raw)

        except json.JSONDecodeError:

            return dict(DEFAULT_UNIT_ACTIVITY_MAP)

        if not isinstance(data, dict):

            return dict(DEFAULT_UNIT_ACTIVITY_MAP)

        cleaned: dict[str, str] = {}

        for unit, activity in data.items():

            key = str(unit).strip()

            act = str(activity).strip().lower()

            if key and act in {ACTIVITY_UYUM, ACTIVITY_DENETIM}:

                cleaned[key] = act

        return cleaned or dict(DEFAULT_UNIT_ACTIVITY_MAP)



    def set_unit_activity_map(self, mapping: dict[str, str]) -> None:

        cleaned: dict[str, str] = {}

        for unit, activity in mapping.items():

            key = str(unit).strip()

            act = str(activity).strip().lower()

            if not key:

                continue

            if act not in {ACTIVITY_UYUM, ACTIVITY_DENETIM}:

                raise ValueError(

                    f"'{key}' için faaliyet türü Uyum veya Denetim olmalıdır."

                )

            cleaned[key] = act

        self.repo.set_value(

            SETTING_UNIT_ACTIVITY_MAP,

            json.dumps(cleaned, ensure_ascii=False),

        )



    def resolve_activity(self, unit: str) -> str | None:

        mapping = self.get_unit_activity_map()

        # Exact then case-insensitive

        if unit in mapping:

            return mapping[unit]

        for key, activity in mapping.items():

            if key.lower() == unit.lower():

                return activity

        return None

