from datetime import date

from flask import Blueprint, request
from marshmallow import ValidationError

from app.services.purchase_service import PurchaseService
from app.utils.response import success, created, error
from app.utils.pagination import get_pagination_params
from app.models.supplier import Supplier
from app.models.product import Product

bp = Blueprint("purchases", __name__, url_prefix="/api/v1/purchases")


# ─── Helper ───────────────────────────────────────────────────────────────────


def _parse_date(raw: str, param_name: str):
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValueError(f"{param_name} must be a valid date in YYYY-MM-DD format.")


# ─── GET /api/v1/purchases/next-number ────────────────────────────────────────
# MUST be defined BEFORE /<int:id> to avoid routing conflict.


@bp.route("/next-number", methods=["GET"])
def next_number():
    purchase_no = PurchaseService.next_number()
    return success({"purchase_no": purchase_no})


# ─── GET /api/v1/purchases ────────────────────────────────────────────────────


@bp.route("", methods=["GET"])
def list_purchases():
    page, per_page = get_pagination_params()

    supplier_id_raw = request.args.get("supplier_id")
    supplier_id = (
        int(supplier_id_raw) if supplier_id_raw and supplier_id_raw.isdigit() else None
    )

    search = request.args.get("search", "").strip() or None

    try:
        from_date = _parse_date(request.args.get("from_date"), "from_date")
        to_date = _parse_date(request.args.get("to_date"), "to_date")
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)

    items, meta = PurchaseService.get_all(
        supplier_id=supplier_id,
        from_date=from_date,
        to_date=to_date,
        search=search,
        page=page,
        per_page=per_page,
    )
    return success(items, meta=meta)


# ─── POST /api/v1/purchases ───────────────────────────────────────────────────


@bp.route("", methods=["POST"])
def create_purchase():
    from app.schemas.purchase_schema import purchase_create_schema

    try:
        data = purchase_create_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        new_purchase = PurchaseService.create(data)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)
    except RuntimeError as exc:
        return error("INTERNAL_ERROR", str(exc), 500)

    return created(new_purchase)


# ─── GET /api/v1/purchases/<id> ───────────────────────────────────────────────


@bp.route("/<int:purchase_id>", methods=["GET"])
def get_purchase(purchase_id: int):
    try:
        purchase = PurchaseService.get_by_id(purchase_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)

    return success(purchase)


# ─── POST /api/v1/purchases/bulk-import ──────────────────────────────────────


@bp.route("/bulk-import", methods=["POST"])
def bulk_import_purchases():
    """
    Bulk create purchases from Excel rows.
    Each row represents one purchase with one line item.
    Rows with the same invoice_no on the same date are merged into one purchase.

    Body: { "rows": [{ supplier, product, quantity, purchase_price,
                        invoice_no, purchase_date, notes }] }
    Returns: { total, saved, failed, errors: [{row, field, message}] }
    """
    data = request.get_json(silent=True) or {}
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        return error("VALIDATION_ERROR", "rows must be a non-empty list.", 400)

    # Build lookup maps (name → id) once.
    suppliers_by_name = {
        s.name.strip().lower(): s.id
        for s in Supplier.query.filter(Supplier.deleted_at.is_(None)).all()
    }
    products_by_name = {
        f"{p.brand.strip().lower()} {p.item.strip().lower()} {p.pack_size.strip().lower()}": p.id
        for p in Product.query.filter(Product.deleted_at.is_(None)).all()
    }
    # Also index by "brand item" without pack_size for flexible matching.
    products_by_short = {
        f"{p.brand.strip().lower()} {p.item.strip().lower()}": p.id
        for p in Product.query.filter(Product.deleted_at.is_(None)).all()
    }

    def resolve_product(name: str):
        n = name.strip().lower()
        return products_by_name.get(n) or products_by_short.get(n)

    saved = 0
    failed = 0
    errors = []

    # Group rows by (supplier, invoice_no, purchase_date) so multiple product
    # rows for the same invoice become one purchase with multiple items.
    from collections import defaultdict
    groups = defaultdict(list)
    row_map = {}  # group_key → first excel row index (for error reporting)
    row_errors = {}  # excel_row_idx → list of error strings

    for i, row in enumerate(rows):
        excel_row = i + 2
        sup_name = str(row.get("supplier") or "").strip()
        invoice_no = str(row.get("invoice_no") or "").strip() or None
        purchase_date = str(row.get("purchase_date") or "").strip() or None
        product_name = str(row.get("product") or "").strip()
        notes = str(row.get("notes") or "").strip() or None

        row_errs = []

        if not sup_name:
            row_errs.append("supplier is required")
        if not product_name:
            row_errs.append("product is required")

        try:
            qty = int(float(row.get("quantity") or 0))
            if qty <= 0:
                row_errs.append("quantity must be > 0")
        except (ValueError, TypeError):
            row_errs.append("quantity must be a number")
            qty = 0

        try:
            rate = float(row.get("purchase_price") or 0)
            if rate <= 0:
                row_errs.append("purchase_price must be > 0")
        except (ValueError, TypeError):
            row_errs.append("purchase_price must be a number")
            rate = 0

        supplier_id = suppliers_by_name.get(sup_name.lower())
        if sup_name and not supplier_id:
            row_errs.append(f'supplier "{sup_name}" not found')

        product_id = resolve_product(product_name) if product_name else None
        if product_name and not product_id:
            row_errs.append(f'product "{product_name}" not found')

        if row_errs:
            failed += 1
            errors.append({"row": excel_row, "field": "general", "message": "; ".join(row_errs)})
            continue

        # Validate date format
        parsed_date = None
        if purchase_date:
            try:
                parsed_date = date.fromisoformat(purchase_date)
            except ValueError:
                failed += 1
                errors.append({"row": excel_row, "field": "purchase_date", "message": "must be YYYY-MM-DD"})
                continue

        group_key = (supplier_id, invoice_no, purchase_date or "")
        groups[group_key].append({
            "product_id": product_id,
            "quantity": qty,
            "rate": rate,
        })
        if group_key not in row_map:
            row_map[group_key] = excel_row

    # Now create one purchase per group.
    for group_key, items in groups.items():
        supplier_id, invoice_no, purchase_date_str = group_key
        excel_row = row_map[group_key]
        try:
            parsed_date = date.fromisoformat(purchase_date_str) if purchase_date_str else None
            PurchaseService.create({
                "supplier_id": supplier_id,
                "purchase_date": parsed_date,
                "invoice_number": invoice_no,
                "tax_amount": 0.0,
                "notes": None,
                "items": items,
            })
            saved += len(items)
        except (LookupError, ValueError, RuntimeError) as exc:
            failed += len(items)
            errors.append({"row": excel_row, "field": "general", "message": str(exc)})

    return success({"total": len(rows), "saved": saved, "failed": failed, "errors": errors})


# ─── PATCH /api/v1/purchases/<id>/cancel ──────────────────────────────────────


@bp.route("/<int:purchase_id>/cancel", methods=["PATCH"])
def cancel_purchase(purchase_id: int):
    try:
        purchase = PurchaseService.cancel(purchase_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)
    except RuntimeError as exc:
        return error("INTERNAL_ERROR", str(exc), 500)

    return success(purchase)
