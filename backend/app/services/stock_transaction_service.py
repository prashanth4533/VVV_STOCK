from app.models.stock_transaction import StockTransaction


class StockTransactionService:
    """Read-only query layer for stock_transactions."""

    @staticmethod
    def get_all(
        product_id: int = None,
        transaction_type: str = None,
        from_date=None,
        to_date=None,
        page: int = 1,
        per_page: int = 50,
    ):
        """
        Return paginated stock transactions with optional filters.
        Eagerly loads the related product (via joinedload) to avoid N+1.
        """
        from sqlalchemy.orm import joinedload

        query = StockTransaction.query.options(joinedload(StockTransaction.product))

        if product_id:
            query = query.filter(StockTransaction.product_id == product_id)

        if transaction_type:
            txn_type_upper = transaction_type.upper()
            valid_types = {
                "STOCK_IN",
                "STOCK_OUT",
                "ADJUSTMENT",
                "EOD_COUNT",
                "NEW_PRODUCT",
            }
            if txn_type_upper not in valid_types:
                raise ValueError(
                    f"transaction_type must be one of: {', '.join(sorted(valid_types))}"
                )
            query = query.filter(StockTransaction.transaction_type == txn_type_upper)

        if from_date:
            query = query.filter(StockTransaction.transaction_date >= from_date)

        if to_date:
            query = query.filter(StockTransaction.transaction_date <= to_date)

        query = query.order_by(
            StockTransaction.transaction_date.desc(),
            StockTransaction.id.desc(),
        )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        from app.schemas.stock_transaction_schema import stock_transactions_schema
        from app.utils.pagination import build_meta

        return stock_transactions_schema.dump(pagination.items), build_meta(pagination)
