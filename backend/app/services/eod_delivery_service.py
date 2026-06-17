"""
EODDeliveryService
==================
Orchestrates the nightly pipeline:

    Generate report -> Format message -> Send to each recipient (with retry)
    -> Log each delivery -> Roll up report status.

Called by the cron entrypoint (app/jobs/run_eod.py) and by the Admin
"Run now" / "Test send" endpoints. All timing lives in the cron schedule; this
service just does the work once when asked.

Idempotency:
    * daily_reports.report_date is UNIQUE  -> can't double-generate a date.
    * eod.last_run_date guard              -> a normal run skips a date already
                                              completed (override with force=True).
"""

import time
from datetime import date as date_cls, datetime
from zoneinfo import ZoneInfo

from app import db
from app.models.daily_report import DailyReport
from app.models.report_delivery import ReportDelivery
from app.services.eod_report_service import EODReportService
from app.services.message_formatter import MessageFormatter
from app.services.settings_service import SettingsService
from app.services.whatsapp import get_provider
from app.services.whatsapp.base import WhatsAppError

# Backoff between send attempts (seconds). len() == max attempts.
DEFAULT_BACKOFF = [5, 30, 120]


class EODDeliveryService:
    @staticmethod
    def _today(tz_name: str) -> date_cls:
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Asia/Kolkata")
        return datetime.now(tz).date()

    # ─── main entrypoint ────────────────────────────────────────────────────

    @staticmethod
    def run(
        report_date: date_cls | None = None,
        force: bool = False,
        dry_run: bool = False,
        backoff: list[int] | None = None,
        sleep=time.sleep,
    ) -> dict:
        """Generate and deliver the EOD report.

        force   : ignore the enabled flag and last_run_date guard.
        dry_run : generate + render but do NOT send (no provider calls).
        Returns a summary dict for the caller / API response.
        """
        config = SettingsService.get_eod_config()
        backoff = backoff or DEFAULT_BACKOFF

        if not config["enabled"] and not force:
            return {"skipped": True, "reason": "EOD WhatsApp delivery is disabled."}

        report_date = report_date or EODDeliveryService._today(config["timezone"])

        if (
            not force
            and not dry_run
            and config["last_run_date"] == report_date.isoformat()
        ):
            return {
                "skipped": True,
                "reason": f"Already completed for {report_date.isoformat()}.",
            }

        # 1) compute + render + persist (idempotent on report_date)
        payload = EODReportService.compute(report_date)
        message_text = MessageFormatter.render_text(payload)
        report = EODReportService.generate(report_date, message_text=message_text)

        if dry_run:
            return {
                "report_id": report.id,
                "report_date": report_date.isoformat(),
                "dry_run": True,
                "message_text": message_text,
                "recipients": config["recipients"],
            }

        recipients = config["recipients"]
        if not recipients:
            report.status = "failed"
            db.session.commit()
            return {
                "report_id": report.id,
                "report_date": report_date.isoformat(),
                "error": "No recipients configured (eod.recipients).",
            }

        # 2) send to each recipient with retry + per-recipient logging
        provider = get_provider(config["provider"])
        use_template = bool(config["template_name"])
        params = (
            MessageFormatter.render_template_params(payload) if use_template else None
        )

        results = []
        sent = failed = 0
        for recipient in recipients:
            delivery = ReportDelivery(
                report_id=report.id,
                recipient=recipient,
                channel="whatsapp",
                provider=provider.name,
                status="pending",
            )
            db.session.add(delivery)
            db.session.flush()  # assign id

            ok = EODDeliveryService._send_with_retry(
                provider=provider,
                delivery=delivery,
                recipient=recipient,
                message_text=message_text,
                use_template=use_template,
                template_name=config["template_name"],
                template_lang=config["template_lang"],
                params=params,
                backoff=backoff,
                sleep=sleep,
            )
            sent += 1 if ok else 0
            failed += 0 if ok else 1
            results.append(
                {
                    "recipient": recipient,
                    "status": delivery.status,
                    "error": delivery.error_message,
                }
            )

        # 3) roll up report status
        if failed == 0:
            report.status = "sent"
        elif sent == 0:
            report.status = "failed"
        else:
            report.status = "partial"

        db.session.commit()

        # 4) record completion (only on a non-failed run, so a fully failed run retries next time)
        if report.status in ("sent", "partial"):
            SettingsService.set("eod.last_run_date", report_date.isoformat())

        return {
            "report_id": report.id,
            "report_date": report_date.isoformat(),
            "status": report.status,
            "sent": sent,
            "failed": failed,
            "results": results,
        }

    # ─── send + retry for a single recipient ──────────────────────────────────

    @staticmethod
    def _send_with_retry(
        provider,
        delivery: ReportDelivery,
        recipient: str,
        message_text: str,
        use_template: bool,
        template_name: str,
        template_lang: str,
        params,
        backoff: list[int],
        sleep,
    ) -> bool:
        last_error = None
        for attempt in range(1, len(backoff) + 1):
            delivery.attempt_count = attempt
            try:
                if use_template:
                    result = provider.send_template(
                        recipient, template_name, template_lang, params
                    )
                else:
                    result = provider.send_text(recipient, message_text)

                if result.success:
                    delivery.status = "sent"
                    delivery.provider_msg_id = result.provider_msg_id
                    delivery.error_message = None
                    delivery.sent_at = datetime.utcnow()
                    return True

                last_error = result.error or "unknown send failure"
            except WhatsAppError as exc:
                last_error = str(exc)
                if not exc.retryable:
                    break  # permanent error -> stop retrying
            except Exception as exc:  # noqa: BLE001 - never let one recipient kill the run
                last_error = f"unexpected: {exc}"

            # backoff before next attempt (skip wait after the final attempt)
            if attempt < len(backoff):
                sleep(backoff[attempt - 1])

        delivery.status = "failed"
        delivery.error_message = last_error
        return False

    # ─── Admin "Test Send" ────────────────────────────────────────────────────

    @staticmethod
    def send_test(recipient: str) -> dict:
        """Send a one-off test message to a single number. Uses free-form text
        (works inside the 24h window) so it needs no template approval."""
        provider = get_provider()
        body = (
            "✅ VVV STOCK — test message.\n"
            "If you can read this, EOD WhatsApp delivery is wired up correctly."
        )
        try:
            result = provider.send_text(recipient, body)
        except WhatsAppError as exc:
            return {"success": False, "error": str(exc)}
        return {
            "success": result.success,
            "provider_msg_id": result.provider_msg_id,
            "error": result.error,
        }
