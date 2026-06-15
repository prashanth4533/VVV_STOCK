from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE


# ─── Output schema ─────────────────────────────────────────────────────────────


class StockTransactionSchema(Schema):
    """Serialises a StockTransaction model instance."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    product_id = fields.Int()
    transaction_type = fields.Str()
    quantity_change = fields.Int()
    previous_qty = fields.Int()
    new_qty = fields.Int()
    reference_type = fields.Str()
    reference_id = fields.Int(allow_none=True)
    reason = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)
    transaction_date = fields.Date(format="iso")
    transaction_time = fields.Time(format="%H:%M:%S")
    created_by = fields.Int(allow_none=True)
    created_at = fields.DateTime(format="iso", dump_default=None)

    # Nested product brief
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


# ─── Input schemas ─────────────────────────────────────────────────────────────


class StockInSchema(Schema):
    """Validates POST /stock-transactions/stock-in"""

    class Meta:
        unknown = EXCLUDE

    product_id = fields.Int(
        required=True,
        error_messages={"required": "product_id is required."},
    )
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="quantity must be at least 1."),
        error_messages={"required": "quantity is required."},
    )
    notes = fields.Str(load_default=None, allow_none=True)

    @validates("product_id")
    def validate_product_id(self, value):
        if value <= 0:
            raise ValidationError("product_id must be a positive integer.")


class StockInBatchItemSchema(Schema):
    """A single item inside a batch stock-in request."""

    class Meta:
        unknown = EXCLUDE

    product_id = fields.Int(
        required=True,
        error_messages={"required": "product_id is required."},
    )
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="quantity must be at least 1."),
        error_messages={"required": "quantity is required."},
    )

    @validates("product_id")
    def validate_product_id(self, value):
        if value <= 0:
            raise ValidationError("product_id must be a positive integer.")


class StockInBatchSchema(Schema):
    """Validates POST /stock-transactions/stock-in/batch"""

    class Meta:
        unknown = EXCLUDE

    items = fields.List(
        fields.Nested(StockInBatchItemSchema),
        required=True,
        validate=validate.Length(min=1, error="items must contain at least one entry."),
        error_messages={"required": "items is required."},
    )
    notes = fields.Str(load_default=None, allow_none=True)


class StockAdjustmentSchema(Schema):
    """Validates POST /stock-transactions/adjustment"""

    class Meta:
        unknown = EXCLUDE

    product_id = fields.Int(
        required=True,
        error_messages={"required": "product_id is required."},
    )
    actual_stock = fields.Int(
        required=True,
        validate=validate.Range(min=0, error="actual_stock must be >= 0."),
        error_messages={"required": "actual_stock is required."},
    )
    reason = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=64),
    )
    notes = fields.Str(load_default=None, allow_none=True)

    @validates("product_id")
    def validate_product_id(self, value):
        if value <= 0:
            raise ValidationError("product_id must be a positive integer.")


# ─── Schema singletons ─────────────────────────────────────────────────────────

stock_transaction_schema = StockTransactionSchema()
stock_transactions_schema = StockTransactionSchema(many=True)
stock_in_schema = StockInSchema()
stock_in_batch_schema = StockInBatchSchema()
stock_adjustment_schema = StockAdjustmentSchema()
