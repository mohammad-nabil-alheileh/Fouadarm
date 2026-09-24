# src/application/excel_export_service.py
"""
Builds a monthly Excel workbook (Products, Batches, Orders, Payments,
Customers) from the database, scoped to a single calendar month.

Products is a current-catalog snapshot — products aren't a time-scoped
concept, so it always reflects "right now" regardless of which month the
rest of the report covers. Batches, Orders, Payments, and Customers are all
filtered to the given month only (never all-time).
"""
import calendar
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from sqlalchemy.engine import Connection

from src.infrastructure.repositories import InventoryRepository, OrderRepository
from src.application.orders_service import OrdersService

# backend/src/application/excel_export_service.py -> parents[2] == backend/
# (== /app inside the container, which is bind-mounted to ./backend on the host)
EXPORTS_DIR = Path(__file__).resolve().parents[2] / "exports"


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = date(year, month, last_day)
    return start, end


def _num(value):
    """openpyxl can't write Decimal directly — convert to float for storage."""
    return float(value) if isinstance(value, Decimal) else value


def _write_sheet(wb: Workbook, title: str, headers: list, rows: list):
    ws = wb.create_sheet(title=title)
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append(row)

    if not rows:
        for i, header in enumerate(headers, start=1):
            ws.column_dimensions[get_column_letter(i)].width = max(len(str(header)) + 2, 12)
        return

    for i, header in enumerate(headers, start=1):
        col_values = [str(header)] + [str(r[i - 1]) for r in rows]
        width = min(max(len(v) for v in col_values) + 2, 40)
        ws.column_dimensions[get_column_letter(i)].width = width


def generate_monthly_excel(
    conn: Connection,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> str:
    """
    Generates the workbook for the given calendar month (defaults to the
    current month if not given), saves it to the exports folder, and
    returns the absolute file path. Always overwrites any existing file for
    the same month, so re-running it reflects the latest data.
    """
    today = date.today()
    year = year or today.year
    month = month or today.month
    start_date, end_date = _month_bounds(year, month)

    inventory_repo = InventoryRepository(conn)
    order_repo = OrderRepository(conn)
    orders_service = OrdersService(conn, inventory_repo, order_repo)

    products = inventory_repo.get_all_active_products()
    batches = inventory_repo.get_all_active_batches(start_date=start_date, end_date=end_date)
    orders = orders_service.get_grouped_orders(start_date=start_date, end_date=end_date)
    payments = order_repo.get_active_payments(start_date=start_date, end_date=end_date)

    orders_by_id = {o["order_id"]: o for o in orders}
    for p in payments:
        order = orders_by_id.get(p["order_id"])
        p["customer_name"] = order["customer_name"] if order else ""

    customers = {}
    for o in orders:
        c = customers.setdefault(o["customer_name"], {
            "customer_name": o["customer_name"],
            "order_count": 0,
            "total_spent": Decimal("0.00"),
            "total_paid": Decimal("0.00"),
        })
        c["order_count"] += 1
        c["total_spent"] += o["total_amount"] or Decimal("0.00")
        c["total_paid"] += o["total_paid"] or Decimal("0.00")
    customer_rows = sorted(customers.values(), key=lambda c: c["total_spent"], reverse=True)

    wb = Workbook()
    wb.remove(wb.active)

    _write_sheet(
        wb, "Products",
        headers=["Product ID", "Product Name", "Unit Price", "Quantity In Stock"],
        rows=[[p["id"], p["product_name"], _num(p["unit_price"]), p["quantity"]] for p in products],
    )

    _write_sheet(
        wb, "Batches",
        headers=["Batch ID", "Product Name", "Quarter", "Foot", "Line", "Count", "Trashed", "Remaining", "Date Entered"],
        rows=[
            [b["product_batch_id"], b["product_name"], b["quarter"], b["foot"], b["line"],
             b["count"], b["trashed"], b["count"] - b["trashed"], b["date_entered"]]
            for b in batches
        ],
    )

    order_rows = []
    for o in orders:
        items_str = ", ".join(f"{it['product_name']} x{it['quantity']}" for it in o["items"])
        order_rows.append([
            o["order_id"], o["customer_name"], o["order_date"], items_str,
            _num(o["total_amount"]), _num(o["total_paid"]), _num(o["remaining_balance"]),
            "Yes" if o["is_fully_paid"] else "No",
        ])
    _write_sheet(
        wb, "Orders",
        headers=["Order ID", "Customer", "Date", "Items", "Total", "Paid", "Remaining", "Fully Paid"],
        rows=order_rows,
    )

    _write_sheet(
        wb, "Payments",
        headers=["Order ID", "Customer", "Payment Method", "Amount", "Date"],
        rows=[[p["order_id"], p["customer_name"], p["payment_method"], _num(p["amount"]), p["date"]] for p in payments],
    )

    _write_sheet(
        wb, "Customers",
        headers=["Customer", "Orders", "Total Spent", "Total Paid"],
        rows=[[c["customer_name"], c["order_count"], _num(c["total_spent"]), _num(c["total_paid"])] for c in customer_rows],
    )

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"fouad_farm_report_{year}-{month:02d}.xlsx"
    filepath = EXPORTS_DIR / filename
    wb.save(filepath)
    return str(filepath)
