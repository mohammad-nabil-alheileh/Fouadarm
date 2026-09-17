from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Connection
from typing import Optional
from datetime import date

from src.connection import get_db_connection
from src.infrastructure.repositories import InventoryRepository, OrderRepository
from src.application.inventory_service import InventoryService
from src.application.orders_service import OrdersService

from src.exceptions import(
    InsufficientStockError,
    InvalidBatchCountError,
    InvalidPaymentAmount,
    OrderNotFound,
    OrderIsAlreadyCancelled,
    PaymentNotFound
)
router = APIRouter(prefix="/reports", tags=["Business Intelligence & Reports"])

# =====================================================================
# 📊 INVENTORY LOOKUPS
# =====================================================================

@router.get("/batches", status_code=status.HTTP_200_OK)
def get_batches_report(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None, 
    only_available: bool = False,
    conn: Connection = Depends(get_db_connection)
):
    """
    Fetches an operational view of active plant batch lots.
    Can be filtered by date ranges or restricted to show only lots with stock remaining.
    """
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        data = service.get_active_batches_report(start_date, end_date, only_available)
        return {"status": "success", "data": data}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =====================================================================
# 💳 FINANCIAL AUDITING
# =====================================================================

@router.get("/orders/{order_id}/financial-summary", status_code=status.HTTP_200_OK)
def get_order_summary(order_id: int, conn: Connection = Depends(get_db_connection)):
    """
    Calculates the financial standing of a specific invoice.
    Aggregates all non-deleted item costs against total processed down-payments to find the balance due.
    """
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        summary = service.get_order_financial_summary(order_id)
        return {"status": "success", "summary": summary}
    
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================================
# 📈 SALES & CUSTOMER INTELLIGENCE
# =====================================================================

@router.get("/customers", status_code=status.HTTP_200_OK)
def get_customer_sales_report(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None, 
    conn: Connection = Depends(get_db_connection)
):
    """
    Brings each customer, their total item volume bought, and a detailed list of what they bought.
    Sorted from top-spending customer down to the bottom, optionally filtered across a specific time period.
    """
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        data = service.get_customer_sales_report(start_date, end_date)
        return {"status": "success", "data": data}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/products/ranking", status_code=status.HTTP_200_OK)
def get_product_sales_ranking(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None, 
    conn: Connection = Depends(get_db_connection)
):
    """
    Brings every product in the system along with its accumulated total units sold and revenue generated.
    The response is rank-ordered automatically from top-selling items to bottom-selling items.
    """
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        data = service.get_top_selling_products_report(start_date, end_date)
        return {"status": "success", "data": data}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/orders/search", status_code=status.HTTP_200_OK)
def search_orders(
    customer_name: Optional[str] = None,
    product_name: Optional[str] = None,
    payment_method: Optional[str] = None,
    payment_status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn: Connection = Depends(get_db_connection),
):
    """
    Flexible order lookup: partial, case-insensitive matches on customer name
    and/or product name, an optional payment method filter, an optional
    payment_status filter ("paid" or "unpaid"), and an optional order-date
    range. All filters are optional and combine with AND.
    """
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        data = service.search_orders(
            customer_name=customer_name,
            product_name=product_name,
            payment_method=payment_method,
            payment_status=payment_status,
            start_date=start_date,
            end_date=end_date,
        )
        return {"status": "success", "data": data}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))