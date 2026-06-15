from marshmallow import Schema, fields, validate, EXCLUDE


# ─── Brief schema (used inside other serialisers) ─────────────────────────────


class SupplierBriefSchema(Schema):
    """Minimal supplier info for embedding inside product responses."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    name = fields.Str()


# ─── Output schema ─────────────────────────────────────────────────────────────


class SupplierSchema(Schema):
    """Serialises a Supplier model instance."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    name = fields.Str()
    contact_person = fields.Str(allow_none=True)
    mobile = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    gst = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)
    is_active = fields.Bool()
    product_count = fields.Int(dump_default=0)


class SupplierDetailSchema(SupplierSchema):
    """Extended supplier schema for the detail endpoint (/suppliers/:id)."""

    assigned_products = fields.List(fields.Dict(), dump_default=[])
    purchase_summary = fields.Dict(dump_default={"count": 0, "total_value": 0.0})


# ─── Input schema ─────────────────────────────────────────────────────────────


class SupplierInputSchema(Schema):
    """Validates POST / PUT request bodies for suppliers."""

    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128),
        error_messages={"required": "name is required."},
    )
    contact_person = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=64),
    )
    mobile = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=20),
    )
    address = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    gst = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=20),
    )
    notes = fields.Str(load_default=None, allow_none=True)


supplier_schema = SupplierSchema()
suppliers_schema = SupplierSchema(many=True)
supplier_detail_schema = SupplierDetailSchema()
supplier_input_schema = SupplierInputSchema()
