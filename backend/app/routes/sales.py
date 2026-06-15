from datetime import date

from flask import Blueprint, request
from marshmallow import ValidationError

from app.services.sale_service import SaleService
from app.utils.response import success, created, error
from app.utils.pagination import get_pagination_params

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


# ─── GET /api/v1/sales/<id> ───────────────────────────────────────────────────


@bp.route("/<int:sale_id>", methods=["GET"])
def get_sale(sale_id: int):
    try:
        sale = SaleService.get_by_id(sale_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)

    return success(sale)
