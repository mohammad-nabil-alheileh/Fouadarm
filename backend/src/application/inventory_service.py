# src/application/inventory_service.py
from datetime import date
from decimal import Decimal
from typing import Optional, List
from src.domain.models import ProductDomain, ProductBatchDomain
from sqlalchemy import select, update, and_
from src.infrastructure.tables import  product_batch_table, products_table

from src.exceptions import (
    InvalidBatchCountError,
    ProductAlreadyExistsError,
    ProductNotFoundError,
    ProductBatchNotFoundError
)

class InventoryService:
    def __init__(self, conn, inventory_repo):
        self.conn = conn
        self.inventory_repo = inventory_repo

    def create_new_product(self, name: str, unit_price: Decimal) -> int:
        """
        Use Case: Registers a completely new plant product type in the system.
        """

        conflict_stmt = select(products_table).where(
            and_(
                products_table.c.product_name == name,
                products_table.c.is_deleted == False
            )
        )
        existing_product = self.conn.execute(conflict_stmt).fetchone()
        
        if existing_product is not None:
            raise ProductAlreadyExistsError("منتج بهذا الاسم موجود بالفعل")
        
        product = ProductDomain(
            product_id=0,
            product_name=name,
            unit_price=Decimal(str(unit_price)),
            is_deleted=False
        )
        
        
        stmt = products_table.insert().values(
            product_name=product.name,
            unit_price=product.unit_price,
            created_at=date.today(),
            is_deleted=product.is_deleted
        )
        result = self.conn.execute(stmt)
        return result.inserted_primary_key[0]

    # Add these to InventoryService in src/application/inventory_service.py

    def get_active_products_report(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        """
        Use Case: Fetch active products list for reporting (All time or by time period).
        """
        return self.inventory_repo.get_all_active_products(start_date, end_date)

    def get_active_batches_report(self, start_date: Optional[date] = None, end_date: Optional[date] = None, only_available: bool = False) -> List[dict]:
        """
        Use Case: Fetch active plant batches for nursery reporting (All time or by time period).
        """
        return self.inventory_repo.get_all_active_batches(start_date, end_date, only_available)

    def get_active_batches_for_a_product(self, start_date: Optional[date] = None, end_date: Optional[date] = None, only_available: bool = False) -> List[dict]:
        """
        Use Case: Fetch active plant batches for nursery reporting for a product (All time or by time period).
        """

        check_product_stmt = select(products_table).where(
            and_(
                products_table.c.product_id == id,
                products_table.c.is_deleted == False
            )
        )
        existing_product = self.conn.execute(check_product_stmt).fetchone()

        if existing_product is None:
            raise ProductNotFoundError("the product does not exist")

        return self.inventory_repo.get_active_batches_by_product(start_date, end_date, only_available)

    def record_new_nursery_batch(
        self, 
        product_id: int, 
        count: int, 
        quarter: str, 
        foot: str, 
        line: str
    ) -> int:
        """
        Use Case: Logs a brand new physical batch/lot of plants into a specific 
        nursery location path (Quarter, Foot, Line) for paperwork tracking.
        """

        check_product_stmt = select(products_table).where(
            and_(
                products_table.c.product_id == id,
                products_table.c.is_deleted == False
            )
        )
        existing_product = self.conn.execute(check_product_stmt).fetchone()

        if existing_product is None:
            raise ProductNotFoundError("the product does not exist")

        if count <= 0:
            raise InvalidBatchCountError("A new batch must have a plant count greater than 0.")

        # 1. Initialize our domain batch instance to structure the data safely
        batch = ProductBatchDomain(
            product_batch_id=0,  # Placeholder
            product_id=product_id,
            date_entered=date.today(),
            count=count,
            trashed=0,  # Starts perfectly healthy
            quarter=quarter,
            foot=foot,
            line=line
        )

        # 2. Persist the record directly into your product_batch_table        
        stmt = product_batch_table.insert().values(
            product_id=batch.product_id,
            date_entered=batch.date_entered,
            count=batch.count,
            trashed=batch.trashed,
            quarter=batch.quarter,
            foot=batch.foot,
            line=batch.line,
            is_deleted=False
        )
        result = self.conn.execute(stmt)
        return result.inserted_primary_key[0]
    
    def register_trashed_plants_fifo(self, product_id: int, total_to_trash: int):
        """
        Use Case: Automatically tracks and attributes dead plants to the 
        oldest available batches (FIFO) for a given product.
        """

        check_product_stmt = select(products_table).where(
            and_(
                products_table.c.product_id == id,
                products_table.c.is_deleted == False
            )
        )
        existing_product = self.conn.execute(check_product_stmt).fetchone()

        if existing_product is None:
            raise ProductNotFoundError("the product does not exist")

        if total_to_trash <= 0:
            raise InvalidBatchCountError("Quantity to trash must be greater than 0.")

        # 1. Fetch all active batches for this product sorted by oldest date (FIFO)
        # Using the same repo method we built for the order placement!
        fifo_batches = self.inventory_repo.get_batches_for_product_fifo(product_id)

        # 2. Safety check: Ensure we actually have enough plants total to trash
        total_available = sum(batch.available_stock for batch in fifo_batches)
        if total_available < total_to_trash:
            raise InvalidBatchCountError(
                f"Cannot trash {total_to_trash} plants. "
                f"Total available stock across all batches is only {total_available}."
            )

        # 3. Loop through batches using FIFO rules
        for batch in fifo_batches:
            if total_to_trash <= 0:
                break

            available = batch.available_stock
            if available <= 0:
                continue  # This batch is already fully depleted, skip it

            # Determine how much we can take from this batch
            take_from_this_batch = min(total_to_trash, available)

            # 4. Update the database row for this specific batch
            stmt = (
                update(product_batch_table)
                .where(product_batch_table.c.product_batch_id == batch.product_batch_id)
                .values(trashed=product_batch_table.c.trashed + take_from_this_batch)
            )
            self.conn.execute(stmt)

            # Decrement what's left of our target to trash
            total_to_trash -= take_from_this_batch

    def get_product_stock_summary(self, product_id: int) -> dict:
        """Use Case: Returns totals for total count, total trashed, and total sellable left."""
        fifo_batches = self.inventory_repo.get_batches_for_product_fifo(product_id)
        
        total_remaining_sellable = sum(batch.available_stock for batch in fifo_batches)
        
        return {
            "product_id": product_id,
            "total_sellable_stock": total_remaining_sellable,
            "active_batches_count": len([b for b in fifo_batches if b.available_stock > 0])
        }
    
    def update_product_details(self, product_id: int, name: Optional[str], unit_price: Optional[Decimal] = None):
        """
        Use Case: Updates basic product profiles (name or price changes).
        """

        check_product_stmt = select(products_table).where(
            and_(
                products_table.c.product_id == id,
                products_table.c.is_deleted == False
            )
        )
        existing_product = self.conn.execute(check_product_stmt).fetchone()

        if existing_product is None:
            raise ProductNotFoundError("the product does not exist")

        conflict_stmt = select(products_table).where(
            and_(
                products_table.c.product_name == name,
                products_table.c.is_deleted == False
            )
        )
        existing_product = self.conn.execute(conflict_stmt).fetchone()
        
        if existing_product is not None:
            raise ProductAlreadyExistsError("the product with this name already exists")

        if name is None and unit_price is None:
            return  

        update_values = {}
        if name is not None:
            update_values["product_name"] = name
        if unit_price is not None:
            update_values["unit_price"] = Decimal(str(unit_price))

        stmt = (
            update(products_table)
            .where(products_table.c.product_id == product_id)
            .values(**update_values)
        )
        self.conn.execute(stmt)

    def update_batch_details(
        self, 
        product_batch_id: int, 
        count: Optional[int] = None,
        quarter: Optional[str] = None,
        foot: Optional[str] = None,
        line: Optional[str] = None
    ):
        """
        Use Case: Administrative adjustment for shifting plant locations 
        or fixing manual clerical errors in batch stock counts.
        """

        # 1. Fetch current row state to validate if count changes are safe
        stmt = select(product_batch_table).where(
            product_batch_table.c.product_batch_id == product_batch_id
        )
        row = self.conn.execute(stmt).fetchone()
        if not row:
            raise ProductBatchNotFoundError(f"Batch with ID {product_batch_id} does not exist.")

        update_values = {}
        
        # 2. If adjusting the count, verify it doesn't break business rules
        if count is not None:
            if count < 0:
                raise InvalidBatchCountError("Batch count cannot be negative.")
            
            # Reconstruct model briefly to check against already trashed plants
            if count < row.trashed:
                raise InvalidBatchCountError(
                    f"Cannot set count to {count}. This batch already has "
                    f"{row.trashed} plants recorded as trashed."
                )
            update_values["count"] = count

        # 3. Handle location adjustments dynamically
        if quarter is not None:
            update_values["quarter"] = quarter
        if foot is not None:
            update_values["foot"] = foot
        if line is not None:
            update_values["line"] = line

        if update_values:
            update_stmt = (
                update(product_batch_table)
                .where(product_batch_table.c.product_batch_id == product_batch_id)
                .values(**update_values)
            )
            self.conn.execute(update_stmt)

    def soft_delete_product(self, product_id: int):
        """
        Use Case: Flags a product type as deleted so it no longer appears 
        in client menus or search profiles.
        """

        check_product_stmt = select(products_table).where(
            and_(
                products_table.c.product_id == id,
                products_table.c.is_deleted == False
            )
        )
        existing_product = self.conn.execute(check_product_stmt).fetchone()

        if existing_product is None:
            raise ProductNotFoundError("the product does not exist")

        stmt = (
            update(products_table)
            .where(products_table.c.product_id == product_id)
            .values(is_deleted=True)
        )
        self.conn.execute(stmt)

    def soft_delete_batch(self, product_batch_id: int):
        """
        Use Case: Archives an entire physical lot batch.
        """

        stmt = select(product_batch_table).where(
            product_batch_table.c.product_batch_id == product_batch_id
        )
        row = self.conn.execute(stmt).fetchone()
        if not row:
            raise ProductBatchNotFoundError(f"Batch with ID {product_batch_id} does not exist.")

        stmt = (
            update(product_batch_table)
            .where(product_batch_table.c.product_batch_id == product_batch_id)
            .values(is_deleted=True)
        )
        self.conn.execute(stmt)