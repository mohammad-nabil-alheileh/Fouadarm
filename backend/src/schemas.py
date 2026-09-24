from datetime import date

from pydantic import BaseModel, model_validator
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
    unit_price: Optional[Decimal] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_unit_price(cls, values):
        if isinstance(values, dict):
            normalized = dict(values)
            if normalized.get("price_per_unit") is None and normalized.get("unit_price") is not None:
                normalized["price_per_unit"] = normalized["unit_price"]
            return normalized
        return values

class PlaceOrderRequest(BaseModel):
    customer_name: str
    order_date: Optional[date] = None
    items: List[OrderItemRequest]
    payment_method: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    price_override: Optional[Decimal] = None

class OrderResponse(BaseModel):
    customer_name: str
    order_date: date
    items: List[OrderItemRequest]
    total_amount: Decimal
    payment_method: Optional[str] = None

class EditOrderHeaderRequest(BaseModel):
    customer_name: Optional[str] = None
    price_override: Optional[Decimal] = None

class ManualPaymentRequest(BaseModel):
    payment_method: str
    amount: Decimal

class UpdatePaymentRequest(BaseModel):
    payment_method: Optional[str] = None
    amount: Optional[Decimal] = None