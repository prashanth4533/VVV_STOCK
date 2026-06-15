from app import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sku = db.Column(db.String(20), unique=True, nullable=False)
    brand = db.Column(db.String(64), nullable=False)
    item = db.Column(db.String(128), nullable=False)
    pack_size = db.Column(db.String(16), nullable=False)
    category_id = db.Column(
        db.SmallInteger,
        db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_id = db.Column(
        db.BigInteger,
        db.ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=5)
    purchase_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    category = db.relationship("Category", back_populates="products")
    supplier = db.relationship("Supplier", back_populates="products")
    purchase_items = db.relationship(
        "PurchaseItem", back_populates="product", lazy="dynamic"
    )
    sale_items = db.relationship("SaleItem", back_populates="product", lazy="dynamic")
    stock_transactions = db.relationship(
        "StockTransaction", back_populates="product", lazy="dynamic"
    )
    eod_histories = db.relationship(
        "EODHistory", back_populates="product", lazy="dynamic"
    )
    eod_drafts = db.relationship("EODDraft", back_populates="product", lazy="dynamic")

    __table_args__ = (
        db.Index("ix_products_category_id", "category_id"),
        db.Index("ix_products_supplier_id", "supplier_id"),
        db.Index("ix_products_brand_item", "brand", "item"),
        db.Index("ix_products_current_stock", "current_stock"),
        db.Index("ix_products_deleted_at", "deleted_at"),
    )

    @property
    def status(self):
        if self.current_stock == 0:
            return "OUT"
        elif self.current_stock <= self.reorder_level:
            return "LOW"
        return "OK"

    def __repr__(self):
        return f"<Product {self.sku} {self.brand} {self.item}>"
