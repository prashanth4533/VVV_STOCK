from flask import jsonify


def success(data, status_code=200, meta=None):
    """Return a successful JSON response."""
    body = {"data": data}
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status_code


def created(data):
    """Return 201 Created with the new resource."""
    return success(data, 201)


def no_content():
    """Return 204 No Content (e.g. after DELETE)."""
    return "", 204


def error(code, message, status_code=400, details=None):
    """Return a structured error response."""
    body = {"error": code, "message": message}
    if details is not None:
        body["details"] = details
    return jsonify(body), status_code
