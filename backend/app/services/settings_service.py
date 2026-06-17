"""
SettingsService
===============
Typed accessor over the `settings` key-value table for the EOD feature.

Keys (all prefixed `eod.`):
    eod.enabled        "true" | "false"            -- master on/off switch
    eod.schedule_time  "21:00"                     -- HH:MM, informational (cron owns timing)
    eod.timezone       "Asia/Kolkata"
    eod.provider       "meta"
    eod.recipients     JSON list of phone numbers  -- ["9198...", "9197..."]
    eod.template_name  "vvv_eod_report"            -- approved Meta template
    eod.template_lang  "en"
    eod.last_run_date  "2026-06-16"                -- secondary idempotency guard
"""

import json

from app import db
from app.models.setting import Setting

DEFAULTS = {
    "eod.enabled": "false",
    "eod.schedule_time": "21:00",
    "eod.timezone": "Asia/Kolkata",
    "eod.provider": "meta",
    "eod.recipients": "[]",
    "eod.template_name": "",
    "eod.template_lang": "en",
    "eod.last_run_date": "",
}


class SettingsService:
    @staticmethod
    def get(key: str, default=None):
        row = db.session.get(Setting, key)
        if row is not None and row.value is not None:
            return row.value
        if default is not None:
            return default
        return DEFAULTS.get(key)

    @staticmethod
    def set(key: str, value: str):
        row = db.session.get(Setting, key)
        if row is None:
            row = Setting(key_name=key, value=value)
            db.session.add(row)
        else:
            row.value = value
        db.session.commit()
        return row

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        val = SettingsService.get(key, "true" if default else "false")
        return str(val).strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def get_recipients() -> list[str]:
        raw = SettingsService.get("eod.recipients", "[]")
        try:
            data = json.loads(raw)
            return [str(x).strip() for x in data if str(x).strip()]
        except (ValueError, TypeError):
            return []

    @staticmethod
    def get_eod_config() -> dict:
        """Full EOD config bundle for the Admin UI / job."""
        return {
            "enabled": SettingsService.get_bool("eod.enabled"),
            "schedule_time": SettingsService.get("eod.schedule_time"),
            "timezone": SettingsService.get("eod.timezone"),
            "provider": SettingsService.get("eod.provider"),
            "recipients": SettingsService.get_recipients(),
            "template_name": SettingsService.get("eod.template_name"),
            "template_lang": SettingsService.get("eod.template_lang"),
            "last_run_date": SettingsService.get("eod.last_run_date"),
        }
