from datetime import date

from sqlalchemy import inspect, text

from app import create_app, db


def unwrap(response):
    body = response.get_json(silent=True)
    if response.status_code >= 400:
        raise AssertionError(f"{response.request.method} {response.request.path} -> {response.status_code}: {body}")
    return body or {}


def first_id(rows):
    if not rows:
        raise AssertionError("Expected at least one row")
    return rows[0]["id"]


def main():
    app = create_app()
    client = app.test_client()
    today = date.today().isoformat()

    with app.app_context():
        engine = db.engine
        if engine.url.get_backend_name() != "mysql":
            raise RuntimeError(f"Expected MySQL, got {engine.url.get_backend_name()}")

        with engine.connect() as conn:
            database_name = conn.execute(text("SELECT DATABASE()")).scalar()
            print(f"database={database_name}")
            tables = inspect(conn).get_table_names()
            print("tables=" + ",".join(tables))
            for table in tables:
                quoted = f"`{table.replace('`', '``')}`"
                count = conn.execute(text(f"SELECT COUNT(*) FROM {quoted}")).scalar()
                print(f"count.{table}={count}")

    categories = unwrap(client.get("/api/v1/categories?per_page=200")).get("data", [])
    if not categories:
        raise AssertionError("No categories found. Existing schema/data must include at least one category for product tests.")
    category_id = first_id(categories)

    supplier_payload = {
        "name": f"API Test Supplier {today}",
        "contact_person": "API Tester",
        "mobile": "9999990001",
        "address": "Verification",
        "gst": "TESTGST001",
        "notes": "Created by verify_mysql_api.py",
    }
    supplier = unwrap(client.post("/api/v1/suppliers", json=supplier_payload))["data"]
    supplier_id = supplier["id"]
    print(f"supplier.create={supplier_id}")

    supplier = unwrap(client.put(f"/api/v1/suppliers/{supplier_id}", json={"notes": "Updated by API test"}))["data"]
    print(f"supplier.update={supplier['id']}")

    product_payload = {
        "brand": "API Test",
        "item": f"Inventory Item {today}",
        "pack_size": "1 pc",
        "category_id": category_id,
        "supplier_id": supplier_id,
        "reorder_level": 2,
        "purchase_price": 10,
        "selling_price": 15,
        "opening_stock": 5,
        "notes": "Created by verify_mysql_api.py",
    }
    product = unwrap(client.post("/api/v1/products", json=product_payload))["data"]
    product_id = product["id"]
    print(f"product.create={product_id}")

    product = unwrap(client.put(f"/api/v1/products/{product_id}", json={"notes": "Updated by API test", "reorder_level": 3}))["data"]
    print(f"product.update={product['id']}")

    products = unwrap(client.get("/api/v1/products?per_page=200")).get("data", [])
    if not any(row["id"] == product_id for row in products):
        raise AssertionError("Created product was not returned by fetch products")
    print("product.fetch=ok")

    stock_in = unwrap(client.post("/api/v1/stock-transactions/stock-in", json={
        "product_id": product_id,
        "quantity": 4,
        "notes": "API stock in test",
    }))["data"]
    print(f"stock_in.transaction={stock_in.get('transaction_id')}")

    adjustment = unwrap(client.post("/api/v1/stock-transactions/adjustment", json={
        "product_id": product_id,
        "actual_stock": 8,
        "reason": "API Test",
        "notes": "API adjustment test",
    }))["data"]
    print(f"adjustment.transaction={adjustment.get('transaction_id')}")

    transactions = unwrap(client.get(f"/api/v1/stock-transactions?product_id={product_id}&per_page=100")).get("data", [])
    if not transactions:
        raise AssertionError("Stock history did not return transactions for test product")
    print(f"stock_history.fetch={len(transactions)}")

    purchase = unwrap(client.post("/api/v1/purchases", json={
        "supplier_id": supplier_id,
        "purchase_date": today,
        "invoice_number": f"API-PUR-{product_id}",
        "tax_amount": 0,
        "notes": "API purchase test",
        "items": [{"product_id": product_id, "quantity": 2, "rate": 10}],
    }))["data"]
    print(f"purchase.create={purchase['id']}")

    purchases = unwrap(client.get("/api/v1/purchases?per_page=100")).get("data", [])
    if not any(row["id"] == purchase["id"] for row in purchases):
        raise AssertionError("Created purchase was not returned by fetch purchases")
    print("purchase.fetch=ok")

    sale = unwrap(client.post("/api/v1/sales", json={
        "customer_name": "API Test Customer",
        "customer_mobile": "9999990002",
        "sale_date": today,
        "discount_amount": 0,
        "notes": "API sale test",
        "items": [{"product_id": product_id, "quantity": 1, "rate": 15}],
    }))["data"]
    print(f"sale.create={sale['id']}")

    sales = unwrap(client.get("/api/v1/sales?per_page=100")).get("data", [])
    if not any(row["id"] == sale["id"] for row in sales):
        raise AssertionError("Created sale was not returned by fetch sales")
    print("sale.fetch=ok")

    products_after = unwrap(client.get("/api/v1/products?per_page=200")).get("data", [])
    product_after = next(row for row in products_after if row["id"] == product_id)
    print(f"dashboard.products={len(products_after)}")
    print(f"dashboard.product_stock={product_after['current_stock']}")
    print(f"dashboard.today_purchases={sum(float(row.get('total_amount') or 0) for row in purchases if row.get('purchase_date') == today)}")
    print(f"dashboard.today_sales={sum(float(row.get('total_amount') or 0) for row in sales if row.get('sale_date') == today)}")

    unwrap(client.delete(f"/api/v1/products/{product_id}"))
    print(f"product.delete={product_id}")
    unwrap(client.delete(f"/api/v1/suppliers/{supplier_id}"))
    print(f"supplier.delete={supplier_id}")


if __name__ == "__main__":
    main()
