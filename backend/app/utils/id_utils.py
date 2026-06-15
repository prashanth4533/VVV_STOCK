from app import db


def next_id(model) -> int:
    """Return the next integer primary key for a SQLAlchemy model."""
    current_max = db.session.query(db.func.max(model.id)).scalar()
    return int(current_max or 0) + 1
