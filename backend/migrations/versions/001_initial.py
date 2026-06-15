"""initial schema - all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-06-10 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Categories
    op.create_table(
        "categories",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("sku_prefix", sa.String(8), nullable=False),
        sa.Column("display_color", sa.String(7), nullable=True),
        sa.Column("display_bg", sa.String(7), nullable=True),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )
    op.create_index("ix_categories_sort_order", "categories", ["sort_order"])

    # Suppliers
    op.create_table(
        "suppliers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("contact_person", sa.String(64), nullable=True),
        sa.Column("mobile", sa.String(20), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("gst", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_suppliers_name", "suppliers", ["name"])
    op.create_index("ix_suppliers_mobile", "suppliers", ["mobile"])
    op.create_index("ix_suppliers_deleted_at", "suppliers", ["deleted_at"])

    # Products
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("sku", sa.String(20), nullable=False),
        sa.Column("brand", sa.String(64), nullable=False),
        sa.Column("item", sa.String(128), nullable=False),
        sa.Column("pack_size", sa.String(16), nullable=False),
        sa.Column("category_id", sa.SmallInteger(), nullable=False),
        sa.Column("supplier_id", sa.BigInteger(), nullable=True),
        sa.Column("current_stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column(
            "purchase_price", sa.Numeric(12, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "selling_price", sa.Numeric(12, 2), nullable=False, server_default="0"
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_supplier_id", "products", ["supplier_id"])
    op.create_index("ix_products_brand_item", "products", ["brand", "item"])
    op.create_index("ix_products_current_stock", "products", ["current_stock"])
    op.create_index("ix_products_deleted_at", "products", ["deleted_at"])

    # Purchases
    op.create_table(
        "purchases",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("purchase_no", sa.String(16), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("supplier_id", sa.BigInteger(), nullable=False),
        sa.Column("invoice_number", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column(
            "total_amount", sa.Numeric(14, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "confirmed", "cancelled", name="purchase_status"),
            nullable=False,
            server_default="confirmed",
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("purchase_no", name="uq_purchases_purchase_no"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_purchases_purchase_date", "purchases", ["purchase_date"])
    op.create_index("ix_purchases_supplier_id", "purchases", ["supplier_id"])
    op.create_index("ix_purchases_status", "purchases", ["status"])

    # Purchase Items
    op.create_table(
        "purchase_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("purchase_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("purchase_id", "product_id", name="uq_purchase_product"),
    )
    op.create_index("ix_purchase_items_purchase_id", "purchase_items", ["purchase_id"])
    op.create_index("ix_purchase_items_product_id", "purchase_items", ["product_id"])

    # Sales
    op.create_table(
        "sales",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("sale_no", sa.String(16), nullable=False),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("customer_name", sa.String(128), nullable=False),
        sa.Column("customer_mobile", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column(
            "discount_amount", sa.Numeric(14, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "total_amount", sa.Numeric(14, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "confirmed", "cancelled", name="sale_status"),
            nullable=False,
            server_default="confirmed",
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sale_no", name="uq_sales_sale_no"),
    )
    op.create_index("ix_sales_sale_date", "sales", ["sale_date"])
    op.create_index("ix_sales_customer_name", "sales", ["customer_name"])
    op.create_index("ix_sales_status", "sales", ["status"])

    # Sale Items
    op.create_table(
        "sale_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("sale_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("sale_id", "product_id", name="uq_sale_product"),
    )
    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"])
    op.create_index("ix_sale_items_product_id", "sale_items", ["product_id"])

    # Stock Transactions
    op.create_table(
        "stock_transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "transaction_type",
            sa.Enum(
                "STOCK_IN",
                "STOCK_OUT",
                "ADJUSTMENT",
                "EOD_COUNT",
                "NEW_PRODUCT",
                name="transaction_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("previous_qty", sa.Integer(), nullable=False),
        sa.Column("new_qty", sa.Integer(), nullable=False),
        sa.Column(
            "reference_type",
            sa.Enum(
                "purchase",
                "sale",
                "adjustment",
                "eod",
                "manual",
                "new_product",
                name="reference_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("transaction_time", sa.Time(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_stock_txn_product_created",
        "stock_transactions",
        ["product_id", "created_at"],
    )
    op.create_index("ix_stock_txn_type", "stock_transactions", ["transaction_type"])
    op.create_index("ix_stock_txn_date", "stock_transactions", ["transaction_date"])
    op.create_index(
        "ix_stock_txn_reference",
        "stock_transactions",
        ["reference_type", "reference_id"],
    )

    # EOD History
    op.create_table(
        "eod_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("count_date", sa.Date(), nullable=False),
        sa.Column("system_qty", sa.Integer(), nullable=False),
        sa.Column("physical_qty", sa.Integer(), nullable=False),
        sa.Column("difference", sa.Integer(), nullable=False),
        sa.Column("stock_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["stock_transaction_id"], ["stock_transactions.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_eod_history_session_id", "eod_history", ["session_id"])
    op.create_index("ix_eod_history_count_date", "eod_history", ["count_date"])
    op.create_index(
        "ix_eod_history_product_date", "eod_history", ["product_id", "count_date"]
    )

    # EOD Drafts
    op.create_table(
        "eod_drafts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("physical_qty", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_eod_draft_user_product"),
    )

    # Settings
    op.create_table(
        "settings",
        sa.Column("key_name", sa.String(64), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("key_name"),
    )


def downgrade():
    op.drop_table("eod_drafts")
    op.drop_table("eod_history")
    op.drop_table("stock_transactions")
    op.drop_table("sale_items")
    op.drop_table("sales")
    op.drop_table("purchase_items")
    op.drop_table("purchases")
    op.drop_table("products")
    op.drop_table("suppliers")
    op.drop_table("categories")
    op.drop_table("settings")

    # Drop ENUM types (MySQL handles these automatically, but explicit for PostgreSQL compat)
    op.execute("DROP TYPE IF EXISTS purchase_status")
    op.execute("DROP TYPE IF EXISTS sale_status")
    op.execute("DROP TYPE IF EXISTS transaction_type_enum")
    op.execute("DROP TYPE IF EXISTS reference_type_enum")
