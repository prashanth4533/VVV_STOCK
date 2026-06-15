from app import db
from app.models.category import Category
from app.models.product import Product
from app.utils.id_utils import next_id


class CategoryService:
    @staticmethod
    def get_all(include_stats: bool = False) -> list[dict]:
        """Return all categories ordered by sort_order, with optional per-category stats."""
        categories = Category.query.order_by(Category.sort_order, Category.name).all()

        from app.schemas.category_schema import category_schema

        result = []
        for cat in categories:
            data = category_schema.dump(cat)

            if include_stats:
                prods = (
                    Product.query.filter_by(category_id=cat.id)
                    .filter(Product.deleted_at.is_(None))
                    .all()
                )
                data["stats"] = {
                    "sku_count": len(prods),
                    "total_units": sum(p.current_stock for p in prods),
                    "out": sum(1 for p in prods if p.current_stock == 0),
                    "low": sum(
                        1 for p in prods if 0 < p.current_stock <= p.reorder_level
                    ),
                    "reorder": sum(
                        1 for p in prods if p.current_stock <= p.reorder_level
                    ),
                }
            else:
                data.pop("stats", None)

            result.append(data)

        return result

    @staticmethod
    def get_by_id(category_id: int) -> dict:
        """Return a single category or raise ValueError if not found."""
        cat = Category.query.get(category_id)
        if not cat:
            raise LookupError(f"Category {category_id} not found.")

        from app.schemas.category_schema import category_schema

        data = category_schema.dump(cat)
        data.pop("stats", None)
        return data

    @staticmethod
    def create(data: dict) -> dict:
        """Create a new category. Raises ValueError on duplicate name."""
        existing = Category.query.filter_by(name=data["name"]).first()
        if existing:
            raise ValueError(f"Category '{data['name']}' already exists.")

        cat = Category(
            id=next_id(Category),
            name=data["name"],
            sku_prefix=data["sku_prefix"].upper(),
            display_color=data.get("display_color"),
            display_bg=data.get("display_bg"),
            sort_order=data.get("sort_order", 0),
        )
        db.session.add(cat)
        db.session.commit()

        from app.schemas.category_schema import category_schema

        result = category_schema.dump(cat)
        result.pop("stats", None)
        return result

    @staticmethod
    def update(category_id: int, data: dict) -> dict:
        """Update an existing category. Raises LookupError / ValueError."""
        cat = Category.query.get(category_id)
        if not cat:
            raise LookupError(f"Category {category_id} not found.")

        # Check name uniqueness if changing
        new_name = data.get("name")
        if new_name and new_name != cat.name:
            conflict = Category.query.filter_by(name=new_name).first()
            if conflict:
                raise ValueError(f"Category '{new_name}' already exists.")

        if "name" in data:
            cat.name = data["name"]
        if "sku_prefix" in data:
            cat.sku_prefix = data["sku_prefix"].upper()
        if "display_color" in data:
            cat.display_color = data["display_color"]
        if "display_bg" in data:
            cat.display_bg = data["display_bg"]
        if "sort_order" in data:
            cat.sort_order = data["sort_order"]

        db.session.commit()

        from app.schemas.category_schema import category_schema

        result = category_schema.dump(cat)
        result.pop("stats", None)
        return result

    @staticmethod
    def delete(category_id: int) -> None:
        """Delete category. Raises LookupError if not found; ValueError if products exist."""
        cat = Category.query.get(category_id)
        if not cat:
            raise LookupError(f"Category {category_id} not found.")

        # Block if active products reference this category
        product_count = (
            Product.query.filter_by(category_id=category_id)
            .filter(Product.deleted_at.is_(None))
            .count()
        )
        if product_count > 0:
            raise ValueError(
                f"Cannot delete: {product_count} product(s) belong to this category. "
                "Reassign or delete the products first."
            )

        db.session.delete(cat)
        db.session.commit()
