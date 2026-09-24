from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import insert, select, update

from src.domain.models import OrderAggregate
from src.exceptions import (
    InsufficientStockError,
    InvalidPaymentAmount,
    OrderIsAlreadyCancelled,
    OrderNotFound,
    PaymentNotFound,
)
from src.infrastructure.repositories import InventoryRepository, OrderRepository
from src.infrastructure.tables import (
    order_items_table,
    orders_table,
    payment_table,
    product_batch_table,
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
        order_date: Optional[date] = None,
        price_override: Optional[Decimal] = None,
        payment_info: Optional[Dict] = None
    ) -> OrderAggregate:
        """
        Use Case: Coordinates the FIFO checkout business logic workflow.
        """
        # 1. Instantiate Domain Order Aggregate Core
        try:
            order = OrderAggregate(
                customer_name=customer_name,
                manual_total_override=price_override,
                order_date=order_date or date.today()
            )
        except ValueError as e:
            raise InvalidPaymentAmount(str(e))

        # 2. Iterate through each requested product line item
        for item in requested_items:
            product_id = item["product_id"]
            quantity_needed = item["quantity"]
            current_price = None

            if hasattr(self.inventory_repo, "get_product_unit_price"):
                current_price = self.inventory_repo.get_product_unit_price(product_id)

            if current_price is None:
                current_price = Decimal(str(item.get("price_per_unit") or item.get("unit_price") or 0))

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
                amount=Decimal(str(payment_info["amount"])),
                payment_date=date.today(),
            )

        new_order_id = self.order_repo.save(order)

        # 5. Hand the finalized domain aggregate to the repository infrastructure to save
        order.order_id = new_order_id
        return order

    def get_grouped_orders(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[dict]:
        """
        Groups raw line items back into structured parent orders with nested items,
        ensuring different orders by the same customer on the same day are not merged.
        """
        # 1. Fetch flat rows from repository
        flat_rows = self.order_repo.get_raw_order_line_items(start_date, end_date)

        # 2. Group items by a truly unique key: order_id
        # (We fall back to customer+date only if your raw repository lacks order_id)
        grouped_data = defaultdict(lambda: {
            "order_id": None,
            "customer_name": "",
            "order_date": None,
            "items": [],
            "total_amount": Decimal("0.00"),
            "payment_method": None
        })

        for row in flat_rows:
            # Check if your raw query has order_id; if not, add it to your SELECT query
            # or fall back to a safe composite key that includes product or sequence IDs.
            order_id = row.get("order_id")
            key = order_id if order_id is not None else (row["customer_name"], row["order_date"])

            # Populate outer metadata once per unique order
            if not grouped_data[key]["customer_name"]:
                grouped_data[key]["order_id"] = order_id
                grouped_data[key]["customer_name"] = row["customer_name"]
                grouped_data[key]["order_date"] = row["order_date"]
                # Use the order's actual stored total (respects a manual price
                # override); it must NOT be recomputed from line items, since
                # that silently discards any override applied at checkout.
                grouped_data[key]["total_amount"] = row.get("total_price") or Decimal("0.00")

            # Append to the nested items list
            item_price = row["price_per_unit_at_that_time"]
            quantity = row["quantity"]

            grouped_data[key]["items"].append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "quantity": quantity,
                "price_per_unit_at_that_time": item_price
            })

        # 3. Attach payment totals (amount paid, remaining balance, methods used)
        payment_rows = self.order_repo.get_active_payments()
        paid_by_order = defaultdict(lambda: Decimal("0.00"))
        methods_by_order = defaultdict(set)
        for p in payment_rows:
            paid_by_order[p["order_id"]] += p["amount"]
            methods_by_order[p["order_id"]].add(p["payment_method"])

        orders = list(grouped_data.values())
        for order in orders:
            oid = order["order_id"]
            total_paid = paid_by_order.get(oid, Decimal("0.00"))
            remaining = order["total_amount"] - total_paid
            order["total_paid"] = total_paid
            order["remaining_balance"] = remaining
            order["is_fully_paid"] = remaining <= 0
            order["payment_methods"] = sorted(methods_by_order.get(oid, set()))
            order["payment_method"] = order["payment_methods"][0] if order["payment_methods"] else None

        return orders

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
        4. Recalculate and update the order header total price — unless a manual
           price override is currently in effect, in which case it's left alone.

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

        # Detect whether a manual price override is currently in effect. There's
        # no separate column recording "this total was manually overridden" —
        # total_price just holds whatever the final number is. So we check: does
        # the stored total already match what these (about-to-be-replaced) items
        # compute to? If it doesn't, someone applied an override via
        # edit_order_header, and this update must not silently discard it.
        old_computed_total = sum(
            (Decimal(str(item.quantity)) * Decimal(str(item.price_per_unit_at_that_time)) for item in current_items),
            Decimal("0.00"),
        )
        has_manual_override = Decimal(str(order_row.total_price)) != old_computed_total

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
            current_price = None

            if hasattr(self.inventory_repo, "get_product_unit_price"):
                current_price = self.inventory_repo.get_product_unit_price(product_id)

            if current_price is None:
                current_price = Decimal(str(item.get("price_per_unit") or item.get("unit_price") or 0))

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

        # 5. Update the order header's total price — but only if there wasn't a
        # manual override in effect before this edit. If there was, leave the
        # stored total alone (call edit_order_header separately to change or
        # clear it); otherwise, adopt the freshly computed FIFO total.
        if not has_manual_override:
            update_header_stmt = (
                update(orders_table)
                .where(orders_table.c.order_id == order_id)
                .values(total_price=new_total_price)
            )
            self.conn.execute(update_header_stmt)

        final_total_price = order_row.total_price if has_manual_override else new_total_price

        return {
            "order_id": order_id,
            "status": "updated",
            "new_total_price": final_total_price
        }

    def search_orders(
        self,
        customer_name: Optional[str] = None,
        product_name: Optional[str] = None,
        payment_method: Optional[str] = None,
        payment_status: Optional[str] = None,  # "paid" | "unpaid" | None
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """
        Use Case: Flexible order lookup across customer name, product name,
        payment method used, paid/unpaid status, and a date range. Reuses
        get_grouped_orders so results carry the same accurate totals and
        payment info shown everywhere else (respecting price overrides).
        """
        orders = self.get_grouped_orders(start_date=start_date, end_date=end_date)

        def matches(order: dict) -> bool:
            if customer_name and customer_name.strip():
                if customer_name.strip().lower() not in order["customer_name"].lower():
                    return False
            if product_name and product_name.strip():
                needle = product_name.strip().lower()
                if not any(needle in item["product_name"].lower() for item in order["items"]):
                    return False
            if payment_method and payment_method.strip():
                needle = payment_method.strip().lower()
                if not any(needle in m.lower() for m in order["payment_methods"]):
                    return False
            if payment_status == "paid" and not order["is_fully_paid"]:
                return False
            if payment_status == "unpaid" and order["is_fully_paid"]:
                return False
            return True

        return [o for o in orders if matches(o)]

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
        if not row or row.is_deleted or row.is_refunded:
            raise PaymentNotFound(f"Payment record with ID {payment_id} not found.")

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
        if not row or row.is_deleted:
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
        if not row or row.is_deleted:
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