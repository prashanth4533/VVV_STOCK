from app import db


class DailyReport(db.Model):
    """One row per business day. Stores the computed metrics snapshot and the
    rendered WhatsApp message so the report is reproducible and auditable.

    NOTE: distinct from EODHistory/EODDraft (the physical stock-count feature).
    This is the daily business *summary report* delivered over WhatsApp.
    """

    __tablename__ = "daily_reports"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    # report_date is UNIQUE -> doubles as the idempotency key. A re-run or a
    # second gunicorn worker that tries to insert the same date loses cleanly.
    report_date = db.Column(db.Date, nullable=False, unique=True)
    payload_json = db.Column(db.JSON, nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum("generated", "sent", "partial", "failed", name="daily_report_status"),
        nullable=False,
        default="generated",
    )
    generated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )

    # Relationships
    deliveries = db.relationship(
        "ReportDelivery",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (db.Index("ix_daily_reports_date", "report_date"),)

    def __repr__(self):
        return f"<DailyReport {self.report_date} status={self.status}>"
