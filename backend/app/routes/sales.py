from datetime import date
from collections import defaultdict

from flask import Blueprint, request
from marshmallow import ValidationError

from app.services.sale_service import SaleService
from app.utils.response import success, created, error
from app.utils.pagination import get_pagination_params
from app.models.product import Product

bp = Blueprint("sales", __name__, url_prefix="/api/v1/sales")


# ─── Helper ──────────────────────────────────────────────────────────────────

def _parse_date(raw: str, param_name: str):
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValueError(f"{param_name} must be a valid date in YYYY-MM-DD format.")


# ─── GET /api/v1/sales/next-number ───────────────────────────────────────────
# MUST be before /<int:id> to avoid routing conflict.


@bp.route("/next-number", methods=["GET"])
def next_number():
    sale_no = SaleService.next_number()
    return success({"sale_no": sale_no})


# ─── GET /api/v1/sales ───────────────────────────────────────────────────────


@bp.route("", methods=["GET"])
def list_sales():
    page, per_page = get_pagination_params()
    try:
        from_date = _parse_date(request.args.get("from_date"), "from_date")
        to_date = _parse_date(request.args.get("to_date"), "to_date")
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)

    search = request.args.get("search", "").strip() or None
    try:
        items, meta = SaleService.get_all(
            from_date=from_date,
            to_date=to_date,
            search=search,
            page=page,
            per_page=per_page,
        )
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)

    return success(items, meta=meta)


# ─── POST /api/v1/sales ───────────────────────────────────────────────────────


@bp.route("", methods=["POST"])
def create_sale():
    from app.schemas.sale_schema import sale_create_schema

    try:
        data = sale_create_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        new_sale = SaleService.create(data)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)
    except RuntimeError as exc:
        return error("INTERNAL_ERROR", str(exc), 500)

    return created(new_sale)


# ─── POST /api/v1/sales/bulk-import ──────────────────────────────────────────


@bp.route("/bulk-import", methods=["POST"])
def bulk_import_sales():
    """
    Bulk create sales from Excel rows.
    Rows with the same invoice_no and customer_name on the same date are merged.

    Body: { "rows": [{ invoice_no, sale_date, customer_name, product,
                        quantity, selling_price, notes }] }
    Returns: { total, saved, failed, errors: [{row, field, message}] }
    """
    data = request.get_json(silent=True) or {}
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        return error("VALIDATION_ERROR", "rows must be a non-empty list.", 400)

    products_by_name = {
        f"{p.brand.strip().lower()} {p.item.strip().lower()} {p.pack_size.strip().lower()}": p.id
        for p in Product.query.filter(Product.deleted_at.is_(None)).all()
    }
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
    groups = defaultdict(list)
    row_map = {}

    for i, row in enumerate(rows):
        excel_row = i + 2
        customer_name = str(row.get("customer_name") or "").strip()
        invoice_no = str(row.get("invoice_no") or "").strip() or None
        sale_date = str(row.get("sale_date") or "").strip() or None
        product_name = str(row.get("product") or "").strip()
        notes = str(row.get("notes") or "").strip() or None

        row_errs = []

        if not customer_name:
            row_errs.append("customer_name is required")
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
            rate = float(row.get("selling_price") or 0)
            if rate <= 0:
                row_errs.append("selling_price must be > 0")
        except (ValueError, TypeError):
            row_errs.append("selling_price must be a number")
            rate = 0

        product_id = resolve_product(product_name) if product_name else None
        if product_name and not product_id:
            row_errs.append(f'product "{product_name}" not found')

        if row_errs:
            failed += 1
            errors.append({"row": excel_row, "field": "general", "message": "; ".join(row_errs)})
            continue

        if sale_date:
            try:
                date.fromisoformat(sale_date)
            except ValueError:
                failed += 1
                errors.append({"row": excel_row, "field": "sale_date", "message": "must be YYYY-MM-DD"})
                continue

        group_key = (customer_name, invoice_no or "", sale_date or "")
        groups[group_key].append({
            "product_id": product_id,
            "quantity": qty,
            "rate": rate,
        })
        if group_key not in row_map:
            row_map[group_key] = excel_row

    for group_key, items in groups.items():
        customer_name, invoice_no, sale_date_str = group_key
        excel_row = row_map[group_key]
        try:
            parsed_date = date.fromisoformat(sale_date_str) if sale_date_str else None
            SaleService.create({
                "customer_name": customer_name,
                "customer_mobile": None,
                "sale_date": parsed_date,
                "discount_amount": 0.0,
                "notes": None,
                "items": items,
            })
            saved += len(items)
        except (LookupError, ValueError, RuntimeError) as exc:
            failed += len(items)
            errors.append({"row": excel_row, "field": "general", "message": str(exc)})

    return success({"total": len(rows), "saved": saved, "failed": failed, "errors": errors})


# ─── GET /api/v1/sales/<id> ───────────────────────────────────────────────────


@bp.route("/<int:sale_id>", methods=["GET"])
def get_sale(sale_id: int):
    try:
        sale = SaleService.get_by_id(sale_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)

    return success(sale)
