import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app import create_app, db
from app.models.category import Category
from app.models.product import Product
from app.models.supplier import Supplier
from seed import CATEGORIES, SUPPLIERS

SUPPLIER_RECORDS = [
    {"id": 1, "name": "SURAJ Traders", "contact": "Ramesh", "mobile": "9876543210", "address": "Chennai", "gst": "33AABCS1234A1Z5", "notes": ""},
    {"id": 2, "name": "MATHURA Foods", "contact": "Suresh", "mobile": "9876543211", "address": "Madurai", "gst": "33AABCM5678B2Z6", "notes": ""},
    {"id": 3, "name": "AMT Traders", "contact": "Ganesh", "mobile": "9876543212", "address": "Coimbatore", "gst": "", "notes": ""},
]

PRODUCTS = [
    {"sku": "TOR-0001", "brand": "SURAJ", "item": "துவர பருப்பு", "pack": "50kg", "cat": "Toor Dal", "qty": 103, "reorderLevel": 20, "supplierId": 1, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "TOR-0002", "brand": "SURAJ", "item": "துவர பருப்பு", "pack": "30kg", "cat": "Toor Dal", "qty": 184, "reorderLevel": 20, "supplierId": 1, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "TOR-0003", "brand": "MATHURA", "item": "துவர பருப்பு", "pack": "50kg", "cat": "Toor Dal", "qty": 90, "reorderLevel": 15, "supplierId": 2, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "TOR-0004", "brand": "INDIA GOLD", "item": "துவர பருப்பு", "pack": "30kg", "cat": "Toor Dal", "qty": 2, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "TOR-0005", "brand": "Ananth Gold", "item": "துவர பருப்பு", "pack": "50kg", "cat": "Toor Dal", "qty": 4, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "TOR-0006", "brand": "LION", "item": "துவர பருப்பு", "pack": "30kg", "cat": "Toor Dal", "qty": 148, "reorderLevel": 20, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0007", "brand": "AMT ORANGE", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 92, "reorderLevel": 15, "supplierId": 3, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0008", "brand": "777", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 19, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0009", "brand": "AMT 777", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 0, "reorderLevel": 10, "supplierId": 3, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0010", "brand": "RR", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0011", "brand": "OLD 777", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0012", "brand": "AMT 777 BALL", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 19, "reorderLevel": 10, "supplierId": 3, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0013", "brand": "AKSHAYA", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0014", "brand": "JALLIKATTU", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 21, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0015", "brand": "KUMBAM", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 12, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "RGN-0016", "brand": "Meenakshi", "item": "வறு கடலை", "pack": "30kg", "cat": "Roasted Groundnut", "qty": 4, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0017", "brand": "KS", "item": "பாசி பருப்பு", "pack": "30kg", "cat": "Dal Varieties", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0018", "brand": "PARAS", "item": "பாசி பருப்பு", "pack": "30kg", "cat": "Dal Varieties", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0019", "brand": "தென்னை", "item": "பாசி பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0020", "brand": "MR", "item": "பாசி பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0021", "brand": "SARASWATHI", "item": "பாசி பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0022", "brand": "ஸ்வஸ்திக்", "item": "உ.பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 3, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0023", "brand": "DOSA", "item": "உ.பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0024", "brand": "JT", "item": "உ.பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0025", "brand": "மகராஜா", "item": "கடலை பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 49, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0026", "brand": "111", "item": "கடலை பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 8, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0027", "brand": "SK", "item": "பட்டாணி பருப்பு", "pack": "50kg", "cat": "Dal Varieties", "qty": 10, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0028", "brand": "DIAMOND", "item": "பட்டாணி பருப்பு", "pack": "30kg", "cat": "Dal Varieties", "qty": 43, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "DAL-0029", "brand": "plain", "item": "சிவப்பு மசூர்", "pack": "30kg", "cat": "Dal Varieties", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "PEA-0030", "brand": "KALASH", "item": "பச்சை பட்டாணி", "pack": "30kg", "cat": "Peas", "qty": 3, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "PEA-0031", "brand": "HORSE", "item": "பச்சை பட்டாணி", "pack": "30kg", "cat": "Peas", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "PEA-0032", "brand": "plain", "item": "வெள்ள பட்டாணி", "pack": "30kg", "cat": "Peas", "qty": 51, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "PEA-0033", "brand": "plain", "item": "தட்டை பயறு", "pack": "30kg", "cat": "Peas", "qty": 4, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRG-0034", "brand": "MECURY", "item": "பாசி பயறு", "pack": "30kg", "cat": "Green Gram", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRG-0035", "brand": "plain", "item": "பாசி பயறு", "pack": "30kg", "cat": "Green Gram", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRG-0036", "brand": "plain", "item": "கருப்பு உழுந்து", "pack": "30kg", "cat": "Green Gram", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRG-0037", "brand": "plain", "item": "ராஜ்மா பீன்ஸ்", "pack": "30kg", "cat": "Green Gram", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GND-0038", "brand": "2000", "item": "வெ.கடலை", "pack": "30kg", "cat": "Groundnuts", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GND-0039", "brand": "RAJAT", "item": "வெ.கடலை", "pack": "30kg", "cat": "Groundnuts", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GND-0040", "brand": "1000", "item": "வெ.கடை", "pack": "30kg", "cat": "Groundnuts", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRC-0041", "brand": "A1", "item": "அரிசி", "pack": "26kg", "cat": "Grains & Rice", "qty": 1, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRC-0042", "brand": "மல்லி", "item": "இ. அரிசி", "pack": "26kg", "cat": "Grains & Rice", "qty": 0, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRC-0043", "brand": "BABA", "item": "அரிசி", "pack": "26kg", "cat": "Grains & Rice", "qty": 1, "reorderLevel": 10, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRC-0044", "brand": "ஆசீர்வாத்", "item": "கோதுமை", "pack": "50kg", "cat": "Grains & Rice", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRC-0045", "brand": "plain", "item": "கம்பு", "pack": "50kg", "cat": "Grains & Rice", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRC-0046", "brand": "ROSE", "item": "மால்டா", "pack": "30kg", "cat": "Grains & Rice", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "GRC-0047", "brand": "LOTUS", "item": "மால்டா", "pack": "30kg", "cat": "Grains & Rice", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "BNS-0048", "brand": "plain", "item": "வெ.மொச்சை", "pack": "30kg", "cat": "Beans", "qty": 0, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
    {"sku": "BNS-0049", "brand": "plain", "item": "போர் மொச்சை", "pack": "30kg", "cat": "Beans", "qty": 1, "reorderLevel": 5, "supplierId": None, "purchasePrice": 0, "sellingPrice": 0, "notes": ""},
]


def find_supplier_by_old_id(suppliers, old_id):
    if old_id is None:
        return None
    for sup in suppliers:
        if sup.get("id") == old_id:
            return sup
    return None


def seed():
    app = create_app()
    with app.app_context():
        frontend_suppliers, frontend_products = SUPPLIER_RECORDS, PRODUCTS

        existing_categories = {c.name: c for c in Category.query.all()}
        for category_id, cat_data in enumerate(CATEGORIES, start=1):
            if cat_data["name"] not in existing_categories:
                category = Category(id=category_id, **cat_data)
                db.session.add(category)
                existing_categories[category.name] = category
                print(f"  + Category: {category.name}")

        existing_suppliers = {s.name: s for s in Supplier.query.all()}
        for supplier_id, sup_data in enumerate(SUPPLIERS, start=1):
            if sup_data["name"] not in existing_suppliers:
                supplier = Supplier(id=supplier_id, **sup_data)
                db.session.add(supplier)
                existing_suppliers[supplier.name] = supplier
                print(f"  + Supplier: {supplier.name}")

        db.session.commit()

        existing_suppliers = {s.name: s for s in Supplier.query.all()}
        existing_products = {p.sku for p in Product.query.all()}

        inserted_products = 0
        failed_records = []

        for product_id, prod_data in enumerate(frontend_products, start=1):
            sku = prod_data.get("sku")
            if not sku:
                failed_records.append({"reason": "missing_sku", "record": prod_data})
                continue
            if sku in existing_products:
                continue

            category_name = prod_data.get("cat")
            category = existing_categories.get(category_name)
            if category is None:
                failed_records.append({"sku": sku, "reason": f"missing_category:{category_name}"})
                continue

            supplier = None
            supplier_info = find_supplier_by_old_id(frontend_suppliers, prod_data.get("supplierId"))
            if supplier_info is not None:
                supplier = existing_suppliers.get(supplier_info["name"])
                if supplier is None:
                    supplier = Supplier.query.filter_by(name=supplier_info["name"]).first()
                    if supplier:
                        existing_suppliers[supplier.name] = supplier

            product = Product(
                id=product_id,
                sku=sku,
                brand=prod_data.get("brand", ""),
                item=prod_data.get("item", ""),
                pack_size=prod_data.get("pack", ""),
                category_id=category.id,
                supplier_id=supplier.id if supplier else None,
                current_stock=int(prod_data.get("qty") or 0),
                reorder_level=int(prod_data.get("reorderLevel") or 0),
                purchase_price=float(prod_data.get("purchasePrice") or 0),
                selling_price=float(prod_data.get("sellingPrice") or 0),
                notes=prod_data.get("notes") or None,
            )
            db.session.add(product)
            inserted_products += 1
            print(f"  + Product: {sku}")

        db.session.commit()

        products_count = db.session.query(Product).count()
        suppliers_count = db.session.query(Supplier).count()

        print(f"\nInserted products: {inserted_products}")
        print(f"Total products in DB: {products_count}")
        print(f"Total suppliers in DB: {suppliers_count}")
        if failed_records:
            print("Failed records:")
            for row in failed_records:
                print("  ", row)

        client = app.test_client()
        products_resp = client.get("/api/v1/products")
        suppliers_resp = client.get("/api/v1/suppliers")

        print("\nGET /api/v1/products sample:")
        print(json.dumps(products_resp.get_json(), indent=2, ensure_ascii=True)[:2000])
        print("\nGET /api/v1/suppliers sample:")
        print(json.dumps(suppliers_resp.get_json(), indent=2, ensure_ascii=True)[:2000])

        total_units = db.session.query(db.func.sum(Product.current_stock)).scalar() or 0
        out_of_stock = db.session.query(Product).filter(Product.current_stock == 0).count()
        low_stock = db.session.query(Product).filter(Product.current_stock > 0, Product.current_stock <= Product.reorder_level).count()
        reorder_required = db.session.query(Product).filter(Product.current_stock <= Product.reorder_level).count()

        print("\nDashboard metrics:")
        print(f"  Total Products: {products_count}")
        print(f"  Total Units: {total_units}")
        print(f"  Low Stock: {low_stock}")
        print(f"  Out Of Stock: {out_of_stock}")
        print(f"  Reorder Required: {reorder_required}")

    return inserted_products, suppliers_count, failed_records


if __name__ == "__main__":
    seed()
