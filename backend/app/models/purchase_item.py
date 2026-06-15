from app import db


class PurchaseItem(db.Model):
    __tablename__ = "purchase_items"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    purchase_id = db.Column(
        db.BigInteger,
        db.ForeignKey("purchases.id", ondelete="CASCADE"),
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
    purchase = db.relationship("Purchase", back_populates="items")
    product = db.relationship("Product", back_populates="purchase_items")

    __table_args__ = (
        db.Index("ix_purchase_items_purchase_id", "purchase_id"),
        db.Index("ix_purchase_items_product_id", "product_id"),
        db.UniqueConstraint("purchase_id", "product_id", name="uq_purchase_product"),
    )

    def __repr__(self):
        return f"<PurchaseItem purchase={self.purchase_id} product={self.product_id}>"
