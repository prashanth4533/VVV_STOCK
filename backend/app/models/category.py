from app import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    sku_prefix = db.Column(db.String(8), nullable=False)
    display_color = db.Column(db.String(7), nullable=True)
    display_bg = db.Column(db.String(7), nullable=True)
    sort_order = db.Column(db.SmallInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())

    # Relationships
    products = db.relationship("Product", back_populates="category", lazy="dynamic")

    __table_args__ = (db.Index("ix_categories_sort_order", "sort_order"),)

    def __repr__(self):
        return f"<Category {self.name}>"
