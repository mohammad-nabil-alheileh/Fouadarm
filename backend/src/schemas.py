from datetime import date

from pydantic import BaseModel
from decimal import Decimal
from typing import Optional, List

class NewProductRequest(BaseModel):
    product_name: str
    unit_price: Decimal

class UpdateProductRequest(BaseModel):
    product_name: Optional[str] = None
    unit_price: Optional[Decimal] = None

class NewBatchRequest(BaseModel):
    product_id: int
    date_entered: date
    count: int
    quarter: str
    foot: str
    line: str

class UpdateBatchRequest(BaseModel):
    count: Optional[int] = None
    quarter: Optional[str] = None
    foot: Optional[str] = None
    line: Optional[str] = None

class TrashFIFORequest(BaseModel):
    product_id: int
    total_to_trash: int

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: Decimal

class PlaceOrderRequest(BaseModel):
    customer_name: str
    items: List[OrderItemRequest]
    payment_method: Optional[str] = None
    payment_amount: Optional[Decimal] = None

class EditOrderHeaderRequest(BaseModel):
    customer_name: Optional[str] = None
    price_override: Optional[Decimal] = None

class ManualPaymentRequest(BaseModel):
    payment_method: str
    amount: Decimal

class UpdatePaymentRequest(BaseModel):
    payment_method: Optional[str] = None
    amount: Optional[Decimal] = None