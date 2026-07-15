from datetime import date
from decimal import Decimal
from typing import List, Optional
from src.exceptions import InsufficientStockError, BatchAlreadyAssignedToOrderError,InvalidBatchCountError, InvalidPaymentAmount, OrderNotFound, OrderIsAlreadyCancelled, PaymentNotFound

class ProductDomain:
    def __init__(self, product_id: int, product_name: str, unit_price: Decimal, is_deleted: bool = False):
        self.product_id = product_id
        self.product_name = product_name
        self.unit_price = unit_price
        self.is_deleted = is_deleted


class ProductBatchDomain:
    def __init__(self, product_batch_id: int, product_id: int, date_entered: date, count: int, trashed: int, quarter: str, foot: str, line: str, is_deleted: bool = False):
        self.product_batch_id = product_batch_id
        self.product_id = product_id
        self.date_entered = date_entered
        self.count = count          
        self.trashed = trashed      
        self.allocated = 0
        self.quarter = quarter
        self.foot = foot
        self.line = line
        self.is_deleted = is_deleted

    @property
    def available_stock(self) -> int:
        """Business Logic: Calculate actual sellable inventory left in this batch"""
        return self.count - self.trashed - self.allocated

    def allocate(self, quantity: int):
        """Deduct stock from this specific lot"""
        if quantity > self.available_stock:
            raise InsufficientStockError(f"Cannot allocate {quantity}. Only {self.available_stock} items left in batch {self.product_batch_id}.")
        self.allocated += quantity

    def mark_as_deleted(self):
            """Domain Action: Ensures we can't allocate from a dead batch"""
            if self.allocated > 0:
                raise BatchAlreadyAssignedToOrderError("Cannot delete a batch that already has items allocated to orders.")
            self.is_deleted = True


class PaymentDomain:
    def __init__(self, payment_id: int, order_id: int, amount: Decimal, payment_date: date, payment_method: str, is_deleted: bool = False):
        self.payment_id = payment_id
        self.order_id = order_id
        self.payment_method = payment_method
        self.amount = amount
        self.payment_date = payment_date
        self.is_refunded = False
        self.is_deleted = is_deleted


class OrderItemDomain:
    def __init__(self, product_id: int, product_batch_id: int, quantity: int, price_per_unit: Decimal, is_deleted: bool = False):
        self.product_id = product_id
        self.product_batch_id = product_batch_id
        self.quantity = quantity
        self.price_per_unit = price_per_unit
        self.is_deleted = is_deleted


class OrderAggregate:
    def __init__(self, customer_name: str, order_date: date, manual_total_override: Optional[Decimal] = None):
        if manual_total_override is not None and manual_total_override < 0:
            raise ValueError("manual_total_override cannot be negative.")

        self.customer_name = customer_name
        self.order_date = order_date
        self.items: List[OrderItemDomain] = []
        self.payments: List[PaymentDomain] = []
        self.is_cancelled = False
        self.is_deleted = False
        self.order_id = None
        self.manual_total_override = manual_total_override

    def add_item(self, batch: ProductBatchDomain, quantity: int, price_per_unit: Decimal):
        """
        Business Rule: Verify stock availability inside the domain 
        before adding it to the order.
        """
        if self.is_cancelled:
            raise OrderIsAlreadyCancelled("Cannot add items to a cancelled order.")
        
        # 1. Enforce inventory check
        batch.allocate(quantity)
        
        # 2. Add item to order list
        item = OrderItemDomain(
            product_id=batch.product_id,
            product_batch_id=batch.product_batch_id,
            quantity=quantity,
            price_per_unit=price_per_unit
        )
        self.items.append(item)

    def add_payment(self, payment_method: str, amount: Decimal, payment_id: int, payment_date: date):
            """Business Rule: Record a payment transaction against this order lifecycle"""
            if self.is_cancelled:
                raise OrderIsAlreadyCancelled("Cannot process payment for a cancelled order.")
            
            # We don't have an order_id yet when creating a brand new order, 
            # the repository will assign it during save.
            payment = PaymentDomain(
                payment_id=payment_id,
                order_id=0, 
                payment_method=payment_method,
                amount=amount,
                payment_date=payment_date
            )
            self.payments.append(payment)

    @property
    def total_price(self) -> Decimal:
        """
        Business Rule: Use manual user override if provided; 
        otherwise, calculate dynamic sum.
        """
        if self.manual_total_override is not None:
            return self.manual_total_override
        return sum(
            (item.quantity * item.price_per_unit for item in self.items),
            Decimal("0"),
        )