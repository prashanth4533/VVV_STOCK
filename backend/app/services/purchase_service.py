"""
PurchaseService
===============
Manages the full purchase lifecycle:

  create()          — build PO, create items, call StockService.stock_in(), commit
  get_all()         — paginated list with optional filters
  get_by_id()       — full detail (header + items)
  cancel()          — reverse stock via StockService.stock_out(), mark cancelled
  next_number()     — generate next PO-XXXX number (server-side, safe under load)
"""

from datetime import date, datetime

from sqlalchemy import func

from app import db
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.supplier import Supplier
from app.models.product import Product
from app.services.stock_service import StockService


class PurchaseService:
    # ─── Number generation ────────────────────────────────────────────────────

    @staticmethod
    def next_number() -> str:
        """
        Compute the next purchase number as PO-XXXX.
        Scans MAX(purchase_no) to stay correct even after cancellations or gaps.
        Thread-safe: runs in the same DB transaction as the INSERT.
        """
        result = db.session.query(func.max(Purchase.purchase_no)).scalar()
        if result:
            try:
                seq = int(result.split("-")[1]) + 1
            except (IndexError, ValueError):
                seq = 1
        else:
            seq = 1
        return f"PO-{seq:04d}"

    # ─── Queries ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_all(
        supplier_id: int = None,
        from_date=None,
        to_date=None,
        search: str = None,
        page: int = 1,
        per_page: int = 50,
    ):
        """Paginated purchase list — header only, no items detail."""
        from sqlalchemy.orm import joinedload

        query = Purchase.query.options(joinedload(Purchase.supplier))

        if supplier_id:
            query = query.filter(Purchase.supplier_id == supplier_id)

        if from_date:
            query = query.filter(Purchase.purchase_date >= from_date)

        if to_date:
            query = query.filter(Purchase.purchase_date <= to_date)

        if search:
            pattern = f"%{search}%"
            query = query.join(Supplier, Purchase.supplier_id == Supplier.id).filter(
                db.or_(
                    Purchase.purchase_no.ilike(pattern),
                    Purchase.invoice_number.ilike(pattern),
                    Supplier.name.ilike(pattern),
                )
            )

        query = query.order_by(
            Purchase.purchase_date.desc(),
            Purchase.id.desc(),
        )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        from app.schemas.purchase_schema import purchases_detail_schema
        from app.utils.pagination import build_meta

        return purchases_detail_schema.dump(pagination.items), build_meta(pagination)

    @staticmethod
    def get_by_id(purchase_id: int) -> dict:
        """Return full purchase detail including items and product info."""
        from sqlalchemy.orm import joinedload

        purchase = (
            Purchase.query.options(
                joinedload(Purchase.supplier),
                joinedload(Purchase.items).joinedload(PurchaseItem.product),
            )
            .filter(Purchase.id == purchase_id)
            .first()
        )
        if not purchase:
            raise LookupError(f"Purchase {purchase_id} not found.")

        from app.schemas.purchase_schema import purchase_detail_schema

        return purchase_detail_schema.dump(purchase)

    # ─── Create ───────────────────────────────────────────────────────────────

    @staticmethod
    def create(data: dict) -> dict:
        """
        Create a confirmed purchase:
        1. Validate supplier and all products.
        2. Generate purchase_no.
        3. INSERT Purchase + PurchaseItems.
        4. Call StockService.stock_in() for each item (handles stock + txn).
        5. Commit in a single transaction; rollback entirely on any failure.
        """
        # ── Validate supplier ──────────────────────────────────────────────
        supplier = Supplier.query.filter(
            Supplier.id == data["supplier_id"],
            Supplier.deleted_at.is_(None),
        ).first()
        if not supplier:
            raise LookupError(f"Supplier {data['supplier_id']} not found.")

        # ── Validate products + calculate totals ───────────────────────────
        items_data = data["items"]
        product_ids = [i["product_id"] for i in items_data]

        # Detect duplicate products in the same PO
        if len(product_ids) != len(set(product_ids)):
            raise ValueError(
                "Duplicate product_id entries in items — each product may appear only once."
            )

        products = {
            p.id: p
            for p in Product.query.filter(
                Product.id.in_(product_ids),
                Product.deleted_at.is_(None),
            ).all()
        }
        missing = set(product_ids) - set(products.keys())
        if missing:
            raise LookupError(f"Product(s) not found: {sorted(missing)}")

        tax_amount = float(data.get("tax_amount", 0.0))
        subtotal = sum(item["quantity"] * item["rate"] for item in items_data)
        total_amount = subtotal + tax_amount

        purchase_date = data.get("purchase_date") or date.today()

        try:
            purchase_no = PurchaseService.next_number()

            purchase = Purchase(
                purchase_no=purchase_no,
                purchase_date=purchase_date,
                supplier_id=data["supplier_id"],
                invoice_number=data.get("invoice_number"),
                notes=data.get("notes"),
                subtotal=round(subtotal, 2),
                tax_amount=round(tax_amount, 2),
                total_amount=round(total_amount, 2),
                status="confirmed",
            )
            db.session.add(purchase)
            db.session.flush()  # get purchase.id

            # ── Create line items ──────────────────────────────────────────
            for item in items_data:
                product = products[item["product_id"]]
                line_total = round(item["quantity"] * item["rate"], 2)
                pi = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    rate=round(item["rate"], 2),
                    line_total=line_total,
                )
                db.session.add(pi)

            db.session.flush()  # write items before stock mutations

            # ── Stock in for each item (within the same session) ──────────
            for item in items_data:
                StockService.create_transaction(
                    product=products[item["product_id"]],
                    txn_type="STOCK_IN",
                    quantity_change=item["quantity"],
                    ref_type="purchase",
                    ref_id=purchase.id,
                    notes=f"Purchase {purchase_no}",
                )

            db.session.commit()

        except (ValueError, LookupError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError(f"create purchase failed: {exc}") from exc

        return PurchaseService.get_by_id(purchase.id)

    # ─── Cancel ───────────────────────────────────────────────────────────────

    @staticmethod
    def cancel(purchase_id: int) -> dict:
        """
        Cancel a confirmed purchase:
        1. Guard against double-cancellation or cancelling a draft.
        2. Reverse stock for each line item via StockService.create_transaction().
        3. Mark purchase as cancelled.
        4. Commit in a single transaction.
        """
        from sqlalchemy.orm import joinedload

        purchase = (
            Purchase.query.options(
                joinedload(Purchase.items).joinedload(PurchaseItem.product),
            )
            .filter(Purchase.id == purchase_id)
            .first()
        )
        if not purchase:
            raise LookupError(f"Purchase {purchase_id} not found.")

        if purchase.status == "cancelled":
            raise ValueError("Purchase is already cancelled.")

        if purchase.status == "draft":
            raise ValueError(
                "Draft purchases cannot be cancelled via this endpoint — delete instead."
            )

        try:
            for item in purchase.items:
                product = (
                    Product.query.filter(
                        Product.id == item.product_id,
                        Product.deleted_at.is_(None),
                    )
                    .with_for_update()
                    .first()
                )

                if not product:
                    raise LookupError(
                        f"Product {item.product_id} not found during cancellation."
                    )

                # Prevent stock going below zero
                if product.current_stock < item.quantity:
                    raise ValueError(
                        f"Cannot cancel: product '{product.brand} {product.item}' "
                        f"has only {product.current_stock} units but PO had {item.quantity}. "
                        "Adjust stock first."
                    )

                StockService.create_transaction(
                    product=product,
                    txn_type="STOCK_OUT",
                    quantity_change=-item.quantity,
                    ref_type="purchase",
                    ref_id=purchase.id,
                    notes=f"Cancellation of {purchase.purchase_no}",
                )

            purchase.status = "cancelled"
            db.session.commit()

        except (ValueError, LookupError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError(f"cancel purchase failed: {exc}") from exc

        return PurchaseService.get_by_id(purchase_id)
