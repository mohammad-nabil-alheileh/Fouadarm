from sqlalchemy import Table, Column, Integer, String, Date, Boolean, Numeric, ForeignKey
from src.connection import metadata

products_table = Table(
    "products",
    metadata,
    Column("product_id", Integer, primary_key=True, autoincrement=True),
    Column("product_name", String, nullable=False, unique=True),
    Column("unit_price", Numeric(10, 2), nullable=False),
    Column("is_deleted", Boolean, default=False, nullable=False),
    Column("created_at", Date, nullable=False),
)

product_batch_table = Table(
    "product_batches",
    metadata,
    Column("product_batch_id", Integer, primary_key=True, autoincrement=True), 
    Column("product_id", Integer, ForeignKey("products.product_id"), nullable=False),
    Column("date_entered", Date, nullable=False),
    Column("count", Integer, nullable=False),
    Column("trashed", Integer, nullable=False),
    Column("quarter", String, nullable=False),
    Column("foot", String, nullable=False),
    Column("line", String, nullable=False),
    Column("is_deleted", Boolean, default=False, nullable=False)
)

orders_table = Table(
    "orders",
    metadata,
    Column("order_id", Integer, primary_key=True, autoincrement=True),
    Column("customer_name", String, nullable=False),
    Column("order_date", Date, nullable=False),
    Column("total_price", Numeric(10, 2), nullable=False),
    Column("is_cancelled", Boolean, default=False, nullable=False),
    Column("is_deleted", Boolean, default=False, nullable=False),
)

order_items_table = Table(
    "order_items",
    metadata,
    Column("order_item_id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer, ForeignKey("orders.order_id"), nullable=False),
    Column("product_batch_id", Integer, ForeignKey("product_batches.product_batch_id"), nullable=False),
    Column("shipped", Integer, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("price_per_unit_at_that_time", Numeric(10, 2), nullable=False),
    Column("is_deleted", Boolean, default=False, nullable=False),
    Column("created_at", Date, nullable=False)
)

payment_table = Table(
    "payment",
    metadata,
    Column("payment_id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer, ForeignKey("orders.order_id"), nullable=False),
    Column("payment_method", String, nullable=False),  # e.g., "Regular" or "Deposit"
    Column("amount", Numeric(10, 2), nullable=False),
    Column("date", Date, nullable=False),
    Column("is_refunded", Boolean, default=False, nullable=False),
    Column("is_deleted", Boolean, default=False, nullable=False),
)