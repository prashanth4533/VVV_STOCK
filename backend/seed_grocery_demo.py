from datetime import date, time
from decimal import Decimal

from app import create_app, db
from app.models.category import Category
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stock_transaction import StockTransaction
from app.models.supplier import Supplier


CATEGORIES = [
    ("Rice", "RCE", "#2563eb", "#dbeafe"),
    ("Dal", "DAL", "#d97706", "#fef3c7"),
    ("Oil", "OIL", "#16a34a", "#dcfce7"),
    ("Sugar", "SUG", "#9333ea", "#f3e8ff"),
    ("Spices", "SPC", "#dc2626", "#fee2e2"),
]

SUPPLIERS = [
    {
        "name": "ABC Traders",
        "contact_person": "Arun Kumar",
        "mobile": "9876501001",
        "address": "Koyambedu Wholesale Market, Chennai",
        "gst": "33ABCDE1234F1Z5",
        "notes": "Rice and grocery staples",
    },
    {
        "name": "Madurai Foods",
        "contact_person": "Meenakshi Raman",
        "mobile": "9876501002",
        "address": "East Masi Street, Madurai",
        "gst": "33MADFO5678L1Z2",
        "notes": "Dal and spices supplier",
    },
    {
        "name": "Vaigai Distributors",
        "contact_person": "Sathish Vel",
        "mobile": "9876501003",
        "address": "Vaigai Industrial Estate, Madurai",
        "gst": "33VAIGA9012P1Z8",
        "notes": "Edible oil and packaged goods",
    },
]

PRODUCTS = [
    ("RCE-001", "Ponni", "Rice", "25kg", "Rice", "ABC Traders", 1250, 1425, 8),
    ("DAL-001", "Toor", "Dal", "1kg", "Dal", "Madurai Foods", 115, 138, 25),
    ("DAL-002", "Urad", "Dal", "1kg", "Dal", "Madurai Foods", 110, 132, 20),
    ("OIL-001", "Groundnut", "Oil", "1L", "Oil", "Vaigai Distributors", 165, 195, 18),
    ("SUG-001", "Sugar", "", "1kg", "Sugar", "ABC Traders", 38, 45, 30),
    ("SPC-001", "Chilli", "Powder", "500g", "Spices", "Madurai Foods", 92, 118, 12),
    ("SPC-002", "Turmeric", "Powder", "500g", "Spices", "Madurai Foods", 68, 88, 12),
    ("DAL-003", "Moong", "Dal", "1kg", "Dal", "Madurai Foods", 105, 128, 20),
    ("DAL-004", "Bengal Gram", "", "1kg", "Dal", "Madurai Foods", 82, 102, 22),
    ("OIL-002", "Sunflower", "Oil", "1L", "Oil", "Vaigai Distributors", 135, 160, 18),
]

PURCHASES = [
    {
        "purchase_no": "PO-0001",
        "purchase_date": date(2026, 6, 8),
        "supplier": "ABC Traders",
        "invoice_number": "ABC-260608",
        "tax_amount": Decimal("850.00"),
        "items": [("RCE-001", 16), ("SUG-001", 90)],
    },
    {
        "purchase_no": "PO-0002",
        "purchase_date": date(2026, 6, 9),
        "supplier": "Madurai Foods",
        "invoice_number": "MF-260609",
        "tax_amount": Decimal("620.00"),
        "items": [("DAL-001", 80), ("DAL-002", 65), ("DAL-003", 55), ("DAL-004", 70), ("SPC-001", 40), ("SPC-002", 36)],
    },
    {
        "purchase_no": "PO-0003",
        "purchase_date": date(2026, 6, 10),
        "supplier": "Vaigai Distributors",
        "invoice_number": "VD-260610",
        "tax_amount": Decimal("540.00"),
        "items": [("OIL-001", 48), ("OIL-002", 60)],
    },
]

SALES = [
    {
        "sale_no": "SO-0001",
        "sale_date": date(2026, 6, 11),
        "customer_name": "Sri Lakshmi Stores",
        "customer_mobile": "9840011111",
        "discount_amount": Decimal("120.00"),
        "items": [("RCE-001", 4), ("DAL-001", 18), ("OIL-001", 10), ("SUG-001", 25)],
    },
    {
        "sale_no": "SO-0002",
        "sale_date": date(2026, 6, 12),
        "customer_name": "Meena Mini Mart",
        "customer_mobile": "9840022222",
        "discount_amount": Decimal("75.00"),
        "items": [("DAL-002", 20), ("DAL-003", 15), ("SPC-001", 12), ("SPC-002", 10), ("OIL-002", 16)],
    },
    {
        "sale_no": "SO-0003",
        "sale_date": date(2026, 6, 13),
        "customer_name": "VVV Counter Sale",
        "customer_mobile": None,
        "discount_amount": Decimal("0.00"),
        "items": [("RCE-001", 3), ("DAL-004", 22), ("OIL-001", 8), ("SUG-001", 20), ("OIL-002", 12)],
    },
]


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def clear_demo_data():
    for model in (StockTransaction, SaleItem, Sale, PurchaseItem, Purchase, Product, Supplier, Category):
        db.session.query(model).delete()
    db.session.commit()


def seed_categories():
    categories = {}
    for index, (name, prefix, color, bg) in enumerate(CATEGORIES, start=1):
        category = Category(
            id=index,
            name=name,
            sku_prefix=prefix,
            display_color=color,
            display_bg=bg,
            sort_order=index,
        )
        db.session.add(category)
        categories[name] = category
    db.session.flush()
    return categories


def seed_suppliers():
    suppliers = {}
    for index, payload in enumerate(SUPPLIERS, start=1):
        supplier = Supplier(id=index, **payload, is_active=True)
        db.session.add(supplier)
        suppliers[payload["name"]] = supplier
    db.session.flush()
    return suppliers


def seed_products(categories, suppliers):
    products = {}
    for index, (sku, brand, item, pack, category_name, supplier_name, purchase_price, selling_price, reorder_level) in enumerate(PRODUCTS, start=1):
        product = Product(
            id=index,
            sku=sku,
            brand=brand,
            item=item,
            pack_size=pack,
            category=categories[category_name],
            supplier=suppliers[supplier_name],
            current_stock=0,
            reorder_level=reorder_level,
            purchase_price=money(purchase_price),
            selling_price=money(selling_price),
            notes="Demo grocery inventory item",
            is_active=True,
        )
        db.session.add(product)
        products[sku] = product
    db.session.flush()
    return products


def add_stock_transaction(product, txn_type, qty_change, ref_type, ref_id, txn_date, notes, txn_time=time(10, 30)):
    previous_qty = int(product.current_stock or 0)
    new_qty = previous_qty + int(qty_change)
    product.current_stock = new_qty
    txn_id = db.session.query(StockTransaction).count() + 1
    db.session.add(
        StockTransaction(
            id=txn_id,
            product=product,
            transaction_type=txn_type,
            quantity_change=int(qty_change),
            previous_qty=previous_qty,
            new_qty=new_qty,
            reference_type=ref_type,
            reference_id=ref_id,
            notes=notes,
            transaction_date=txn_date,
            transaction_time=txn_time,
        )
    )


def seed_purchases(products, suppliers):
    purchase_item_id = 1
    for purchase_id, payload in enumerate(PURCHASES, start=1):
        subtotal = Decimal("0.00")
        purchase = Purchase(
            id=purchase_id,
            purchase_no=payload["purchase_no"],
            purchase_date=payload["purchase_date"],
            supplier=suppliers[payload["supplier"]],
            invoice_number=payload["invoice_number"],
            notes="Demo purchase for grocery inventory validation",
            tax_amount=payload["tax_amount"],
            status="confirmed",
        )
        db.session.add(purchase)
        db.session.flush()

        for sku, quantity in payload["items"]:
            product = products[sku]
            line_total = money(product.purchase_price) * quantity
            subtotal += line_total
            db.session.add(
                PurchaseItem(
                    id=purchase_item_id,
                    purchase=purchase,
                    product=product,
                    quantity=quantity,
                    rate=money(product.purchase_price),
                    line_total=line_total,
                )
            )
            purchase_item_id += 1
            add_stock_transaction(
                product,
                "STOCK_IN",
                quantity,
                "purchase",
                purchase.id,
                payload["purchase_date"],
                f"Purchase {purchase.purchase_no}",
                time(9, 45),
            )

        purchase.subtotal = subtotal
        purchase.total_amount = subtotal + payload["tax_amount"]


def seed_sales(products):
    sale_item_id = 1
    for sale_id, payload in enumerate(SALES, start=1):
        subtotal = Decimal("0.00")
        sale = Sale(
            id=sale_id,
            sale_no=payload["sale_no"],
            sale_date=payload["sale_date"],
            customer_name=payload["customer_name"],
            customer_mobile=payload["customer_mobile"],
            notes="Demo sale for grocery inventory validation",
            discount_amount=payload["discount_amount"],
            status="confirmed",
        )
        db.session.add(sale)
        db.session.flush()

        for sku, quantity in payload["items"]:
            product = products[sku]
            line_total = money(product.selling_price) * quantity
            subtotal += line_total
            db.session.add(
                SaleItem(
                    id=sale_item_id,
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    rate=money(product.selling_price),
                    line_total=line_total,
                )
            )
            sale_item_id += 1
            add_stock_transaction(
                product,
                "STOCK_OUT",
                -quantity,
                "sale",
                sale.id,
                payload["sale_date"],
                f"Sale {sale.sale_no}",
                time(17, 15),
            )

        sale.subtotal = subtotal
        sale.total_amount = subtotal - payload["discount_amount"]


def seed_manual_adjustments(products):
    add_stock_transaction(
        products["SPC-001"],
        "ADJUSTMENT",
        -1,
        "adjustment",
        None,
        date(2026, 6, 13),
        "Damaged packet removed during stock check",
        time(18, 5),
    )
    add_stock_transaction(
        products["RCE-001"],
        "ADJUSTMENT",
        1,
        "adjustment",
        None,
        date(2026, 6, 13),
        "Physical count correction",
        time(18, 10),
    )


def seed():
    app = create_app()
    with app.app_context():
        clear_demo_data()
        categories = seed_categories()
        suppliers = seed_suppliers()
        products = seed_products(categories, suppliers)
        seed_purchases(products, suppliers)
        seed_sales(products)
        seed_manual_adjustments(products)
        db.session.commit()

        print("Seeded grocery demo data")
        for model, label in (
            (Category, "categories"),
            (Supplier, "suppliers"),
            (Product, "products"),
            (Purchase, "purchases"),
            (Sale, "sales"),
            (StockTransaction, "stock_transactions"),
        ):
            print(f"{label}: {db.session.query(model).count()}")


if __name__ == "__main__":
    seed()
