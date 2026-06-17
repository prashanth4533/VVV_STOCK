"""daily report + delivery tables (WhatsApp EOD report feature)

Revision ID: 002_daily_reports
Revises: 001_initial
Create Date: 2026-06-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "002_daily_reports"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # Daily Reports
    op.create_table(
        "daily_reports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "generated", "sent", "partial", "failed", name="daily_report_status"
            ),
            nullable=False,
            server_default="generated",
        ),
        sa.Column(
            "generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_date", name="uq_daily_reports_date"),
    )
    op.create_index("ix_daily_reports_date", "daily_reports", ["report_date"])

    # Report Deliveries
    op.create_table(
        "report_deliveries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("report_id", sa.BigInteger(), nullable=False),
        sa.Column("recipient", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False, server_default="whatsapp"),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "sent", "delivered", "failed", name="report_delivery_status"
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("provider_msg_id", sa.String(128), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["report_id"], ["daily_reports.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_deliveries_report", "report_deliveries", ["report_id"])
    op.create_index("ix_deliveries_status", "report_deliveries", ["status"])


def downgrade():
    op.drop_table("report_deliveries")
    op.drop_table("daily_reports")

    op.execute("DROP TYPE IF EXISTS report_delivery_status")
    op.execute("DROP TYPE IF EXISTS daily_report_status")
