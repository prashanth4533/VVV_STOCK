"""
EOD report cron entrypoint
==========================
Run once and exit. Designed to be triggered by Railway Cron (or any external
scheduler) at the configured time, e.g.:

    Cron schedule : 0 21 * * *      (set service TZ to Asia/Kolkata)
    Start command : python -m app.jobs.run_eod

Running as a separate one-shot process (not inside the gunicorn web workers)
avoids the double-fire that an in-process scheduler would cause with
`gunicorn --workers 2`.

Flags (optional):
    --force      ignore the enabled flag and last-run guard
    --dry-run    generate + render but do not send
    --date=YYYY-MM-DD   run for a specific date instead of "today"

Exit code is 0 on success/skip, 1 on hard failure (so the scheduler can alert).
"""

import sys
from datetime import date

from app import create_app
from app.services.eod_delivery_service import EODDeliveryService


def _parse_args(argv: list[str]) -> dict:
    opts = {"force": False, "dry_run": False, "report_date": None}
    for arg in argv:
        if arg == "--force":
            opts["force"] = True
        elif arg == "--dry-run":
            opts["dry_run"] = True
        elif arg.startswith("--date="):
            opts["report_date"] = date.fromisoformat(arg.split("=", 1)[1])
    return opts


def main(argv: list[str] | None = None) -> int:
    opts = _parse_args(argv if argv is not None else sys.argv[1:])
    app = create_app()
    with app.app_context():
        try:
            result = EODDeliveryService.run(
                report_date=opts["report_date"],
                force=opts["force"],
                dry_run=opts["dry_run"],
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[EOD] FAILED: {exc}", flush=True)
            return 1

    print(f"[EOD] {result}", flush=True)
    # A run that produced a fully-failed report is a soft failure worth alerting.
    if result.get("status") == "failed" or result.get("error"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
