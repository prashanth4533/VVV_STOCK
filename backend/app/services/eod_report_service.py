"""
EODReportService
================
Computes the End-of-Day business summary for a given date and persists it as a
DailyReport row (idempotent on report_date).

This is the *report engine* only. It does NOT format or send WhatsApp messages —
that is the job of MessageFormatter and the WhatsApp providers. Keeping these
separate means the metrics can be unit-tested without any external calls.

Metric definitions
-------------------
Sales / Purchases : only `confirmed` documents dated on report_date.
Inventory         : point-in-time snapshot of active (non-deleted) products,
                    taken at generation time.
Stock activity    : stock_transactions dated on report_date.
Stock value       : current_stock * purchase_price.
                    Closing value  = current total stock value.
                    Net change     = sum(quantity_change * purchase_price) for
                                     transactions on report_date.
                    Opening value  = Closing value - Net change.
                    (Self-consistent: closing - opening == net change.)
"""

from datetime import date as date_cls
from decimal import Decimal

from sqlalchemy import func

from app import db
from app.models.daily_report import DailyReport
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.stock_transaction import StockTransaction

TOP_PRODUCTS_LIMIT = 5


def _money(value) -> float:
    """Normalise a Decimal/None money value to a 2dp float for JSON."""
    if value is None:
        return 0.0
    return float(Decimal(value).quantize(Decimal("0.01")))


class EODReportService:
    # ─── Public API ───────────────────────────────────────────────────────────

    @staticmethod
    def compute(report_date: date_cls) -> dict:
        """Compute the full metrics snapshot for report_date. Pure read-only —
        does not touch daily_reports. Returns a JSON-serialisable dict."""
        return {
            "report_date": report_date.isoformat(),
            "sales": EODReportService._sales_summary(report_date),
            "purchases": EODReportService._purchase_summary(report_date),
            "inventory": EODReportService._inventory_summary(),
            "stock_activity": EODReportService._stock_activity(report_date),
            "snapshot": EODReportService._business_snapshot(report_date),
        }

    @staticmethod
    def generate(report_date: date_cls, message_text: str = "") -> DailyReport:
        """Compute metrics and persist (idempotent upsert on report_date).

        If a report already exists for the date it is refreshed in place rather
        than duplicated. `message_text` is optional here so the engine can be
        run standalone; the cron job passes the rendered message.
        """
        payload = EODReportService.compute(report_date)

        try:
            report = DailyReport.query.filter_by(report_date=report_date).first()
            if report is None:
                report = DailyReport(report_date=report_date)
                db.session.add(report)

            report.payload_json = payload
            report.message_text = message_text
            # Only reset status if it hasn't been promoted to sent/partial/failed.
            if report.status not in ("sent", "partial", "failed"):
                report.status = "generated"
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError(f"EOD report generate failed: {exc}") from exc

        return report

    # ─── Sales ──────────────────────────────────────────────────────────────

    @staticmethod
    def _sales_summary(report_date: date_cls) -> dict:
        total_amount, txn_count = (
            db.session.query(
                func.coalesce(func.sum(Sale.total_amount), 0),
                func.count(Sale.id),
            )
            .filter(Sale.sale_date == report_date, Sale.status == "confirmed")
            .one()
        )

        total_qty = (
            db.session.query(func.coalesce(func.sum(SaleItem.quantity), 0))
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(Sale.sale_date == report_date, Sale.status == "confirmed")
            .scalar()
        )

        top_rows = (
            db.session.query(
                Product.brand,
                Product.item,
                func.sum(SaleItem.quantity).label("qty"),
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .join(Product, SaleItem.product_id == Product.id)
            .filter(Sale.sale_date == report_date, Sale.status == "confirmed")
            .group_by(Product.id, Product.brand, Product.item)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(TOP_PRODUCTS_LIMIT)
            .all()
        )

        return {
            "total_amount": _money(total_amount),
            "transaction_count": int(txn_count or 0),
            "total_quantity": int(total_qty or 0),
            "top_products": [
                {"name": f"{brand} {item}".strip(), "quantity": int(qty)}
                for brand, item, qty in top_rows
            ],
        }

    # ─── Purchases ────────────────────────────────────────────────────────────

    @staticmethod
    def _purchase_summary(report_date: date_cls) -> dict:
        total_amount, txn_count = (
            db.session.query(
                func.coalesce(func.sum(Purchase.total_amount), 0),
                func.count(Purchase.id),
            )
            .filter(
                Purchase.purchase_date == report_date,
                Purchase.status == "confirmed",
            )
            .one()
        )

        total_qty = (
            db.session.query(func.coalesce(func.sum(PurchaseItem.quantity), 0))
            .join(Purchase, PurchaseItem.purchase_id == Purchase.id)
            .filter(
                Purchase.purchase_date == report_date,
                Purchase.status == "confirmed",
            )
            .scalar()
        )

        return {
            "total_amount": _money(total_amount),
            "transaction_count": int(txn_count or 0),
            "total_quantity": int(total_qty or 0),
        }

    # ─── Inventory (point-in-time) ──────────────────────────────────────────────

    @staticmethod
    def _inventory_summary() -> dict:
        active = Product.query.filter(Product.deleted_at.is_(None))

        total_products = active.count()
        total_stock = (
            db.session.query(func.coalesce(func.sum(Product.current_stock), 0))
            .filter(Product.deleted_at.is_(None))
            .scalar()
        )
        out_of_stock = active.filter(Product.current_stock == 0).count()
        low_stock = active.filter(
            Product.current_stock > 0,
            Product.current_stock <= Product.reorder_level,
        ).count()
        # Reorder required = at or below reorder level (includes out-of-stock).
        reorder_required = active.filter(
            Product.current_stock <= Product.reorder_level
        ).count()

        return {
            "total_products": int(total_products),
            "total_stock_on_hand": int(total_stock or 0),
            "low_stock_products": int(low_stock),
            "out_of_stock_products": int(out_of_stock),
            "reorder_required_products": int(reorder_required),
        }

    # ─── Stock activity ─────────────────────────────────────────────────────────

    @staticmethod
    def _stock_activity(report_date: date_cls) -> dict:
        rows = (
            db.session.query(
                StockTransaction.transaction_type,
                func.count(StockTransaction.id),
            )
            .filter(StockTransaction.transaction_date == report_date)
            .group_by(StockTransaction.transaction_type)
            .all()
        )
        counts = {ttype: int(c) for ttype, c in rows}
        return {
            "stock_in_transactions": counts.get("STOCK_IN", 0),
            "stock_adjustment_transactions": counts.get("ADJUSTMENT", 0),
        }

    # ─── Business snapshot (stock value) ────────────────────────────────────────

    @staticmethod
    def _business_snapshot(report_date: date_cls) -> dict:
        closing_value = (
            db.session.query(
                func.coalesce(
                    func.sum(Product.current_stock * Product.purchase_price), 0
                )
            )
            .filter(Product.deleted_at.is_(None))
            .scalar()
        )

        # Value of net stock movement on report_date, priced at current cost.
        net_change = (
            db.session.query(
                func.coalesce(
                    func.sum(
                        StockTransaction.quantity_change * Product.purchase_price
                    ),
                    0,
                )
            )
            .join(Product, StockTransaction.product_id == Product.id)
            .filter(StockTransaction.transaction_date == report_date)
            .scalar()
        )

        closing = Decimal(closing_value or 0)
        net = Decimal(net_change or 0)
        opening = closing - net

        return {
            "opening_stock_value": _money(opening),
            "closing_stock_value": _money(closing),
            "net_stock_change": _money(net),
        }
