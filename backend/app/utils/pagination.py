from flask import request


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 50
MAX_PER_PAGE = 200


def get_pagination_params():
    """Extract and sanitise page / per_page from the current request."""
    try:
        page = max(1, int(request.args.get("page", DEFAULT_PAGE)))
    except (ValueError, TypeError):
        page = DEFAULT_PAGE

    try:
        per_page = min(
            MAX_PER_PAGE,
            max(1, int(request.args.get("per_page", DEFAULT_PER_PAGE))),
        )
    except (ValueError, TypeError):
        per_page = DEFAULT_PER_PAGE

    return page, per_page


def build_meta(pagination):
    """Build the standard pagination meta block from a SQLAlchemy Pagination object."""
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }
