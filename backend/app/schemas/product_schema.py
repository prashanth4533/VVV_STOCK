from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE


# ─── Brief schemas for embedding ──────────────────────────────────────────────


class CategoryBriefSchema(Schema):
    """Minimal category info embedded in product responses."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    name = fields.Str()
    sku_prefix = fields.Str()
    display_color = fields.Str(allow_none=True)
    display_bg = fields.Str(allow_none=True)


class SupplierBriefEmbedSchema(Schema):
    """Minimal supplier info embedded in product responses."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    name = fields.Str()


# ─── Output schema ─────────────────────────────────────────────────────────────


class ProductSchema(Schema):
    """Serialises a Product model instance to a dict."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    sku = fields.Str()
    brand = fields.Str()
    item = fields.Str()
    pack_size = fields.Str()
    category = fields.Nested(CategoryBriefSchema)
    supplier = fields.Nested(SupplierBriefEmbedSchema, allow_none=True)
    current_stock = fields.Int()
    reorder_level = fields.Int()
    purchase_price = fields.Float()
    selling_price = fields.Float()
    status = fields.Method("_get_status")
    notes = fields.Str(allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(format="iso", dump_default=None)

    def _get_status(self, obj):
        return obj.status


class ProductBriefSchema(Schema):
    """Minimal product info (used inside supplier detail responses)."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    sku = fields.Str()
    brand = fields.Str()
    item = fields.Str()
    pack_size = fields.Str()
    current_stock = fields.Int()
    status = fields.Method("_get_status")

    def _get_status(self, obj):
        return obj.status


# ─── Input schemas ─────────────────────────────────────────────────────────────


class ProductInputSchema(Schema):
    """Validates the POST /products request body."""

    class Meta:
        unknown = EXCLUDE

    brand = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=64),
        error_messages={"required": "brand is required."},
    )
    item = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128),
        error_messages={"required": "item is required."},
    )
    pack_size = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=16),
        error_messages={"required": "pack_size is required."},
    )
    category_id = fields.Int(
        required=True,
        error_messages={"required": "category_id is required."},
    )
    supplier_id = fields.Int(load_default=None, allow_none=True)
    opening_stock = fields.Int(load_default=0, validate=validate.Range(min=0))
    reorder_level = fields.Int(load_default=5, validate=validate.Range(min=0))
    purchase_price = fields.Float(load_default=0.0, validate=validate.Range(min=0))
    selling_price = fields.Float(load_default=0.0, validate=validate.Range(min=0))
    notes = fields.Str(load_default=None, allow_none=True)

    @validates("category_id")
    def validate_category_id(self, value):
        if value <= 0:
            raise ValidationError("category_id must be a positive integer.")


class ProductUpdateSchema(Schema):
    """Validates the PUT /products/:id request body — all fields optional."""

    class Meta:
        unknown = EXCLUDE

    brand = fields.Str(validate=validate.Length(min=1, max=64))
    item = fields.Str(validate=validate.Length(min=1, max=128))
    pack_size = fields.Str(validate=validate.Length(min=1, max=16))
    category_id = fields.Int()
    supplier_id = fields.Int(allow_none=True)
    reorder_level = fields.Int(validate=validate.Range(min=0))
    purchase_price = fields.Float(validate=validate.Range(min=0))
    selling_price = fields.Float(validate=validate.Range(min=0))
    notes = fields.Str(allow_none=True)


product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
product_brief_schema = ProductBriefSchema()
products_brief_schema = ProductBriefSchema(many=True)
product_input_schema = ProductInputSchema()
product_update_schema = ProductUpdateSchema()
