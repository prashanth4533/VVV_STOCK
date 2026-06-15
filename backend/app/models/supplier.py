from app import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    contact_person = db.Column(db.String(64), nullable=True)
    mobile = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    gst = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    products = db.relationship("Product", back_populates="supplier", lazy="dynamic")
    purchases = db.relationship("Purchase", back_populates="supplier", lazy="dynamic")

    __table_args__ = (
        db.Index("ix_suppliers_name", "name"),
        db.Index("ix_suppliers_mobile", "mobile"),
        db.Index("ix_suppliers_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return f"<Supplier {self.name}>"
