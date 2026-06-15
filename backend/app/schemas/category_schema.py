import re
from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE


# ─── Output schema (model instance → dict) ────────────────────────────────────


class CategorySchema(Schema):
    """Serialises a Category model instance to a dict."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    name = fields.Str()
    sku_prefix = fields.Str()
    display_color = fields.Str(allow_none=True)
    display_bg = fields.Str(allow_none=True)
    sort_order = fields.Int()
    # stats is injected by the service when include_stats=True
    stats = fields.Dict(dump_default=None)


# ─── Input schema (request body → validated dict) ─────────────────────────────


class CategoryInputSchema(Schema):
    """Validates POST / PUT request bodies for categories."""

    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=64),
        error_messages={"required": "name is required."},
    )
    sku_prefix = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=8),
        error_messages={"required": "sku_prefix is required."},
    )
    display_color = fields.Str(load_default=None, allow_none=True)
    display_bg = fields.Str(load_default=None, allow_none=True)
    sort_order = fields.Int(load_default=0, validate=validate.Range(min=0))

    @validates("display_color")
    def validate_display_color(self, value):
        if value is not None and not re.match(r"^#[0-9a-fA-F]{6}$", value):
            raise ValidationError("Must be a 6-digit hex color, e.g. #2d6a4f")

    @validates("display_bg")
    def validate_display_bg(self, value):
        if value is not None and not re.match(r"^#[0-9a-fA-F]{6}$", value):
            raise ValidationError("Must be a 6-digit hex color, e.g. #e8f5e9")


category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
category_input_schema = CategoryInputSchema()
