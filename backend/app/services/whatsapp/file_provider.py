"""FileProvider — writes EOD reports to a local file instead of sending WhatsApp.

Use this for local testing before a WhatsApp subscription is active.
Set  eod.provider = file  (via PUT /api/v1/eod/settings or directly in DB).
Reports are appended to  backend/eod_reports.log  (one delivery per entry).
"""

import os
from datetime import datetime

from app.services.whatsapp.base import WhatsAppProvider, SendResult

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "eod_reports.log")
LOG_PATH = os.path.normpath(LOG_PATH)


class FileProvider(WhatsAppProvider):
    name = "file"

    def send_text(self, to: str, message: str) -> SendResult:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"\n{'='*60}\n"
            f"[{timestamp}] TO: {to}\n"
            f"{'='*60}\n"
            f"{message}\n"
        )
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"[FileProvider] Report written to {LOG_PATH}", flush=True)
        return SendResult(success=True, provider_msg_id=f"file-{timestamp}")

    def send_template(self, to: str, template_name: str, lang: str, params: list) -> SendResult:
        # For file provider, render template params as labelled text
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        param_lines = "\n".join(f"  {{{{{i+1}}}}}: {v}" for i, v in enumerate(params))
        entry = (
            f"\n{'='*60}\n"
            f"[{timestamp}] TO: {to}  TEMPLATE: {template_name} ({lang})\n"
            f"{'='*60}\n"
            f"{param_lines}\n"
        )
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"[FileProvider] Template delivery written to {LOG_PATH}", flush=True)
        return SendResult(success=True, provider_msg_id=f"file-tpl-{timestamp}")
