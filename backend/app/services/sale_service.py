from datetime import date

from sqlalchemy import func

from app import db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.services.stock_service import StockService


class SaleService:
    @staticmethod
    def next_number() -> str:
        result = db.session.query(func.max(Sale.sale_no)).scalar()
        if result:
            try:
                seq = int(result.split("-")[1]) + 1
            except (IndexError, ValueError):
                seq = 1
        else:
            seq = 1
        return f"SO-{seq:04d}"

    @staticmethod
    def get_all(
        from_date=None,
        to_date=None,
        search: str = None,
        page: int = 1,
        per_page: int = 50,
    ):
        from sqlalchemy.orm import joinedload

        query = Sale.query.options(joinedload(Sale.items).joinedload(SaleItem.product))

        if from_date:
            query = query.filter(Sale.sale_date >= from_date)

        if to_date:
            query = query.filter(Sale.sale_date <= to_date)

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Sale.sale_no.ilike(pattern),
                    Sale.customer_name.ilike(pattern),
                )
            )

        query = query.order_by(Sale.sale_date.desc(), Sale.id.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        from app.schemas.sale_schema import sale_detail_schema
        from app.utils.pagination import build_meta

        return sale_detail_schema.dump(pagination.items), build_meta(pagination)

    @staticmethod
    def get_by_id(sale_id: int) -> dict:
        from sqlalchemy.orm import joinedload

        sale = (
            Sale.query.options(joinedload(Sale.items).joinedload(SaleItem.product))
            .filter(Sale.id == sale_id)
            .first()
        )
        if not sale:
            raise LookupError(f"Sale {sale_id} not found.")

        from app.schemas.sale_schema import sale_schema

        return sale_schema.dump(sale)

    @staticmethod
    def create(data: dict) -> dict:
        sale_date = data.get("sale_date") or date.today()
        items_data = data["items"]

        product_ids = [item["product_id"] for item in items_data]
        products = {
            p.id: p
            for p in Product.query.filter(Product.id.in_(product_ids), Product.deleted_at.is_(None)).with_for_update().all()
        }

        missing = [pid for pid in product_ids if pid not in products]
        if missing:
            raise LookupError(f"Product(s) not found: {missing}.")

        subtotal = 0.0
        for item in items_data:
            product = products[item["product_id"]]
            quantity = item["quantity"]
            if quantity <= 0:
                raise ValueError("quantity must be greater than 0.")
            if product.current_stock < quantity:
                raise ValueError(
                    f"Insufficient stock for {product.brand} {product.item}. Available: {product.current_stock}, requested: {quantity}."
                )
            subtotal += quantity * item["rate"]

        discount_amount = data.get("discount_amount") or 0.0
        total_amount = round(subtotal - discount_amount, 2)

        sale_no = SaleService.next_number()
        sale = Sale(
            sale_no=sale_no,
            sale_date=sale_date,
            customer_name=data["customer_name"].strip(),
            customer_mobile=data.get("customer_mobile"),
            notes=data.get("notes"),
            subtotal=round(subtotal, 2),
            discount_amount=round(discount_amount, 2),
            total_amount=round(total_amount, 2),
            status="confirmed",
        )
        db.session.add(sale)
        db.session.flush()

        for item in items_data:
            product = products[item["product_id"]]
            line_total = round(item["quantity"] * item["rate"], 2)
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item["quantity"],
                rate=round(item["rate"], 2),
                line_total=line_total,
            )
            db.session.add(sale_item)

        db.session.flush()

        for item in items_data:
            product = products[item["product_id"]]
            StockService.create_transaction(
                product=product,
                txn_type="STOCK_OUT",
                quantity_change=-item["quantity"],
                ref_type="sale",
                ref_id=sale.id,
                notes=f"Sale {sale_no}",
            )

        db.session.commit()

        from app.schemas.sale_schema import sale_schema
        return sale_schema.dump(sale)
