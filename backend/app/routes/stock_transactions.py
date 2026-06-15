from datetime import date

from flask import Blueprint, request
from marshmallow import ValidationError

from app.services.stock_service import StockService
from app.services.stock_transaction_service import StockTransactionService
from app.utils.response import success, created, error
from app.utils.pagination import get_pagination_params

bp = Blueprint("stock_transactions", __name__, url_prefix="/api/v1/stock-transactions")


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _parse_date(raw: str, param_name: str):
    """Parse an ISO date string (YYYY-MM-DD). Returns None if raw is None/empty."""
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValueError(f"{param_name} must be a valid date in YYYY-MM-DD format.")


# ─── GET /api/v1/stock-transactions ───────────────────────────────────────────


@bp.route("", methods=["GET"])
def list_transactions():
    page, per_page = get_pagination_params()

    product_id_raw = request.args.get("product_id")
    product_id = (
        int(product_id_raw) if product_id_raw and product_id_raw.isdigit() else None
    )

    transaction_type = request.args.get("transaction_type", "").strip() or None

    try:
        from_date = _parse_date(request.args.get("from_date"), "from_date")
        to_date = _parse_date(request.args.get("to_date"), "to_date")
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)

    try:
        items, meta = StockTransactionService.get_all(
            product_id=product_id,
            transaction_type=transaction_type,
            from_date=from_date,
            to_date=to_date,
            page=page,
            per_page=per_page,
        )
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)

    return success(items, meta=meta)


# ─── POST /api/v1/stock-transactions/stock-in ─────────────────────────────────


@bp.route("/stock-in", methods=["POST"])
def stock_in():
    from app.schemas.stock_transaction_schema import stock_in_schema

    try:
        data = stock_in_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        result = StockService.stock_in(
            product_id=data["product_id"],
            quantity=data["quantity"],
            notes=data.get("notes"),
        )
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)
    except RuntimeError as exc:
        return error("INTERNAL_ERROR", str(exc), 500)

    return created(result)


# ─── POST /api/v1/stock-transactions/stock-in/batch ───────────────────────────


@bp.route("/stock-in/batch", methods=["POST"])
def stock_in_batch():
    from app.schemas.stock_transaction_schema import stock_in_batch_schema

    try:
        data = stock_in_batch_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        results = StockService.stock_in_batch(
            items=data["items"],
            notes=data.get("notes"),
        )
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)
    except RuntimeError as exc:
        return error("INTERNAL_ERROR", str(exc), 500)

    return created(
        {
            "results": results,
            "total_items": len(results),
        }
    )


# ─── POST /api/v1/stock-transactions/adjustment ───────────────────────────────


@bp.route("/adjustment", methods=["POST"])
def adjustment():
    from app.schemas.stock_transaction_schema import stock_adjustment_schema

    try:
        data = stock_adjustment_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        result = StockService.adjust_stock(
            product_id=data["product_id"],
            actual_stock=data["actual_stock"],
            reason=data.get("reason"),
            notes=data.get("notes"),
        )
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc), 400)
    except RuntimeError as exc:
        return error("INTERNAL_ERROR", str(exc), 500)

    return success(result)
