"""
Database seed script for VVV Stock.
Run with: flask seed
Or: python seed.py
"""

from app import create_app, db
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.setting import Setting


CATEGORIES = [
    {
        "name": "Toor Dal",
        "sku_prefix": "TOR",
        "display_color": "#2d6a4f",
        "display_bg": "#e8f5e9",
        "sort_order": 1,
    },
    {
        "name": "Roasted Groundnut",
        "sku_prefix": "RGN",
        "display_color": "#c07028",
        "display_bg": "#fff3e0",
        "sort_order": 2,
    },
    {
        "name": "Dal Varieties",
        "sku_prefix": "DAL",
        "display_color": "#1a56a0",
        "display_bg": "#e3f0ff",
        "sort_order": 3,
    },
    {
        "name": "Peas",
        "sku_prefix": "PEA",
        "display_color": "#3a7d44",
        "display_bg": "#e8f5e9",
        "sort_order": 4,
    },
    {
        "name": "Green Gram",
        "sku_prefix": "GRG",
        "display_color": "#6b3fa0",
        "display_bg": "#f3e8ff",
        "sort_order": 5,
    },
    {
        "name": "Groundnuts",
        "sku_prefix": "GND",
        "display_color": "#9c6b00",
        "display_bg": "#fffde7",
        "sort_order": 6,
    },
    {
        "name": "Grains & Rice",
        "sku_prefix": "GRC",
        "display_color": "#a04020",
        "display_bg": "#fff3e0",
        "sort_order": 7,
    },
    {
        "name": "Beans",
        "sku_prefix": "BNS",
        "display_color": "#5a5a5a",
        "display_bg": "#f5f5f5",
        "sort_order": 8,
    },
]

SUPPLIERS = [
    {
        "name": "SURAJ Traders",
        "contact_person": "Ramesh",
        "mobile": "9876543210",
        "address": "Chennai",
        "gst": "33AABCS1234A1Z5",
        "notes": "",
    },
    {
        "name": "MATHURA Foods",
        "contact_person": "Suresh",
        "mobile": "9876543211",
        "address": "Madurai",
        "gst": "33AABCM5678B2Z6",
        "notes": "",
    },
    {
        "name": "AMT Traders",
        "contact_person": "Ganesh",
        "mobile": "9876543212",
        "address": "Coimbatore",
        "gst": "",
        "notes": "",
    },
]

SETTINGS = [
    {"key_name": "business_name", "value": "VVV Traders"},
    {"key_name": "whatsapp_number", "value": ""},
]


def seed():
    """Seed the database with initial data."""
    app = create_app()
    with app.app_context():
        # Categories
        existing_cats = {c.name for c in Category.query.all()}
        for cat_data in CATEGORIES:
            if cat_data["name"] not in existing_cats:
                db.session.add(Category(**cat_data))
                print(f"  + Category: {cat_data['name']}")
            else:
                print(f"  = Category exists: {cat_data['name']}")

        # Suppliers
        existing_sups = {s.name for s in Supplier.query.all()}
        for sup_data in SUPPLIERS:
            if sup_data["name"] not in existing_sups:
                db.session.add(Supplier(**sup_data))
                print(f"  + Supplier: {sup_data['name']}")
            else:
                print(f"  = Supplier exists: {sup_data['name']}")

        # Settings
        existing_settings = {s.key_name for s in Setting.query.all()}
        for setting_data in SETTINGS:
            if setting_data["key_name"] not in existing_settings:
                db.session.add(Setting(**setting_data))
                print(f"  + Setting: {setting_data['key_name']}")
            else:
                print(f"  = Setting exists: {setting_data['key_name']}")

        db.session.commit()
        print("\n✓ Seed complete.")


if __name__ == "__main__":
    seed()
