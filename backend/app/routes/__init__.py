from app.routes.categories import bp as categories_bp
from app.routes.suppliers import bp as suppliers_bp
from app.routes.products import bp as products_bp
from app.routes.stock_transactions import bp as stock_transactions_bp
from app.routes.purchases import bp as purchases_bp
from app.routes.sales import bp as sales_bp
from app.routes.eod import bp as eod_bp

__all__ = [
    "categories_bp",
    "suppliers_bp",
    "products_bp",
    "stock_transactions_bp",
    "purchases_bp",
    "sales_bp",
    "eod_bp",
]
