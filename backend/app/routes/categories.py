from flask import Blueprint, request
from marshmallow import ValidationError

from app.services.category_service import CategoryService
from app.utils.response import success, created, no_content, error

bp = Blueprint("categories", __name__, url_prefix="/api/v1/categories")


# ─── GET /api/v1/categories ────────────────────────────────────────────────────


@bp.route("", methods=["GET"])
def list_categories():
    include_stats = request.args.get("include_stats", "false").lower() == "true"
    items = CategoryService.get_all(include_stats=include_stats)
    return success(items, meta={"total": len(items)})


# ─── POST /api/v1/categories ──────────────────────────────────────────────────


@bp.route("", methods=["POST"])
def create_category():
    from app.schemas.category_schema import category_input_schema

    try:
        data = category_input_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        new_cat = CategoryService.create(data)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)

    return created(new_cat)


# ─── GET /api/v1/categories/<id> ──────────────────────────────────────────────


@bp.route("/<int:category_id>", methods=["GET"])
def get_category(category_id: int):
    try:
        cat = CategoryService.get_by_id(category_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)

    return success(cat)


# ─── PUT /api/v1/categories/<id> ──────────────────────────────────────────────


@bp.route("/<int:category_id>", methods=["PUT"])
def update_category(category_id: int):
    from app.schemas.category_schema import CategoryInputSchema

    try:
        # partial=True: allow omitting fields for PUT in this context
        data = CategoryInputSchema(partial=True).load(
            request.get_json(silent=True) or {}
        )
    except ValidationError as exc:
        return error("VALIDATION_ERROR", "Invalid input data.", 400, exc.messages)

    try:
        updated = CategoryService.update(category_id, data)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)

    return success(updated)


# ─── DELETE /api/v1/categories/<id> ───────────────────────────────────────────


@bp.route("/<int:category_id>", methods=["DELETE"])
def delete_category(category_id: int):
    try:
        CategoryService.delete(category_id)
    except LookupError as exc:
        return error("NOT_FOUND", str(exc), 404)
    except ValueError as exc:
        return error("CONFLICT", str(exc), 409)

    return no_content()
