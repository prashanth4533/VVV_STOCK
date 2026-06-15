from app import db


class EODHistory(db.Model):
    __tablename__ = "eod_history"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(36), nullable=False)
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    count_date = db.Column(db.Date, nullable=False)
    system_qty = db.Column(db.Integer, nullable=False)
    physical_qty = db.Column(db.Integer, nullable=False)
    difference = db.Column(db.Integer, nullable=False)
    stock_transaction_id = db.Column(
        db.BigInteger,
        db.ForeignKey("stock_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Relationships
    product = db.relationship("Product", back_populates="eod_histories")
    stock_transaction = db.relationship("StockTransaction", lazy="joined")

    __table_args__ = (
        db.Index("ix_eod_history_session_id", "session_id"),
        db.Index("ix_eod_history_count_date", "count_date"),
        db.Index("ix_eod_history_product_date", "product_id", "count_date"),
    )

    def __repr__(self):
        return f"<EODHistory {self.count_date} product={self.product_id} diff={self.difference:+d}>"
