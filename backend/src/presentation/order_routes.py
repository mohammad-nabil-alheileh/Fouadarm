from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Connection
from typing import List

from src.connection import get_db_connection
from src.infrastructure.repositories import InventoryRepository, OrderRepository
from src.application.orders_service import OrdersService
from src.schemas import PlaceOrderRequest, OrderItemRequest, EditOrderHeaderRequest, ManualPaymentRequest, UpdatePaymentRequest

from src.exceptions import(
    InvalidBatchCountError,
    InvalidPaymentAmount,
    OrderNotFound,
    OrderIsAlreadyCancelled,
    PaymentNotFound
)

router = APIRouter(prefix="/orders", tags=["Orders & Point of Sale"])

# =====================================================================
# 🛒 ORDER MANAGEMENT LIFECYCLE
# =====================================================================

@router.post("", status_code=status.HTTP_201_CREATED)
def place_order(payload: PlaceOrderRequest, conn: Connection = Depends(get_db_connection)):
    """Executes a customer checkout transaction, pulling plant batches using FIFO rules."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        payment_info = None
        if payload.payment_method and payload.payment_amount:
            payment_info = {"payment_method": payload.payment_method, "amount": payload.payment_amount}
            
        items_dict = [item.model_dump() for item in payload.items]
        order_id = service.place_order(payload.customer_name, items_dict, payment_info=payment_info)
        return {"status": "success", "order_id": order_id}
    except InvalidBatchCountError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.patch("/{order_id}/items")
def update_order_items(order_id: int, payload: List[OrderItemRequest], conn: Connection = Depends(get_db_connection)):
    """
    Atomically updates line items (adds, removes, or modifies quantities).
    Reverts old inventory stock to original batches and re-applies FIFO for new items.
    """
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        items_dict = [item.model_dump() for item in payload]
        result = service.update_order_items(order_id, items_dict)
        return {"status": "success", "details": result}
    
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    except InvalidBatchCountError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.patch("/{order_id}/header")
def edit_order_header(order_id: int, payload: EditOrderHeaderRequest, conn: Connection = Depends(get_db_connection)):
    """Updates basic order metadata like the customer's name or a manual invoice price override."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        service.edit_order_header(order_id, payload.customer_name, payload.price_override)
        return {"status": "success", "message": "Order header updated successfully."}
    
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except InvalidBatchCountError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, conn: Connection = Depends(get_db_connection)):
    """Cancels an order, rolls back physical plant counts to their specific source batches, and voids payments."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        service.cancel_order(order_id)
        return {"status": "success", "message": "Order cancelled; stock safely returned to batch pools."}
    
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except OrderIsAlreadyCancelled as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{order_id}")
def delete_order(order_id: int, conn: Connection = Depends(get_db_connection)):
    """Soft-deletes an order ledger profile so it no longer populates in active sales lookups."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        service.delete_order_record(order_id)
        return {"status": "success", "message": "Order record soft-deleted safely."}
    
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================================
# 💳 PAYMENT TRANSACTION MANAGEMENT
# =====================================================================

@router.post("/{order_id}/payments", status_code=status.HTTP_201_CREATED)
def add_payment(order_id: int, payload: ManualPaymentRequest, conn: Connection = Depends(get_db_connection)):
    """Logs an incremental down-payment or split payment settlement record against an active order invoice."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        payment_id = service.add_manual_payment(order_id, payload.payment_method, payload.amount)
        return {"status": "success", "payment_id": payment_id}
    
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/payments/{payment_id}")
def update_payment(payment_id: int, payload: UpdatePaymentRequest, conn: Connection = Depends(get_db_connection)):
    """Corrects an error on an isolated payment receipt transaction line (e.g., wrong payment method or amount)."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        service.update_payment_details(payment_id, payload.payment_method, payload.amount)
        return {"status": "success", "message": "Payment record metrics adjusted."}

    except PaymentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    except InvalidPaymentAmount as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/payments/{payment_id}")
def delete_payment(payment_id: int, conn: Connection = Depends(get_db_connection)):
    """Soft-deletes a payment entry row from the financial audit history trail."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        service.delete_payment_record(payment_id)
        return {"status": "success", "message": "Payment transaction soft-deleted."}
    except PaymentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))