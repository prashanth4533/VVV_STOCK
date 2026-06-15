from datetime import date, datetime

from sqlalchemy import or_

from app import db
from app.models.product import Product
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.stock_transaction import StockTransaction
from app.utils.id_utils import next_id


class ProductService:
    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _assert_category(category_id: int) -> Category:
        cat = Category.query.get(category_id)
        if not cat:
            raise LookupError(f"Category {category_id} not found.")
        return cat

    @staticmethod
    def _assert_supplier(supplier_id: int) -> Supplier:
        sup = Supplier.query.filter(
            Supplier.id == supplier_id,
            Supplier.deleted_at.is_(None),
        ).first()
        if not sup:
            raise LookupError(f"Supplier {supplier_id} not found.")
        return sup

    @staticmethod
    def _serialise(product: Product) -> dict:
        from app.schemas.product_schema import product_schema

        return product_schema.dump(product)

    # ── Queries ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_all(
        search: str = None,
        category_id: int = None,
        supplier_id: int = None,
        status: str = None,
        show_zero: bool = True,
        page: int = 1,
        per_page: int = 50,
    ):
        """Return a paginated, filtered list of products."""
        query = Product.query.filter(Product.deleted_at.is_(None)).filter(
            Product.is_active == True
        )

        # Search across brand, item, SKU
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Product.brand.ilike(pattern),
                    Product.item.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            )

        # Category filter
        if category_id:
            query = query.filter(Product.category_id == category_id)

        # Supplier filter
        if supplier_id:
            query = query.filter(Product.supplier_id == supplier_id)

        # Status filter (computed in SQL to avoid loading all rows)
        if status == "OUT":
            query = query.filter(Product.current_stock == 0)
        elif status == "LOW":
            query = query.filter(
                Product.current_stock > 0,
                Product.current_stock <= Product.reorder_level,
            )
        elif status == "OK":
            query = query.filter(Product.current_stock > Product.reorder_level)

        # Hide zero-stock products if requested
        if not show_zero:
            query = query.filter(Product.current_stock > 0)

        # Sort: non-zero OK first, then LOW, then OUT; within those by category + brand
        query = query.order_by(
            Product.current_stock == 0,  # OUT last (True = 1)
            (Product.current_stock > 0)
            & (Product.current_stock <= Product.reorder_level),  # LOW middle
            Product.category_id,
            Product.brand,
        )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        from app.schemas.product_schema import products_schema
        from app.utils.pagination import build_meta

        return products_schema.dump(pagination.items), build_meta(pagination)

    @staticmethod
    def get_by_id(product_id: int) -> dict:
        """Return a single product or raise LookupError."""
        product = Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None),
        ).first()
        if not product:
            raise LookupError(f"Product {product_id} not found.")
        return ProductService._serialise(product)

    @staticmethod
    def get_reorder_required() -> list[dict]:
        """Return all products where current_stock <= reorder_level."""
        products = (
            Product.query.filter(Product.deleted_at.is_(None))
            .filter(Product.is_active == True)
            .filter(Product.current_stock <= Product.reorder_level)
            .order_by(Product.current_stock, Product.category_id, Product.brand)
            .all()
        )
        from app.schemas.product_schema import products_schema

        return products_schema.dump(products)

    # ── Mutations ─────────────────────────────────────────────────────────────

    @staticmethod
    def create(data: dict) -> dict:
        """
        Create a product:
        1. Validate category and supplier.
        2. INSERT with a temporary SKU.
        3. Flush to get the auto-incremented ID.
        4. Update SKU to {prefix}-{id:04d}.
        5. Create a NEW_PRODUCT stock transaction if opening_stock > 0.
        """
        cat = ProductService._assert_category(data["category_id"])

        supplier_id = data.get("supplier_id")
        if supplier_id:
            ProductService._assert_supplier(supplier_id)

        opening_stock = int(data.get("opening_stock", 0))
        product_id = next_id(Product)

        product = Product(
            id=product_id,
            brand=data["brand"],
            item=data["item"],
            pack_size=data["pack_size"],
            category_id=data["category_id"],
            supplier_id=supplier_id,
            current_stock=opening_stock,
            reorder_level=int(data.get("reorder_level", 5)),
            purchase_price=float(data.get("purchase_price", 0.0)),
            selling_price=float(data.get("selling_price", 0.0)),
            notes=data.get("notes") or "",
            sku=f"{cat.sku_prefix}-{product_id:04d}",
        )
        db.session.add(product)

        # Stock transaction for opening inventory
        if opening_stock > 0:
            txn = StockTransaction(
                id=next_id(StockTransaction),
                product_id=product.id,
                transaction_type="NEW_PRODUCT",
                quantity_change=opening_stock,
                previous_qty=0,
                new_qty=opening_stock,
                reference_type="new_product",
                notes="Opening stock on product creation",
                transaction_date=date.today(),
                transaction_time=datetime.utcnow().time(),
            )
            db.session.add(txn)

        db.session.commit()
        return ProductService._serialise(product)

    @staticmethod
    def update(product_id: int, data: dict) -> dict:
        """
        Update product master data (brand, item, pack_size, prices, etc.).
        Does NOT change current_stock — that is managed via stock transactions.
        """
        product = Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None),
        ).first()
        if not product:
            raise LookupError(f"Product {product_id} not found.")

        # Validate FK changes
        if "category_id" in data and data["category_id"] != product.category_id:
            ProductService._assert_category(data["category_id"])

        supplier_id = data.get("supplier_id", "NOT_SET")
        if supplier_id != "NOT_SET" and supplier_id is not None:
            ProductService._assert_supplier(supplier_id)

        editable_fields = [
            "brand",
            "item",
            "pack_size",
            "category_id",
            "supplier_id",
            "reorder_level",
            "purchase_price",
            "selling_price",
            "notes",
        ]
        for field in editable_fields:
            if field in data:
                setattr(product, field, data[field])

        db.session.commit()
        return ProductService._serialise(product)

    @staticmethod
    def delete(product_id: int) -> None:
        """
        Soft-delete a product (sets deleted_at + is_active=False).
        Raises LookupError if not found.
        """
        product = Product.query.filter(
            Product.id == product_id,
            Product.deleted_at.is_(None),
        ).first()
        if not product:
            raise LookupError(f"Product {product_id} not found.")

        product.deleted_at = datetime.utcnow()
        product.is_active = False
        db.session.commit()

    @staticmethod
    def delete_all_zero_stock() -> int:
        """
        Soft-delete all active products with current_stock == 0.
        Returns the count of products deleted.
        """
        products = (
            Product.query.filter(Product.deleted_at.is_(None))
            .filter(Product.is_active == True)
            .filter(Product.current_stock == 0)
            .all()
        )
        now = datetime.utcnow()
        for p in products:
            p.deleted_at = now
            p.is_active = False
        db.session.commit()
        return len(products)
