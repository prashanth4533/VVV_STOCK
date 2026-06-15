from datetime import datetime

from app import db
from app.models.supplier import Supplier
from app.models.product import Product
from app.utils.id_utils import next_id


class SupplierService:
    @staticmethod
    def get_all(
        search: str = None, is_active: bool = None, page: int = 1, per_page: int = 50
    ):
        """Return paginated suppliers with optional search and active filter."""
        query = Supplier.query.filter(Supplier.deleted_at.is_(None))

        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Supplier.name.ilike(pattern),
                    Supplier.mobile.ilike(pattern),
                    Supplier.contact_person.ilike(pattern),
                )
            )

        query = query.order_by(Supplier.name)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Build serialised list with product_count
        from app.schemas.supplier_schema import supplier_schema
        from app.utils.pagination import build_meta

        items = []
        for sup in pagination.items:
            data = supplier_schema.dump(sup)
            data["product_count"] = (
                Product.query.filter_by(supplier_id=sup.id)
                .filter(Product.deleted_at.is_(None))
                .count()
            )
            items.append(data)

        return items, build_meta(pagination)

    @staticmethod
    def get_by_id(supplier_id: int) -> dict:
        """Return full supplier detail with assigned products and purchase summary."""
        sup = Supplier.query.filter(
            Supplier.id == supplier_id,
            Supplier.deleted_at.is_(None),
        ).first()
        if not sup:
            raise LookupError(f"Supplier {supplier_id} not found.")

        # Assigned products (brief)
        prods = (
            Product.query.filter_by(supplier_id=supplier_id)
            .filter(Product.deleted_at.is_(None))
            .all()
        )
        from app.schemas.product_schema import products_brief_schema

        assigned_products = products_brief_schema.dump(prods)

        # Purchase summary
        from app.models.purchase import Purchase
        from sqlalchemy import func

        summary = (
            db.session.query(
                func.count(Purchase.id).label("count"),
                func.coalesce(func.sum(Purchase.total_amount), 0).label("total_value"),
            )
            .filter(
                Purchase.supplier_id == supplier_id,
                Purchase.status != "cancelled",
            )
            .one()
        )

        from app.schemas.supplier_schema import supplier_detail_schema

        data = supplier_detail_schema.dump(sup)
        data["product_count"] = len(prods)
        data["assigned_products"] = assigned_products
        data["purchase_summary"] = {
            "count": summary.count,
            "total_value": float(summary.total_value),
        }
        return data

    @staticmethod
    def create(data: dict) -> dict:
        """Create a new supplier. Raises ValueError on duplicate name."""
        existing = (
            Supplier.query.filter_by(name=data["name"])
            .filter(Supplier.deleted_at.is_(None))
            .first()
        )
        if existing:
            raise ValueError(f"Supplier '{data['name']}' already exists.")

        sup = Supplier(
            id=next_id(Supplier),
            name=data["name"],
            contact_person=data.get("contact_person"),
            mobile=data.get("mobile"),
            address=data.get("address"),
            gst=data.get("gst"),
            notes=data.get("notes"),
        )
        db.session.add(sup)
        db.session.commit()

        from app.schemas.supplier_schema import supplier_schema

        result = supplier_schema.dump(sup)
        result["product_count"] = 0
        return result

    @staticmethod
    def update(supplier_id: int, data: dict) -> dict:
        """Update an existing supplier. Raises LookupError / ValueError."""
        sup = Supplier.query.filter(
            Supplier.id == supplier_id,
            Supplier.deleted_at.is_(None),
        ).first()
        if not sup:
            raise LookupError(f"Supplier {supplier_id} not found.")

        # Check name uniqueness if changing
        new_name = data.get("name")
        if new_name and new_name != sup.name:
            conflict = (
                Supplier.query.filter_by(name=new_name)
                .filter(
                    Supplier.deleted_at.is_(None),
                    Supplier.id != supplier_id,
                )
                .first()
            )
            if conflict:
                raise ValueError(f"Supplier '{new_name}' already exists.")

        field_map = ["name", "contact_person", "mobile", "address", "gst", "notes"]
        for field in field_map:
            if field in data:
                setattr(sup, field, data[field])

        db.session.commit()

        from app.schemas.supplier_schema import supplier_schema

        result = supplier_schema.dump(sup)
        result["product_count"] = (
            Product.query.filter_by(supplier_id=sup.id)
            .filter(Product.deleted_at.is_(None))
            .count()
        )
        return result

    @staticmethod
    def delete(supplier_id: int) -> None:
        """
        Soft-delete a supplier and set supplier_id = NULL on assigned products.
        Raises LookupError if not found.
        """
        sup = Supplier.query.filter(
            Supplier.id == supplier_id,
            Supplier.deleted_at.is_(None),
        ).first()
        if not sup:
            raise LookupError(f"Supplier {supplier_id} not found.")

        # Unlink products
        Product.query.filter_by(supplier_id=supplier_id).update(
            {"supplier_id": None}, synchronize_session=False
        )

        # Soft delete
        sup.deleted_at = datetime.utcnow()
        sup.is_active = False
        db.session.commit()
