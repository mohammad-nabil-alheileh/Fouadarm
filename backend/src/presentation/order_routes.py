from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Connection
from typing import List, Optional

from src.connection import get_db_connection
from src.infrastructure.repositories import InventoryRepository, OrderRepository
from src.application.orders_service import OrdersService
from src.schemas import OrderResponse, PlaceOrderRequest, OrderItemRequest, EditOrderHeaderRequest, ManualPaymentRequest, UpdatePaymentRequest

from src.exceptions import(
    InsufficientStockError,
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

@router.get("", status_code=status.HTTP_200_OK)
def get_all_orders(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None, 
    conn: Connection = Depends(get_db_connection)
    ):
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        data = service.get_grouped_orders(start_date=start_date, end_date=end_date)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
def place_order(payload: PlaceOrderRequest, conn: Connection = Depends(get_db_connection)):
    """Executes a customer checkout transaction, pulling plant batches using FIFO rules."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        # 1. Parse optional payment info
        payment_info = None
        if payload.payment_method and payload.payment_amount:
            payment_info = {
                "payment_method": payload.payment_method, 
                "amount": payload.payment_amount
            }
            
        # 2. Extract requested items to pass to service layer
        items_dict = [item.model_dump() for item in payload.items]
        override_total = payload.price_override
        
        # 3. Call service (it now returns the completed OrderAggregate object)
        order = service.place_order(
            payload.customer_name,
            items_dict,
            order_date=payload.order_date,
            price_override=override_total,
            payment_info=payment_info
        )
        
        # 4. Serialize internal domain line items into list of dicts matching output schema
        serialized_items = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price_per_unit": item.price_per_unit
            }
            for item in order.items
        ]

        # 5. Return the full dictionary structure matching OrderResponse
        payment_method = None
        if payload.payment_method:
            payment_method = payload.payment_method
        elif order.payments:
            payment_method = order.payments[0].payment_method

        return {
            "customer_name": order.customer_name,
            "order_date": order.order_date or date.today(),
            "items": serialized_items,
            "total_amount": order.total_price,
            "payment_method": payment_method
        }
    
    except InvalidBatchCountError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Catch any inventory stock out issues
    except InsufficientStockError as e:
        raise HTTPException(status_code=409, detail=str(e))
    
    except InvalidPaymentAmount as e:
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{order_id}/items" , status_code=status.HTTP_200_OK)
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


@router.patch("/{order_id}/header",status_code=status.HTTP_200_OK)
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


@router.post("/{order_id}/cancel", status_code=status.HTTP_200_OK)
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


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
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


@router.patch("/payments/{payment_id}", status_code=status.HTTP_200_OK)
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


@router.delete("/payments/{payment_id}", status_code=status.HTTP_200_OK)
def delete_payment(payment_id: int, conn: Connection = Depends(get_db_connection)):
    """Soft-deletes a payment entry row from the financial audit history trail."""
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        service.delete_payment_record(payment_id)
        return {"status": "success", "message": "Payment transaction deleted."}
    
    except PaymentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))