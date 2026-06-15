from app import db


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sale_no = db.Column(db.String(16), unique=True, nullable=False)
    sale_date = db.Column(db.Date, nullable=False)
    customer_name = db.Column(db.String(128), nullable=False)
    customer_mobile = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    status = db.Column(
        db.Enum("draft", "confirmed", "cancelled", name="sale_status"),
        nullable=False,
        default="confirmed",
    )
    created_by = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())

    # Relationships
    items = db.relationship(
        "SaleItem", back_populates="sale", cascade="all, delete-orphan", lazy="joined"
    )

    __table_args__ = (
        db.Index("ix_sales_sale_date", "sale_date"),
        db.Index("ix_sales_customer_name", "customer_name"),
        db.Index("ix_sales_status", "status"),
    )

    def __repr__(self):
        return f"<Sale {self.sale_no}>"
