from app import db


class Purchase(db.Model):
    __tablename__ = "purchases"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    purchase_no = db.Column(db.String(16), unique=True, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    supplier_id = db.Column(
        db.BigInteger,
        db.ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    invoice_number = db.Column(db.String(64), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    status = db.Column(
        db.Enum("draft", "confirmed", "cancelled", name="purchase_status"),
        nullable=False,
        default="confirmed",
    )
    created_by = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())

    # Relationships
    supplier = db.relationship("Supplier", back_populates="purchases")
    items = db.relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        db.Index("ix_purchases_purchase_date", "purchase_date"),
        db.Index("ix_purchases_supplier_id", "supplier_id"),
        db.Index("ix_purchases_status", "status"),
    )

    def __repr__(self):
        return f"<Purchase {self.purchase_no}>"
