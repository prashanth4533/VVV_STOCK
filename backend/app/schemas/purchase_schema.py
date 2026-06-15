from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE


# ─── Nested schemas ────────────────────────────────────────────────────────────


class SupplierBriefSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    name = fields.Str()
    mobile = fields.Str(allow_none=True)
    gst = fields.Str(allow_none=True)


class PurchaseItemOutSchema(Schema):
    """Serialises a PurchaseItem model instance."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
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


# ─── Output schemas ────────────────────────────────────────────────────────────


class PurchaseSchema(Schema):
    """List view — header only, no items."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    purchase_no = fields.Str()
    purchase_date = fields.Date(format="iso")
    supplier_id = fields.Int()
    supplier = fields.Nested(SupplierBriefSchema)
    invoice_number = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)
    subtotal = fields.Float()
    tax_amount = fields.Float()
    total_amount = fields.Float()
    status = fields.Str()
    created_at = fields.DateTime(format="iso", dump_default=None)


class PurchaseDetailSchema(PurchaseSchema):
    """Detail view — header + items."""

    items = fields.List(fields.Nested(PurchaseItemOutSchema))


# ─── Input schemas ─────────────────────────────────────────────────────────────


class PurchaseItemInputSchema(Schema):
    """Validates a single line item inside a create-purchase request."""

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


class PurchaseCreateSchema(Schema):
    """Validates POST /purchases request body."""

    class Meta:
        unknown = EXCLUDE

    supplier_id = fields.Int(
        required=True,
        error_messages={"required": "supplier_id is required."},
    )
    purchase_date = fields.Date(
        load_default=None,
        allow_none=True,
        format="iso",
    )
    invoice_number = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=64),
    )
    notes = fields.Str(load_default=None, allow_none=True)
    tax_amount = fields.Float(
        load_default=0.0,
        validate=validate.Range(min=0, error="tax_amount must be >= 0."),
    )
    items = fields.List(
        fields.Nested(PurchaseItemInputSchema),
        required=True,
        validate=validate.Length(min=1, error="At least one item is required."),
        error_messages={"required": "items is required."},
    )

    @validates("supplier_id")
    def validate_supplier_id(self, value):
        if value <= 0:
            raise ValidationError("supplier_id must be a positive integer.")


# ─── Schema singletons ─────────────────────────────────────────────────────────

purchase_schema = PurchaseSchema()
purchases_schema = PurchaseSchema(many=True)
purchase_detail_schema = PurchaseDetailSchema()
purchases_detail_schema = PurchaseDetailSchema(many=True)
purchase_create_schema = PurchaseCreateSchema()
