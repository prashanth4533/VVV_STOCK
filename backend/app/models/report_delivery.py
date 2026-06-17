from app import db


class ReportDelivery(db.Model):
    """One row per send attempt per recipient for a DailyReport.

    Tracks WhatsApp delivery status, provider message id, retry count and the
    last error so the Admin UI can surface what happened.
    """

    __tablename__ = "report_deliveries"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("daily_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient = db.Column(db.String(64), nullable=False)  # phone number or group id
    channel = db.Column(db.String(16), nullable=False, default="whatsapp")
    provider = db.Column(db.String(32), nullable=False)  # 'meta' | 'green_api' | ...
    status = db.Column(
        db.Enum("pending", "sent", "delivered", "failed", name="report_delivery_status"),
        nullable=False,
        default="pending",
    )
    provider_msg_id = db.Column(db.String(128), nullable=True)
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Relationships
    report = db.relationship("DailyReport", back_populates="deliveries")

    __table_args__ = (
        db.Index("ix_deliveries_report", "report_id"),
        db.Index("ix_deliveries_status", "status"),
    )

    def __repr__(self):
        return f"<ReportDelivery report={self.report_id} to={self.recipient} status={self.status}>"
