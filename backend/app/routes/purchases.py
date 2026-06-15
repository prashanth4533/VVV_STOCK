from datetime import date

from flask import Blueprint, request
from marshmallow import ValidationError

from app.services.purchase_service import PurchaseService
from app.utils.response import success, created, error
from app.utils.pagination import get_pagination_params

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
