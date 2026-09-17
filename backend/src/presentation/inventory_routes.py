from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Connection
from datetime import date
from typing import Optional

from src.connection import get_db_connection
from src.infrastructure.repositories import InventoryRepository
from src.application.inventory_service import InventoryService
from src.schemas import NewProductRequest, UpdateProductRequest, NewBatchRequest, UpdateBatchRequest, TrashFIFORequest

from src.exceptions import(
    InvalidBatchCountError,
    ProductAlreadyExistsError,
    ProductNotFoundError,
    ProductBatchNotFoundError
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# =====================================================================
# 📦 PRODUCT PROFILE ROUTES
# =====================================================================

@router.post("/products", status_code=status.HTTP_201_CREATED, response_model=NewProductRequest)
def create_product(payload: NewProductRequest, conn: Connection = Depends(get_db_connection)):
    """Registers a new core product profile in the nursery catalog."""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        product = service.create_new_product(payload.product_name, payload.unit_price)
        return {
            "product_name": product.product_name,
            "unit_price": product.unit_price
        }    
    
    except ProductAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/products", status_code=status.HTTP_200_OK)
def list_active_products(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None, 
    conn: Connection = Depends(get_db_connection)
):
    """Fetches non-deleted products, optionally filtered by creation date range (All time if empty)."""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        data = service.get_active_products_report(start_date, end_date)
        return {"status": "success", "data": data}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/products/{product_id}", status_code=status.HTTP_200_OK)
def update_product(product_id: int, payload: UpdateProductRequest, conn: Connection = Depends(get_db_connection)):
    """Modifies product metadata such as base price or catalog naming."""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        service.update_product_details(product_id, payload.product_name, payload.unit_price)
        return {"status": "success", "message": "Product updated successfully."}
    
    except ProductAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, conn: Connection = Depends(get_db_connection)):
    """Flags a catalog product as soft-deleted to hide it from new orders."""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        service.soft_delete_product(product_id)
        return {"status": "success", "message": "Product deleted successfully."}
    
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =====================================================================
# 🌿 PHYSICAL BATCH LOT ROUTES
# =====================================================================

@router.get("/batches", status_code=status.HTTP_200_OK)
def get_batches_by_product(
    product_id: int,
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None, 
    only_available: Optional[bool] = False,
    conn: Connection = Depends(get_db_connection)
):
    """fetches a product batches,  optionally filtered by creation date range (All time if empty), optionally filtered if empty stock (all if empty)"""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        data = service.get_active_batches_for_a_product(product_id, start_date, end_date, only_available)
        return {"status": "success", "data": data}
    
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/batches", status_code=status.HTTP_201_CREATED)
def add_batch(payload: NewBatchRequest, conn: Connection = Depends(get_db_connection)):
    """Logs a new physical incoming plant stock batch lot into specific row sections."""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        batch_id = service.record_new_nursery_batch(
            payload.product_id, payload.date_entered, payload.count, payload.quarter, payload.foot, payload.line
        )
        return {"status": "success", "batch_id": batch_id}
    
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    except InvalidBatchCountError as e :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/batches/{batch_id}", status_code=status.HTTP_200_OK)
def update_batch(batch_id: int, payload: UpdateBatchRequest, conn: Connection = Depends(get_db_connection)):
    """Manually overwrites or adjusts location information or counts on a single lot."""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        service.update_batch_details(batch_id, payload.count, payload.quarter, payload.foot, payload.line)
        return {"status": "success", "message": "Batch details updated successfully."}
    
    except ProductBatchNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except InvalidBatchCountError as e :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/batches/{batch_id}", status_code=status.HTTP_200_OK)
def delete_batch(batch_id: int, conn: Connection = Depends(get_db_connection)):
    """Soft-deletes a physical batch lot completely from active operations."""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        service.soft_delete_batch(batch_id)
        return {"status": "success", "message": "Batch lot soft-deleted successfully."}
    
    except ProductBatchNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# =====================================================================
# 🗑️ WASTE AND LOGISTICS
# =====================================================================

@router.post("/trash-fifo", status_code=status.HTTP_200_OK)
def trash_plants_fifo(payload: TrashFIFORequest, conn: Connection = Depends(get_db_connection)):
    """Deducts damaged or dead stock from the oldest available batches first (FIFO)."""
    service = InventoryService(conn, InventoryRepository(conn))
    try:
        service.register_trashed_plants_fifo(payload.product_id, payload.total_to_trash)
        return {"status": "success", "message": f"Successfully trashed {payload.total_to_trash} units via FIFO."}
    
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    except InvalidBatchCountError as e :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))