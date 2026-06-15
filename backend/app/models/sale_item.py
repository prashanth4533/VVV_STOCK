from app import db


class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sale_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Numeric(12, 2), nullable=False)
    line_total = db.Column(db.Numeric(14, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Relationships
    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product", back_populates="sale_items")

    __table_args__ = (
        db.Index("ix_sale_items_sale_id", "sale_id"),
        db.Index("ix_sale_items_product_id", "product_id"),
        db.UniqueConstraint("sale_id", "product_id", name="uq_sale_product"),
    )

    def __repr__(self):
        return f"<SaleItem sale={self.sale_id} product={self.product_id}>"
