"""
ProductImportService
====================
Handles bulk import of products from Excel rows (parsed on the frontend).

Each row must contain:
  brand, item, pack_size, category (name), supplier (name, optional),
  opening_stock, reorder_level, purchase_price, selling_price

The service:
  1. Validates each row
  2. Resolves category / supplier names to IDs
  3. Creates products via ProductService (skips duplicates with an error note)
  4. Returns { saved, errors: [{row, field, message}] }

No existing business logic is modified.
"""

from app.models.category import Category
from app.models.supplier import Supplier
from app.services.product_service import ProductService


class ProductImportService:
    REQUIRED_FIELDS = [
        "brand",
        "item",
        "pack_size",
        "category",
    ]

    @staticmethod
    def bulk_import(rows: list[dict]) -> dict:
        """
        Process a list of product row dicts and persist valid ones.

        Returns:
            {
              "total": int,
              "saved": int,
              "failed": int,
              "errors": [ {"row": int, "field": str, "message": str} ]
            }
        """
        # Pre-load lookup maps once (case-insensitive)
        cat_map = {
            c.name.strip().lower(): c.id
            for c in Category.query.all()
        }
        sup_map = {
            s.name.strip().lower(): s.id
            for s in Supplier.query.filter(Supplier.deleted_at.is_(None)).all()
        }

        saved = 0
        errors = []

        for idx, raw in enumerate(rows):
            row_num = idx + 2  # Excel row numbers start at 2 (row 1 = header)
            row = {k: (str(v).strip() if v is not None else "") for k, v in raw.items()}

            # ── Validate required fields ──────────────────────────────────────
            row_errors = []
            for field in ProductImportService.REQUIRED_FIELDS:
                if not row.get(field):
                    row_errors.append({
                        "row": row_num,
                        "field": field,
                        "message": f"'{field}' is required.",
                    })

            if row_errors:
                errors.extend(row_errors)
                continue

            # ── Resolve category ──────────────────────────────────────────────
            cat_name = row["category"].strip().lower()
            category_id = cat_map.get(cat_name)
            if category_id is None:
                errors.append({
                    "row": row_num,
                    "field": "category",
                    "message": f"Category '{row['category']}' not found. Create it first.",
                })
                continue

            # ── Resolve supplier (optional) ───────────────────────────────────
            supplier_id = None
            if row.get("supplier"):
                sup_name = row["supplier"].strip().lower()
                supplier_id = sup_map.get(sup_name)
                if supplier_id is None:
                    errors.append({
                        "row": row_num,
                        "field": "supplier",
                        "message": f"Supplier '{row['supplier']}' not found. Create it first.",
                    })
                    continue

            # ── Numeric coercion ──────────────────────────────────────────────
            def to_int(val, default=0):
                try:
                    return max(0, int(float(val))) if val else default
                except (ValueError, TypeError):
                    return default

            def to_float(val, default=0.0):
                try:
                    return max(0.0, float(val)) if val else default
                except (ValueError, TypeError):
                    return default

            data = {
                "brand": row["brand"],
                "item": row["item"],
                "pack_size": row["pack_size"],
                "category_id": category_id,
                "supplier_id": supplier_id,
                "opening_stock": to_int(row.get("opening_stock"), 0),
                "reorder_level": to_int(row.get("reorder_level"), 5),
                "purchase_price": to_float(row.get("purchase_price"), 0.0),
                "selling_price": to_float(row.get("selling_price"), 0.0),
                "notes": row.get("notes") or None,
            }

            # ── Create via existing ProductService ────────────────────────────
            try:
                ProductService.create(data)
                saved += 1
            except LookupError as exc:
                errors.append({
                    "row": row_num,
                    "field": "general",
                    "message": str(exc),
                })
            except ValueError as exc:
                errors.append({
                    "row": row_num,
                    "field": "brand/item",
                    "message": str(exc),
                })
            except Exception as exc:  # noqa: BLE001
                errors.append({
                    "row": row_num,
                    "field": "general",
                    "message": f"Unexpected error: {exc}",
                })

        return {
            "total": len(rows),
            "saved": saved,
            "failed": len(rows) - saved,
            "errors": errors,
        }
