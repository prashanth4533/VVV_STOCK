from flask import Blueprint, request
from marshmallow import ValidationError

from app.services.supplier_service import SupplierService
from app.utils.response import success, created, no_content, error
from app.utils.pagination import get_pagination_params

bp = Blueprint("suppliers", __name__, url_prefix="/api/v1/suppliers")


# ─── GET /api/v1/suppliers ────────────────────────────────────────────────────


@bp.route("", methods=["GET"])
def list_suppliers():
    page, per_page = get_pagination_params()

    # Optional filters
    search = request.args.get("search", "").strip() or None

    is_active_raw = request.args.get("is_active")
    if is_active_raw is None:
        is_active = None
    else:
        is_active = is_active_raw.lower() not in ("false", "0", "no")

    items, meta = SupplierService.get_all(
        search=search,
        is_active=is_active,
        page=page,
        per_page=per_page,
    )
    return success(items, meta=meta)


# ─── POST /api/v1/suppliers ───────────────────────────────────────────────────


@bp.route("", methods=["POST"])
def create_supplier():
    from app.schemas.supplier_schema import supplier_input_schema

    try:
        data = supplier_input_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        new_sup = SupplierService.create(data)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)

    return created(new_sup)


# ─── GET /api/v1/suppliers/<id> ───────────────────────────────────────────────


@bp.route("/<int:supplier_id>", methods=["GET"])
def get_supplier(supplier_id: int):
    try:
        sup = SupplierService.get_by_id(supplier_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)

    return success(sup)


# ─── PUT /api/v1/suppliers/<id> ───────────────────────────────────────────────


@bp.route("/<int:supplier_id>", methods=["PUT"])
def update_supplier(supplier_id: int):
    from app.schemas.supplier_schema import SupplierInputSchema

    try:
        data = SupplierInputSchema(partial=True).load(
            request.get_json(silent=True) or {}
        )
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        updated = SupplierService.update(supplier_id, data)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)

    return success(updated)


# ─── DELETE /api/v1/suppliers/<id> ────────────────────────────────────────────


@bp.route("/<int:supplier_id>", methods=["DELETE"])
def delete_supplier(supplier_id: int):
    try:
        SupplierService.delete(supplier_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)

    return no_content()


# ─── POST /api/v1/suppliers/import-products ───────────────────────────────────


@bp.route("/import-products", methods=["POST"])
def import_products():
    """Bulk-import products from parsed Excel rows.

    Expects JSON body: { "rows": [ { brand, item, pack_size, category, supplier,
    opening_stock, reorder_level, purchase_price, selling_price }, ... ] }

    Returns: { saved: int, errors: [ {row, message} ] }
    """
    from app.services.product_import_service import ProductImportService

    body = request.get_json(silent=True) or {}
    rows = body.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return error("VALIDATION_ERROR", "rows must be a non-empty list.", 400)

    result = ProductImportService.bulk_import(rows)
    return success(result)
