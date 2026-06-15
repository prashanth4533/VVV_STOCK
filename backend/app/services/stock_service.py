"""
StockService
============
Centralised entry point for ALL stock mutations.

Every function:
  - Runs inside an explicit DB transaction (via db.session)
  - Updates products.current_stock atomically
  - Creates a stock_transactions record
  - Rolls back cleanly on any failure (raises RuntimeError with a message)

Public API
----------
  stock_in(product_id, quantity, notes, reference_type, reference_id, created_by)
  stock_in_batch(items, notes, created_by)
  stock_out(product_id, quantity, notes, reference_type, reference_id, created_by)
  adjust_stock(product_id, actual_stock, reason, notes, created_by)
  create_transaction(product, txn_type, quantity_change, ref_type, ref_id, reason, notes, created_by)
"""

from datetime import date, datetime

from app import db
from app.models.product import Product
from app.models.stock_transaction import StockTransaction


class StockService:
    # ─── Internal primitive ──────────────────────────────────────────────────

    @staticmethod
    def create_transaction(
        product: Product,
        txn_type: str,
        quantity_change: int,
        ref_type: str,
        ref_id: int = None,
        reason: str = None,
        notes: str = None,
        created_by: int = None,
    ) -> StockTransaction:
        """
        Low-level builder.  Does NOT commit — caller manages the transaction.
        Updates product.current_stock and appends a StockTransaction to the session.
        """
        previous_qty = product.current_stock
        new_qty = previous_qty + quantity_change

        product.current_stock = new_qty

        txn = StockTransaction(
            product_id=product.id,
            transaction_type=txn_type,
            quantity_change=quantity_change,
            previous_qty=previous_qty,
            new_qty=new_qty,
            reference_type=ref_type,
            reference_id=ref_id,
            reason=reason,
            notes=notes,
            transaction_date=date.today(),
            transaction_time=datetime.utcnow().time(),
            created_by=created_by,
        )
        db.session.add(txn)
        return txn

    # ─── stock_in ────────────────────────────────────────────────────────────

    @staticmethod
    def stock_in(
        product_id: int,
        quantity: int,
        notes: str = None,
        reference_type: str = "manual",
        reference_id: int = None,
        created_by: int = None,
    ) -> dict:
        """
        Increase stock for one product.
        Returns {"product_id", "previous_qty", "new_qty", "transaction_id"}.
        """
        if quantity <= 0:
            raise ValueError("quantity must be a positive integer.")

        try:
            product = (
                Product.query.filter(
                    Product.id == product_id,
                    Product.deleted_at.is_(None),
                )
                .with_for_update()
                .first()
            )

            if not product:
                raise LookupError(f"Product {product_id} not found.")

            txn = StockService.create_transaction(
                product=product,
                txn_type="STOCK_IN",
                quantity_change=quantity,
                ref_type=reference_type,
                ref_id=reference_id,
                notes=notes,
                created_by=created_by,
            )
            db.session.commit()

        except (ValueError, LookupError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError(f"stock_in failed: {exc}") from exc

        return {
            "product_id": product_id,
            "previous_qty": txn.previous_qty,
            "new_qty": txn.new_qty,
            "quantity_change": quantity,
            "transaction_id": txn.id,
        }

    # ─── stock_in_batch ──────────────────────────────────────────────────────

    @staticmethod
    def stock_in_batch(
        items: list[dict],
        notes: str = None,
        created_by: int = None,
    ) -> list[dict]:
        """
        Increase stock for multiple products in a single DB transaction.
        items: [{"product_id": int, "quantity": int}, ...]
        All succeed or all fail.
        Returns list of per-product result dicts.
        """
        if not items:
            raise ValueError("items list must not be empty.")

        results = []
        try:
            for item in items:
                pid = item.get("product_id")
                qty = item.get("quantity")

                if not pid:
                    raise ValueError("Each item must have a product_id.")
                if not qty or int(qty) <= 0:
                    raise ValueError(
                        f"quantity for product_id {pid} must be a positive integer."
                    )

                product = (
                    Product.query.filter(
                        Product.id == pid,
                        Product.deleted_at.is_(None),
                    )
                    .with_for_update()
                    .first()
                )

                if not product:
                    raise LookupError(f"Product {pid} not found.")

                txn = StockService.create_transaction(
                    product=product,
                    txn_type="STOCK_IN",
                    quantity_change=int(qty),
                    ref_type="manual",
                    notes=notes,
                    created_by=created_by,
                )
                results.append(
                    {
                        "product_id": pid,
                        "previous_qty": txn.previous_qty,
                        "new_qty": txn.new_qty,
                        "quantity_change": int(qty),
                        "transaction_id": None,  # filled after flush
                    }
                )

            db.session.flush()  # get txn IDs before commit
            # Update transaction IDs now that flush has assigned them
            txns = (
                StockTransaction.query.filter(
                    StockTransaction.product_id.in_([i["product_id"] for i in results]),
                    StockTransaction.transaction_type == "STOCK_IN",
                )
                .order_by(StockTransaction.id.desc())
                .limit(len(results))
                .all()
            )
            # Build a map: product_id → latest txn id
            txn_map = {t.product_id: t.id for t in txns}
            for r in results:
                r["transaction_id"] = txn_map.get(r["product_id"])

            db.session.commit()

        except (ValueError, LookupError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError(f"stock_in_batch failed: {exc}") from exc

        return results

    # ─── stock_out ───────────────────────────────────────────────────────────

    @staticmethod
    def stock_out(
        product_id: int,
        quantity: int,
        notes: str = None,
        reference_type: str = "manual",
        reference_id: int = None,
        created_by: int = None,
    ) -> dict:
        """
        Decrease stock for one product.
        Raises ValueError if resulting stock would go negative.
        """
        if quantity <= 0:
            raise ValueError("quantity must be a positive integer.")

        try:
            product = (
                Product.query.filter(
                    Product.id == product_id,
                    Product.deleted_at.is_(None),
                )
                .with_for_update()
                .first()
            )

            if not product:
                raise LookupError(f"Product {product_id} not found.")

            if product.current_stock < quantity:
                raise ValueError(
                    f"Insufficient stock. Available: {product.current_stock}, Requested: {quantity}."
                )

            txn = StockService.create_transaction(
                product=product,
                txn_type="STOCK_OUT",
                quantity_change=-quantity,
                ref_type=reference_type,
                ref_id=reference_id,
                notes=notes,
                created_by=created_by,
            )
            db.session.commit()

        except (ValueError, LookupError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError(f"stock_out failed: {exc}") from exc

        return {
            "product_id": product_id,
            "previous_qty": txn.previous_qty,
            "new_qty": txn.new_qty,
            "quantity_change": -quantity,
            "transaction_id": txn.id,
        }

    # ─── adjust_stock ────────────────────────────────────────────────────────

    @staticmethod
    def adjust_stock(
        product_id: int,
        actual_stock: int,
        reason: str = None,
        notes: str = None,
        created_by: int = None,
    ) -> dict:
        """
        Set stock to an absolute value.
        Calculates the signed difference and records an ADJUSTMENT transaction.
        actual_stock must be >= 0.
        """
        if actual_stock < 0:
            raise ValueError("actual_stock must be >= 0.")

        try:
            product = (
                Product.query.filter(
                    Product.id == product_id,
                    Product.deleted_at.is_(None),
                )
                .with_for_update()
                .first()
            )

            if not product:
                raise LookupError(f"Product {product_id} not found.")

            difference = actual_stock - product.current_stock

            if difference == 0:
                # No change — return current state without writing anything
                db.session.rollback()
                return {
                    "product_id": product_id,
                    "previous_qty": product.current_stock,
                    "new_qty": product.current_stock,
                    "quantity_change": 0,
                    "transaction_id": None,
                }

            txn = StockService.create_transaction(
                product=product,
                txn_type="ADJUSTMENT",
                quantity_change=difference,
                ref_type="adjustment",
                reason=reason,
                notes=notes,
                created_by=created_by,
            )
            db.session.commit()

        except (ValueError, LookupError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError(f"adjust_stock failed: {exc}") from exc

        return {
            "product_id": product_id,
            "previous_qty": txn.previous_qty,
            "new_qty": txn.new_qty,
            "quantity_change": difference,
            "transaction_id": txn.id,
        }
