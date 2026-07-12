# src/presentation/report_routes.py
from src.exceptions import OrderNotFound
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Connection
from typing import Optional
from datetime import date

from src.connection import get_db_connection
from src.infrastructure.repositories import InventoryRepository, OrderRepository
from src.application.inventory_service import InventoryService
from src.application.orders_service import OrdersService

router = APIRouter(prefix="/reports", tags=["Business Intelligence & Reports"])

# =====================================================================
# 📊 INVENTORY LOOKUPS
# =====================================================================

@router.get("/batches")
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

@router.get("/orders/{order_id}/financial-summary")
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

@router.get("/customers")
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

@router.get("/products/ranking")
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

@router.get("/orders/search")
def search_orders_by_customer(customer_name: str, conn: Connection = Depends(get_db_connection)):
    """
    Searches and structures historic orders using a partial, case-insensitive customer name look-up string.
    e.g., searching 'jam' will gather all orders matching 'Jamal' with item breakdowns.
    """
    service = OrdersService(conn, InventoryRepository(conn), OrderRepository(conn))
    try:
        data = service.search_orders_by_customer(customer_name)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))