from datetime import date

from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE


class SaleItemOutSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    product_id = fields.Int()
    quantity = fields.Int()
    rate = fields.Float()
    line_total = fields.Float()
    product = fields.Method("_get_product")

    def _get_product(self, obj):
        if obj.product:
            return {
                "id": obj.product.id,
                "sku": obj.product.sku,
                "brand": obj.product.brand,
                "item": obj.product.item,
                "pack_size": obj.product.pack_size,
            }
        return None


class SaleSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    sale_no = fields.Str()
    sale_date = fields.Date(format="iso")
    customer_name = fields.Str()
    customer_mobile = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)
    subtotal = fields.Float()
    discount_amount = fields.Float()
    total_amount = fields.Float()
    status = fields.Str()
    created_at = fields.DateTime(format="iso", dump_default=None)


class SaleDetailSchema(SaleSchema):
    items = fields.List(fields.Nested(SaleItemOutSchema))


class SaleItemInputSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    product_id = fields.Int(
        required=True,
        error_messages={"required": "product_id is required for each item."},
    )
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="quantity must be at least 1."),
        error_messages={"required": "quantity is required for each item."},
    )
    rate = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="rate must be greater than 0."),
        error_messages={"required": "rate is required for each item."},
    )

    @validates("product_id")
    def validate_product_id(self, value):
        if value <= 0:
            raise ValidationError("product_id must be a positive integer.")


class SaleCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    customer_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128),
        error_messages={"required": "customer_name is required."},
    )
    customer_mobile = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=20),
    )
    sale_date = fields.Date(
        load_default=None,
        allow_none=True,
        format="iso",
    )
    notes = fields.Str(load_default=None, allow_none=True)
    discount_amount = fields.Float(
        load_default=0.0,
        validate=validate.Range(min=0, error="discount_amount must be >= 0."),
    )
    items = fields.List(
        fields.Nested(SaleItemInputSchema),
        required=True,
        validate=validate.Length(min=1, error="At least one item is required."),
        error_messages={"required": "items is required."},
    )

    @validates("customer_name")
    def validate_customer_name(self, value):
        if not value.strip():
            raise ValidationError("customer_name cannot be empty.")


sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)
sale_detail_schema = SaleDetailSchema(many=True)
sale_create_schema = SaleCreateSchema()
