"""
EOD WhatsApp Report — Admin API
===============================
GET  /api/v1/eod/settings           current config
PUT  /api/v1/eod/settings           update config (enable, time, recipients, ...)
POST /api/v1/eod/test-send          {"recipient": "9198..."} one-off test message
POST /api/v1/eod/run                trigger a run now ({"force": true, "dry_run": false})
GET  /api/v1/eod/reports            recent reports + delivery summary
GET  /api/v1/eod/reports/<date>     one report (message + per-recipient deliveries)

Secrets (Meta token, phone-number-id) are NOT exposed or set here — they live
in environment variables.
"""

import json
import re
from datetime import date

from flask import Blueprint, request

from app.models.daily_report import DailyReport
from app.services.eod_delivery_service import EODDeliveryService
from app.services.settings_service import SettingsService
from app.utils.response import success, error

bp = Blueprint("eod", __name__, url_prefix="/api/v1/eod")

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_ALLOWED_PROVIDERS = {"meta", "file"}


# ─── GET /settings ───────────────────────────────────────────────────────────


@bp.route("/settings", methods=["GET"])
def get_settings():
    return success(SettingsService.get_eod_config())


# ─── PUT /settings ───────────────────────────────────────────────────────────


@bp.route("/settings", methods=["PUT"])
def update_settings():
    data = request.get_json(silent=True) or {}
    errors = {}

    if "enabled" in data:
        if not isinstance(data["enabled"], bool):
            errors["enabled"] = "must be a boolean."

    if "schedule_time" in data:
        if not isinstance(data["schedule_time"], str) or not _TIME_RE.match(
            data["schedule_time"]
        ):
            errors["schedule_time"] = "must be HH:MM (24h)."

    if "provider" in data and data["provider"] not in _ALLOWED_PROVIDERS:
        errors["provider"] = f"must be one of {sorted(_ALLOWED_PROVIDERS)}."

    if "recipients" in data:
        rec = data["recipients"]
        if not isinstance(rec, list) or not all(isinstance(x, str) for x in rec):
            errors["recipients"] = "must be a list of phone-number strings."
        elif any(not re.fullmatch(r"\d{8,15}", x.strip()) for x in rec if x.strip()):
            errors["recipients"] = "each number must be 8-15 digits, country code, no +."

    if errors:
        return error("VALIDATION_ERROR", "Invalid settings.", 400, errors)

    # Persist each provided key under its eod.* name.
    mapping = {
        "enabled": ("eod.enabled", lambda v: "true" if v else "false"),
        "schedule_time": ("eod.schedule_time", str),
        "timezone": ("eod.timezone", str),
        "provider": ("eod.provider", str),
        "recipients": ("eod.recipients", lambda v: json.dumps([x.strip() for x in v])),
        "template_name": ("eod.template_name", str),
        "template_lang": ("eod.template_lang", str),
    }
    for field, (key, cast) in mapping.items():
        if field in data:
            SettingsService.set(key, cast(data[field]))

    return success(SettingsService.get_eod_config())


# ─── POST /test-send ─────────────────────────────────────────────────────────


@bp.route("/test-send", methods=["POST"])
def test_send():
    data = request.get_json(silent=True) or {}
    recipient = (data.get("recipient") or "").strip()
    if not re.fullmatch(r"\d{8,15}", recipient):
        return error(
            "VALIDATION_ERROR",
            "recipient must be 8-15 digits, country code, no +.",
            400,
        )
    result = EODDeliveryService.send_test(recipient)
    if not result.get("success"):
        return error("SEND_FAILED", result.get("error") or "Send failed.", 502, result)
    return success(result)


# ─── POST /run ───────────────────────────────────────────────────────────────


@bp.route("/run", methods=["POST"])
def run_now():
    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", True))  # manual run defaults to force
    dry_run = bool(data.get("dry_run", False))
    report_date = None
    if data.get("date"):
        try:
            report_date = date.fromisoformat(data["date"])
        except ValueError:
            return error("VALIDATION_ERROR", "date must be YYYY-MM-DD.", 400)

    try:
        result = EODDeliveryService.run(
            report_date=report_date, force=force, dry_run=dry_run
        )
    except Exception as exc:  # noqa: BLE001
        return error("INTERNAL_ERROR", str(exc), 500)
    return success(result)


# ─── GET /reports ────────────────────────────────────────────────────────────


@bp.route("/reports", methods=["GET"])
def list_reports():
    limit = min(int(request.args.get("limit", 30)), 100)
    reports = (
        DailyReport.query.order_by(DailyReport.report_date.desc()).limit(limit).all()
    )
    out = []
    for r in reports:
        deliveries = r.deliveries.all()
        out.append(
            {
                "report_date": r.report_date.isoformat(),
                "status": r.status,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "delivery_count": len(deliveries),
                "delivered": sum(1 for d in deliveries if d.status == "sent"),
                "failed": sum(1 for d in deliveries if d.status == "failed"),
            }
        )
    return success(out)


# ─── GET /reports/<date> ──────────────────────────────────────────────────────


@bp.route("/reports/<report_date>", methods=["GET"])
def get_report(report_date: str):
    try:
        d = date.fromisoformat(report_date)
    except ValueError:
        return error("VALIDATION_ERROR", "date must be YYYY-MM-DD.", 400)

    r = DailyReport.query.filter_by(report_date=d).first()
    if not r:
        return error("NOT_FOUND", f"No report for {report_date}.", 404)

    return success(
        {
            "report_date": r.report_date.isoformat(),
            "status": r.status,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "message_text": r.message_text,
            "payload": r.payload_json,
            "deliveries": [
                {
                    "recipient": d.recipient,
                    "provider": d.provider,
                    "status": d.status,
                    "attempt_count": d.attempt_count,
                    "provider_msg_id": d.provider_msg_id,
                    "error_message": d.error_message,
                    "sent_at": d.sent_at.isoformat() if d.sent_at else None,
                }
                for d in r.deliveries.all()
            ],
        }
    )
