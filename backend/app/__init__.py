import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_marshmallow import Marshmallow

from config import config_by_name

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()


def create_app():
    app = Flask(__name__)

    # Load config
    env = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name[env])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config["CORS_ORIGINS"])
    ma.init_app(app)

    # Import models so Alembic sees them
    from app.models import (  # noqa: F401
        category,
        supplier,
        product,
        purchase,
        purchase_item,
        sale,
        sale_item,
        stock_transaction,
        eod_history,
        eod_draft,
        setting,
    )

    # Register blueprints
    from app.routes import (
        categories_bp,
        suppliers_bp,
        products_bp,
        stock_transactions_bp,
        purchases_bp,
        sales_bp,
    )

    app.register_blueprint(categories_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(stock_transactions_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(sales_bp)

    # Global error handlers
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "BAD_REQUEST", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "NOT_FOUND", "message": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "METHOD_NOT_ALLOWED", "message": str(e)}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(
            {"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."}
        ), 500

    # Health check
    @app.route("/api/v1/health")
    def health():
        return {"status": "ok", "service": "vvv-stock-api"}

    return app
