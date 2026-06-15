from app import db


class StockTransaction(db.Model):
    __tablename__ = "stock_transactions"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    transaction_type = db.Column(
        db.Enum(
            "STOCK_IN",
            "STOCK_OUT",
            "ADJUSTMENT",
            "EOD_COUNT",
            "NEW_PRODUCT",
            name="transaction_type_enum",
        ),
        nullable=False,
    )
    quantity_change = db.Column(db.Integer, nullable=False)
    previous_qty = db.Column(db.Integer, nullable=False)
    new_qty = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(
        db.Enum(
            "purchase",
            "sale",
            "adjustment",
            "eod",
            "manual",
            "new_product",
            name="reference_type_enum",
        ),
        nullable=False,
    )
    reference_id = db.Column(db.BigInteger, nullable=True)
    reason = db.Column(db.String(64), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    transaction_date = db.Column(db.Date, nullable=False)
    transaction_time = db.Column(db.Time, nullable=False)
    created_by = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Relationships
    product = db.relationship("Product", back_populates="stock_transactions")

    __table_args__ = (
        db.Index("ix_stock_txn_product_created", "product_id", "created_at"),
        db.Index("ix_stock_txn_type", "transaction_type"),
        db.Index("ix_stock_txn_date", "transaction_date"),
        db.Index("ix_stock_txn_reference", "reference_type", "reference_id"),
    )

    def __repr__(self):
        return f"<StockTransaction {self.id} {self.transaction_type} {self.quantity_change:+d}>"
