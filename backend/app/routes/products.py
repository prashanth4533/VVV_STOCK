from flask import Blueprint, request
from marshmallow import ValidationError

from app.services.product_service import ProductService
from app.utils.response import success, created, no_content, error
from app.utils.pagination import get_pagination_params

bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


# ─── GET /api/v1/products/reorder-required ────────────────────────────────────
# MUST be defined BEFORE /<int:id> to avoid routing conflict.


@bp.route("/reorder-required", methods=["GET"])
def reorder_required():
    items = ProductService.get_reorder_required()
    return success(items, meta={"total": len(items)})


# ─── GET /api/v1/products ─────────────────────────────────────────────────────


@bp.route("", methods=["GET"])
def list_products():
    page, per_page = get_pagination_params()

    search = request.args.get("search", "").strip() or None

    category_id_raw = request.args.get("category_id")
    category_id = (
        int(category_id_raw) if category_id_raw and category_id_raw.isdigit() else None
    )

    supplier_id_raw = request.args.get("supplier_id")
    supplier_id = (
        int(supplier_id_raw) if supplier_id_raw and supplier_id_raw.isdigit() else None
    )

    status = request.args.get("status", "").upper() or None
    if status not in (None, "OK", "LOW", "OUT"):
        return error("VALIDATION_ERROR", "status must be one of: OK, LOW, OUT", 400)

    show_zero = request.args.get("show_zero", "true").lower() not in (
        "false",
        "0",
        "no",
    )

    items, meta = ProductService.get_all(
        search=search,
        category_id=category_id,
        supplier_id=supplier_id,
        status=status,
        show_zero=show_zero,
        page=page,
        per_page=per_page,
    )
    return success(items, meta=meta)


# ─── POST /api/v1/products ────────────────────────────────────────────────────


@bp.route("", methods=["POST"])
def create_product():
    from app.schemas.product_schema import product_input_schema

    try:
        data = product_input_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        new_product = ProductService.create(data)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)

    return created(new_product)


# ─── GET /api/v1/products/<id> ────────────────────────────────────────────────


@bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    try:
        product = ProductService.get_by_id(product_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)

    return success(product)


# ─── PUT /api/v1/products/<id> ────────────────────────────────────────────────


@bp.route("/<int:product_id>", methods=["PUT"])
def update_product(product_id: int):
    from app.schemas.product_schema import product_update_schema

    try:
        data = product_update_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    if not data:
        return error(
            "VALIDATION_ERROR", "Request body must contain at least one field.", 400
        )

    try:
        updated = ProductService.update(product_id, data)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)

    return success(updated)


# ─── DELETE /api/v1/products/<id> ─────────────────────────────────────────────


@bp.route("/<int:product_id>", methods=["DELETE"])
def delete_product(product_id: int):
    try:
        ProductService.delete(product_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)

    return no_content()
