# src/application/orders_service.py
from decimal import Decimal
from datetime import date
from typing import List, Dict, Optional
from sqlalchemy import select, update, insert

from src.domain.models import OrderAggregate
from src.infrastructure.repositories import InventoryRepository, OrderRepository
from src.infrastructure.tables import orders_table, order_items_table, product_batch_table, payment_table

from src.exceptions import(
    InsufficientStockError,
    InvalidPaymentAmount,
    OrderIsAlreadyCancelled,
    OrderNotFound,
    PaymentNotFound
)

class OrdersService:
    def __init__(self, conn, inventory_repo: InventoryRepository, order_repo: OrderRepository):
        self.conn = conn
        self.inventory_repo = inventory_repo
        self.order_repo = order_repo

    def place_order(
        self, 
        customer_name: str, 
        requested_items: List[Dict], 
        price_override: Optional[Decimal] = None,
        payment_info: Optional[Dict] = None
    ) -> int:
        """
        Use Case: Coordinates the FIFO checkout business logic workflow.
        """
        # 1. Instantiate Domain Order Aggregate Core
        order = OrderAggregate(customer_name=customer_name, manual_total_override=price_override)

        # 2. Iterate through each requested product line item
        for item in requested_items:
            product_id = item["product_id"]
            quantity_needed = item["quantity"]
            current_price = Decimal(str(item["price_per_unit"]))

            # Pull open lots from the repository, automatically sorted by date_entered (FIFO)
            fifo_batches = self.inventory_repo.get_batches_for_product_fifo(product_id)
            
            # Safety check: Ensure global physical stock across all batches can meet demand
            total_available = sum(batch.available_stock for batch in fifo_batches)
            if total_available < quantity_needed:
                raise InsufficientStockError(
                    f"Insufficient overall inventory for product ID {product_id}. "
                    f"Requested: {quantity_needed}, Total available: {total_available}."
                )

            # 3. Apply FIFO allocation loop
            for batch in fifo_batches:
                if quantity_needed <= 0:
                    break
                
                available = batch.available_stock
                if available <= 0:
                    continue  

                take_quantity = min(quantity_needed, available)
                
                # Execute allocation internal domain rules
                order.add_item(batch, take_quantity, current_price)
                quantity_needed -= take_quantity

        # 4. If payment details were supplied, register it
        if payment_info:
            order.add_payment(
                payment_method=payment_info["payment_method"],
                amount=Decimal(str(payment_info["amount"]))
            )

        # 5. Hand the finalized domain aggregate to the repository infrastructure to save
        return self.order_repo.save(order)

    def cancel_order(self, order_id: int):
        """
        Use Case: Cancels an order, rolls back physical stock allocations 
        directly to their original source batches, and soft-deletes payments.
        """
        # 1. Verify the order exists and isn't already cancelled
        order_stmt = select(orders_table).where(orders_table.c.order_id == order_id)
        order_row = self.conn.execute(order_stmt).fetchone()
        
        if not order_row:
            raise OrderNotFound(f"Order with ID {order_id} does not exist.")
        if order_row.is_cancelled:
            raise OrderIsAlreadyCancelled(f"Order with ID {order_id} is already cancelled.")

        # 2. Fetch all items associated with this specific order
        items_stmt = select(order_items_table).where(
            order_items_table.c.order_id == order_id,
            order_items_table.c.is_deleted == False
        )
        items_rows = self.conn.execute(items_stmt).fetchall()

        # 3. Rollback stock counts back into the respective product batches
        for item in items_rows:
            rollback_stock_stmt = (
                update(product_batch_table)
                .where(product_batch_table.c.product_batch_id == item.product_batch_id)
                .values(count=product_batch_table.c.count + item.quantity)
            )
            self.conn.execute(rollback_stock_stmt)

        # 4. Soft-delete the individual order line items
        delete_items_stmt = (
            update(order_items_table)
            .where(order_items_table.c.order_id == order_id)
            .values(is_deleted=True)
        )
        self.conn.execute(delete_items_stmt)

        # 5. Mark associated payment logs as refunded and soft-deleted
        update_payments_stmt = (
            update(payment_table)
            .where(payment_table.c.order_id == order_id)
            .values(is_refunded=True, is_deleted=True)
        )
        self.conn.execute(update_payments_stmt)

        # 6. Set the order header statuses to cancelled and soft-deleted
        update_order_stmt = (
            update(orders_table)
            .where(orders_table.c.order_id == order_id)
            .values(is_cancelled=True, is_deleted=True)
        )
        self.conn.execute(update_order_stmt)

    def edit_order_header(
        self, 
        order_id: int, 
        customer_name: Optional[str] = None, 
        price_override: Optional[Decimal] = None
    ):
        """
        Use Case: Edits top-level order header details like customer name 
        or applying an invoice-wide total price override manually.
        """
        # 1. Verify the order exists and is active
        order_stmt = select(orders_table).where(orders_table.c.order_id == order_id)
        order_row = self.conn.execute(order_stmt).fetchone()
        
        if not order_row:
            raise OrderNotFound(f"Order with ID {order_id} does not exist.")
        if order_row.is_deleted:
            raise OrderNotFound("Cannot edit a deleted order.")

        # 2. Dynamically map update parameters
        update_values = {}
        if customer_name is not None:
            update_values["customer_name"] = customer_name
            
        if price_override is not None:
            update_values["total_price"] = Decimal(str(price_override))

        # 3. Execute update statement if changes were requested
        if update_values:
            stmt = (
                update(orders_table)
                .where(orders_table.c.order_id == order_id)
                .values(**update_values)
            )
            self.conn.execute(stmt)

    def update_order_items(self, order_id: int, new_items: List[Dict]) -> dict:
        """
        Use Case: Updates an entire order's item list (adds, removes, or modifies quantities).
        
        Strategy:
        1. Temporarily return all current order item stocks back to their source batches.
        2. Clear the old order item entries.
        3. Run the standard FIFO allocation logic using the fresh 'new_items' list.
        4. Recalculate and update the order header total price.
        
        new_items format: [{"product_id": 1, "quantity": 30, "price_per_unit": 12.50}]
        """
        # 1. Verify the order exists and is active
        order_stmt = select(orders_table).where(orders_table.c.order_id == order_id)
        order_row = self.conn.execute(order_stmt).fetchone()
        
        if not order_row:
            raise OrderNotFound(f"Order with ID {order_id} does not exist.")
        if order_row.is_cancelled or order_row.is_deleted:
            raise OrderNotFound("Cannot update a cancelled or deleted order.")

        # 2. Fetch current items to REVERT physical stock back to batches
        current_items_stmt = select(order_items_table).where(
            order_items_table.c.order_id == order_id,
            order_items_table.c.is_deleted == False
        )
        current_items = self.conn.execute(current_items_stmt).fetchall()

        for item in current_items:
            rollback_stmt = (
                update(product_batch_table)
                .where(product_batch_table.c.product_batch_id == item.product_batch_id)
                .values(count=product_batch_table.c.count + item.quantity)
            )
            self.conn.execute(rollback_stmt)

        # 3. Soft-delete the old items from the ledger
        clear_items_stmt = (
            update(order_items_table)
            .where(order_items_table.c.order_id == order_id)
            .values(is_deleted=True)
        )
        self.conn.execute(clear_items_stmt)

        # 4. Re-allocate using FIFO with the newly requested items array
        new_total_price = Decimal("0.00")
        
        for item in new_items:
            product_id = item["product_id"]
            quantity_needed = item["quantity"]
            current_price = Decimal(str(item["price_per_unit"]))

            fifo_batches = self.inventory_repo.get_batches_for_product_fifo(product_id)
            
            total_available = sum(batch.available_stock for batch in fifo_batches)
            if total_available < quantity_needed:
                # The database transaction will automatically ROLLBACK everything if this raises
                raise InsufficientStockError(
                    f"Insufficient inventory for product ID {product_id} during update. "
                    f"Requested: {quantity_needed}, Available (after calculation): {total_available}."
                )

            for batch in fifo_batches:
                if quantity_needed <= 0:
                    break
                available = batch.available_stock
                if available <= 0:
                    continue

                take_quantity = min(quantity_needed, available)
                
                # Insert the fresh replacement item allocation row
                insert_item_stmt = insert(order_items_table).values(
                    order_id=order_id,
                    product_batch_id=batch.product_batch_id,
                    shipped=0,
                    quantity=take_quantity,
                    price_per_unit_at_that_time=current_price,
                    created_at=date.today(),
                    is_deleted=False
                )
                self.conn.execute(insert_item_stmt)

                # Deduct from batch
                deduct_stmt = (
                    update(product_batch_table)
                    .where(product_batch_table.c.product_batch_id == batch.product_batch_id)
                    .values(count=product_batch_table.c.count - take_quantity)
                )
                self.conn.execute(deduct_stmt)

                new_total_price += take_quantity * current_price
                quantity_needed -= take_quantity

        # 5. Update the order header header price calculation totals
        # If the original order didn't have a manual price override, update total_price
        if order_row.total_price == Decimal("0.00") or order_row.total_price is not None:
            update_header_stmt = (
                update(orders_table)
                .where(orders_table.c.order_id == order_id)
                .values(total_price=new_total_price)
            )
            self.conn.execute(update_header_stmt)

        return {
            "order_id": order_id,
            "status": "updated",
            "new_total_price": new_total_price
        }

    def search_orders_by_customer(self, search_term: str) -> List[dict]:
        """
        Use Case: Groups raw items back into structured orders matching the customer search term.
        """
        if not search_term.strip():
            return []

        raw_rows = self.order_repo.search_raw_orders_by_customer(search_term.strip())

        # Group multiple line-item rows back into their parent orders
        orders_map = {}
        for row in raw_rows:
            order_id = row["order_id"]
            
            if order_id not in orders_map:
                orders_map[order_id] = {
                    "order_id": order_id,
                    "customer_name": row["customer_name"],
                    "order_date": row["order_date"],
                    "total_price": row["total_price"],
                    "is_cancelled": row["is_cancelled"],
                    "items": []
                }
            
            orders_map[order_id]["items"].append({
                "product_name": row["product_name"],
                "quantity": row["quantity"],
                "price_per_unit": row["price_per_unit_at_that_time"]
            })

        return list(orders_map.values())

    def get_customer_sales_report(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
            """
            Use Case: Logic to calculate total quantities and detailed item lists per customer,
            sorted from top-buyer to bottom-buyer based on total items bought.
            """
            # 1. Fetch raw line items from the repository
            raw_items = self.order_repo.get_raw_order_line_items(start_date, end_date)
            
            # 2. Build the aggregated customer profiles
            customer_profiles = {}
            for row in raw_items:
                name = row["customer_name"]
                p_name = row["product_name"]
                qty = row["quantity"]
                
                if name not in customer_profiles:
                    customer_profiles[name] = {
                        "customer_name": name,
                        "total_items_bought": 0,
                        # Internal dictionary to easily track quantities per distinct product
                        "_items_dict": {} 
                    }
                
                # Increment total volume
                customer_profiles[name]["total_items_bought"] += qty
                
                # Group specific plant quantities under this customer
                if p_name not in customer_profiles[name]["_items_dict"]:
                    customer_profiles[name]["_items_dict"][p_name] = 0
                customer_profiles[name]["_items_dict"][p_name] += qty

            # 3. Flatten the internal items dict into a clean array for the final response
            final_report = []
            for profile in customer_profiles.values():
                formatted_items = [
                    {"product_name": name, "quantity_bought": total_qty}
                    for name, total_qty in profile["_items_dict"].items()
                ]
                
                final_report.append({
                    "customer_name": profile["customer_name"],
                    "total_items_bought": profile["total_items_bought"],
                    "items_detailed": formatted_items
                })

            # 4. Sort from top buyer to bottom buyer
            sorted_report = sorted(
                final_report,
                key=lambda customer: customer["total_items_bought"],
                reverse=True
            )

            return sorted_report


    def get_top_selling_products_report(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        """
        Use Case: Logic to aggregate total units sold and revenue per product,
        and handle sorting dynamically from top to bottom.
        """
        # 1. Get raw rows from repository
        raw_items = self.order_repo.get_raw_order_line_items(start_date, end_date)
        
        # 2. Execute business aggregation logic
        product_metrics = {}
        for row in raw_items:
            pid = row["product_id"]
            if pid not in product_metrics:
                product_metrics[pid] = {
                    "product_id": pid,
                    "product_name": row["product_name"],
                    "total_quantity_sold": 0,
                    "total_revenue": Decimal("0.00")
                }
            
            product_metrics[pid]["total_quantity_sold"] += row["quantity"]
            product_metrics[pid]["total_revenue"] += Decimal(str(row["quantity"])) * Decimal(str(row["price_per_unit_at_that_time"]))

        # 3. Sort the results from top to bottom based on total quantity sold
        sorted_report = sorted(
            product_metrics.values(), 
            key=lambda item: item["total_quantity_sold"], 
            reverse=True
        )
        
        return sorted_report

    def add_manual_payment(self, order_id: int, payment_method: str, amount: Decimal) -> int:
        """
        Use Case: Logs an additional payment or deposit against an existing order.
        """
        if amount <= 0:
            raise InvalidPaymentAmount("Payment amount must be greater than 0.")

        # 1. Verify the order exists and is active
        order_stmt = select(orders_table).where(orders_table.c.order_id == order_id)
        order_row = self.conn.execute(order_stmt).fetchone()
        
        if not order_row:
            raise OrderNotFound(f"Order with ID {order_id} does not exist.")
        if order_row.is_cancelled or order_row.is_deleted:
            raise OrderIsAlreadyCancelled("Cannot add payments to a cancelled or deleted order.")

        # 2. Record the payment transaction line directly
        stmt = insert(payment_table).values(
            order_id=order_id,
            payment_method=payment_method,
            amount=Decimal(str(amount)),
            date=date.today(),
            is_refunded=False,
            is_deleted=False
        )
        result = self.conn.execute(stmt)
        return result.inserted_primary_key[0]

    def update_payment_details(
        self, 
        payment_id: int, 
        payment_method: Optional[str] = None, 
        amount: Optional[Decimal] = None
    ):
        """
        Use Case: Corrects financial mistakes on a payment log row 
        (e.g., wrong payment method typed or incorrect amount entered).
        """
        if payment_method is None and amount is None:
            return  # Nothing to update

        # 1. Verify the payment transaction row exists
        stmt = select(payment_table).where(payment_table.c.payment_id == payment_id)
        row = self.conn.execute(stmt).fetchone()
        if not row:
            raise PaymentNotFound(f"Payment record with ID {payment_id} not found.")
        if row.is_deleted:
            raise PaymentNotFound("Cannot modify a soft-deleted payment transaction.")

        update_values = {}
        if payment_method is not None:
            update_values["payment_method"] = payment_method
        if amount is not None:
            if amount <= 0:
                raise InvalidPaymentAmount("Payment amount must be greater than 0.")
            update_values["amount"] = Decimal(str(amount))

        # 2. Persist the corrected financials to the database
        update_stmt = (
            update(payment_table)
            .where(payment_table.c.payment_id == payment_id)
            .values(**update_values)
        )
        self.conn.execute(update_stmt)

    def delete_payment_record(self, payment_id: int):
        """
        Use Case: Soft-deletes a payment record (e.g., removing a double-posted transaction entry).
        """
        # 1. Verify payment exists
        stmt = select(payment_table).where(payment_table.c.payment_id == payment_id)
        row = self.conn.execute(stmt).fetchone()
        if not row:
            raise PaymentNotFound(f"Payment record with ID {payment_id} not found.")

        # 2. Apply soft-delete flag
        update_stmt = (
            update(payment_table)
            .where(payment_table.c.payment_id == payment_id)
            .values(is_deleted=True)
        )
        self.conn.execute(update_stmt)

    def get_order_financial_summary(self, order_id: int) -> dict:
        """
        Use Case: Compares total order price against total payments made 
        to calculate outstanding balance due or deposits on hand.
        """
        # 1. Fetch order details
        order_stmt = select(orders_table).where(orders_table.c.order_id == order_id)
        order_row = self.conn.execute(order_stmt).fetchone()
        if not order_row:
            raise OrderNotFound(f"Order with ID {order_id} not found.")

        # 2. Sum up all valid active payments
        payment_stmt = select(payment_table).where(
            payment_table.c.order_id == order_id,
            payment_table.c.is_deleted == False,
            payment_table.c.is_refunded == False
        )
        payment_rows = self.conn.execute(payment_stmt).fetchall()
        total_paid = sum(row.amount for row in payment_rows)

        total_price = order_row.total_price
        remaining_balance = total_price - total_paid

        return {
            "order_id": order_id,
            "customer_name": order_row.customer_name,
            "total_price": total_price,
            "total_paid": total_paid,
            "remaining_balance": remaining_balance,
            "is_fully_paid": remaining_balance <= 0
        }

    def get_orders_report(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        """
        Use Case: Historical lookup of non-deleted orders (All time or by time period).
        """
        stmt = select(orders_table).where(orders_table.c.is_deleted == False)
        
        if start_date:
            stmt = stmt.where(orders_table.c.order_date >= start_date)
        if end_date:
            stmt = stmt.where(orders_table.c.order_date <= end_date)
            
        rows = self.conn.execute(stmt).fetchall()
        return [dict(row._mapping) for row in rows]
    
    def delete_order_record(self, order_id: int):
        """
        Use Case: Archives an order from view by soft-deleting it.
        Note: If the order is NOT cancelled first, this will hide the order 
        BUT the stock stays deducted. Usually, you want to cancel_order() 
        before deleting it to restore physical plant stock.
        """
        # 1. Verify order exists
        stmt = select(orders_table).where(orders_table.c.order_id == order_id)
        row = self.conn.execute(stmt).fetchone()
        if not row:
            raise OrderNotFound(f"Order with ID {order_id} not found.")

        # 2. Soft-delete the order header record row
        update_order = (
            update(orders_table)
            .where(orders_table.c.order_id == order_id)
            .values(is_deleted=True)
        )
        self.conn.execute(update_order)

        # 3. Soft-delete associated order items
        update_items = (
            update(order_items_table)
            .where(order_items_table.c.order_id == order_id)
            .values(is_deleted=True)
        )
        self.conn.execute(update_items)

        # 4. Soft-delete associated payments
        update_payments = (
            update(payment_table)
            .where(payment_table.c.order_id == order_id)
            .values(is_deleted=True)
        )
        self.conn.execute(update_payments)