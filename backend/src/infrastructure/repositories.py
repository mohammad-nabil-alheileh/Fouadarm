# src/infrastructure/repositories.py
from sqlalchemy import select, asc, insert, update, and_
from datetime import date 
from typing import List, Optional
from src.domain.models import OrderAggregate, ProductBatchDomain
from src.infrastructure.tables import (
    products_table,
    product_batch_table, 
    orders_table, 
    order_items_table, 
    payment_table
)

class InventoryRepository:
    def __init__(self, conn):
        self.conn = conn  

    def get_batches_for_product_fifo(self, product_id: int) -> list[ProductBatchDomain]:
        """Fetches all active batches for a product, sorted oldest to newest (FIFO)"""
        stmt = (
            select(product_batch_table)
            .where(
                product_batch_table.c.product_id == product_id,
                product_batch_table.c.is_deleted == False
            )
            .order_by(asc(product_batch_table.c.date_entered))
        )
        
        rows = self.conn.execute(stmt).fetchall()
        
        return [
            ProductBatchDomain(
                product_batch_id=row.product_batch_id,
                product_id=row.product_id,
                date_entered=row.date_entered,
                count=row.count,
                trashed=row.trashed,
                quarter=row.quarter,
                foot=row.foot,
                line=row.line
            )
            for row in rows
        ]
    
    def get_all_active_products(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        """Fetches all non-deleted products, optionally filtered by creation date range."""
        stmt = select(products_table).where(products_table.c.is_deleted == False)
        
        # Apply optional date filters dynamically
        if start_date:
            stmt = stmt.where(products_table.c.created_at >= start_date)
        if end_date:
            stmt = stmt.where(products_table.c.created_at <= end_date)
            
        rows = self.conn.execute(stmt).fetchall()
        return [dict(row._mapping) for row in rows]

    def get_all_active_batches(
            self, 
            start_date: Optional[date] = None, 
            end_date: Optional[date] = None,
            only_available: bool = False
        ) -> List[dict]:
            """
            Fetches active batches across the entire nursery.
            If only_available=True, filters out batches that are completely sold or trashed out.
            """
            stmt = select(product_batch_table).where(product_batch_table.c.is_deleted == False)
            
            # 1. Apply date filters dynamically
            if start_date:
                stmt = stmt.where(product_batch_table.c.date_entered >= start_date)
            if end_date:
                stmt = stmt.where(product_batch_table.c.date_entered <= end_date)
                
            # 2. Dynamic filter: Only return rows with items still remaining inside them
            if only_available:
                stmt = stmt.where(
                    (product_batch_table.c.count - product_batch_table.c.trashed) > 0
                )
                
            rows = self.conn.execute(stmt).fetchall()
            return [dict(row._mapping) for row in rows]

    def get_active_batches_by_product(
    self, 
    product_id: int,  # Added product_id parameter
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None,
    only_available: bool = False
    ) -> List[dict]:
        """
        Fetches active batches for a specific product ID across the nursery.
        If only_available=True, filters out batches that are completely sold or trashed out.
        """
        # Base query: filter by active batches AND the specific product_id
        stmt = select(product_batch_table).where(
            product_batch_table.c.is_deleted == False,
            product_batch_table.c.product_id == product_id  # Filter for the specific product
        )
        
        # 1. Apply date filters dynamically
        if start_date:
            stmt = stmt.where(product_batch_table.c.date_entered >= start_date)
        if end_date:
            stmt = stmt.where(product_batch_table.c.date_entered <= end_date)
            
        # 2. Dynamic filter: Only return rows with items still remaining inside them
        if only_available:
            stmt = stmt.where(
                (product_batch_table.c.count - product_batch_table.c.trashed) > 0
            )
            
        rows = self.conn.execute(stmt).fetchall()
        return [dict(row._mapping) for row in rows]

class OrderRepository:
    def __init__(self, conn):
        self.conn = conn 

    def save(self, order: OrderAggregate) -> int:
        """
        Saves a complete Order Aggregate to the database.
        Handles order headers, multiple batch items, and payments atomically.
        """
        # Everything inside this block is an all-or-nothing transaction
        # 1. Insert Order Header
        order_stmt = insert(orders_table).values(
            customer_name=order.customer_name,
            order_date=order.order_date,
            total_price=order.total_price, # Evaluates override vs calculated automatically
            is_cancelled=order.is_cancelled,
            is_deleted=order.is_deleted
        )
        order_result = self.conn.execute(order_stmt)
        real_order_id = order_result.inserted_primary_key[0]

        # 2. Insert Order Items (Your new schema handles auto-increment item IDs)
        for item in order.items:
            item_stmt = insert(order_items_table).values(
                order_id=real_order_id,
                product_batch_id=item.product_batch_id,
                shipped=0,
                quantity=item.quantity,
                price_per_unit_at_that_time=item.price_per_unit,
                created_at=order.order_date,
                is_deleted=False
            )
            self.conn.execute(item_stmt)
            
            # Deduct physical stock from that batch directly
            self._deduct_batch_stock(item.product_batch_id, item.quantity)
            
        # 3. Insert Payments (Fixes the placeholder 0 with the database order_id)
        for payment in order.payments:
            payment_stmt = insert(payment_table).values(
                order_id=real_order_id,
                payment_method=payment.payment_method,
                amount=payment.amount,
                date=payment.date,
                is_refunded=payment.is_refunded,
                is_deleted=payment.is_deleted
            )
            self.conn.execute(payment_stmt)

        return real_order_id

    # In src/infrastructure/repositories.py

    def get_raw_order_line_items(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        """
        Pure Repository Method: Just fetches raw order items joined with product 
        and order metadata. No business calculations happen here.
        """
        stmt = (
            select(
                orders_table.c.customer_name,
                orders_table.c.order_date,
                products_table.c.product_id,
                products_table.c.product_name,
                order_items_table.c.quantity,
                order_items_table.c.price_per_unit_at_that_time
            )
            .select_from(
                order_items_table
                .join(orders_table, order_items_table.c.order_id == orders_table.c.order_id)
                .join(product_batch_table, order_items_table.c.product_batch_id == product_batch_table.c.product_batch_id)
                .join(products_table, product_batch_table.c.product_id == products_table.c.product_id)
            )
            .where(
                and_(
                    order_items_table.c.is_deleted == False,
                    orders_table.c.is_deleted == False
                )
            )
        )

        if start_date:
            stmt = stmt.where(orders_table.c.order_date >= start_date)
        if end_date:
            stmt = stmt.where(orders_table.c.order_date <= end_date)

        rows = self.conn.execute(stmt).fetchall()
        return [dict(row._mapping) for row in rows]

    def search_raw_orders_by_customer(self, search_term: str) -> List[dict]:
        """
        Pure Repository Method: Fetches all non-deleted order rows where 
        the customer name matches the search term (case-insensitive partial match).
        """

        stmt = (
            select(
                orders_table.c.order_id,
                orders_table.c.customer_name,
                orders_table.c.order_date,
                orders_table.c.total_price,
                orders_table.c.is_cancelled,
                products_table.c.product_name,
                order_items_table.c.quantity,
                order_items_table.c.price_per_unit_at_that_time
            )
            .select_from(
                order_items_table
                .join(orders_table, order_items_table.c.order_id == orders_table.c.order_id)
                .join(product_batch_table, order_items_table.c.product_batch_id == product_batch_table.c.product_batch_id)
                .join(products_table, product_batch_table.c.product_id == products_table.c.product_id)
            )
            .where(
                and_(
                    orders_table.c.customer_name.ilike(f"%{search_term}%"),
                    orders_table.c.is_deleted == False,
                    order_items_table.c.is_deleted == False
                )
            )
            .order_by(orders_table.c.order_date.desc())
        )

        rows = self.conn.execute(stmt).fetchall()
        return [dict(row._mapping) for row in rows]

    def _deduct_batch_stock(self, batch_id: int, quantity_sold: int):
        """Internal helper to decrease available stock in a batch row"""
        stmt = (
            update(product_batch_table)
            .where(product_batch_table.c.product_batch_id == batch_id)
            .values(count=product_batch_table.c.count - quantity_sold)
        )
        self.conn.execute(stmt)