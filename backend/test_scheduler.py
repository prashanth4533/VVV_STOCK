"""
Test Scheduler — runs EOD pipeline every 2 minutes instead of daily 9 PM.
Only used for local verification. Remove or ignore before production deploy.

Usage:
    cd backend
    python test_scheduler.py

Press Ctrl+C to stop.
"""

import time
from datetime import datetime

from app import create_app
from app.services.eod_delivery_service import EODDeliveryService

INTERVAL_SECONDS = 120  # 2 minutes


def run_once():
    app = create_app()
    with app.app_context():
        print(f"\n[Scheduler] {datetime.now().strftime('%H:%M:%S')} — triggering EOD run", flush=True)
        result = EODDeliveryService.run(force=True)
        print(f"[Scheduler] Result: {result}", flush=True)


if __name__ == "__main__":
    print(f"[Scheduler] Test scheduler started. Running every {INTERVAL_SECONDS}s. Ctrl+C to stop.")
    print(f"[Scheduler] Provider: file  →  reports written to backend/eod_reports.log\n")

    run_once()  # fire immediately on start

    while True:
        print(f"[Scheduler] Next run in {INTERVAL_SECONDS}s ...", flush=True)
        time.sleep(INTERVAL_SECONDS)
        run_once()
