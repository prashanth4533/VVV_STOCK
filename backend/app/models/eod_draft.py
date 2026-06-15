from app import db


class EODDraft(db.Model):
    __tablename__ = "eod_drafts"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, nullable=True)
    product_id = db.Column(
        db.BigInteger,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    physical_qty = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(
        db.DateTime, nullable=True, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    product = db.relationship("Product", back_populates="eod_drafts")

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_eod_draft_user_product"),
    )

    def __repr__(self):
        return f"<EODDraft user={self.user_id} product={self.product_id} qty={self.physical_qty}>"
