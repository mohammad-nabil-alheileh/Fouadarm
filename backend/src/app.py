import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.application.excel_export_service import generate_monthly_excel
from src.connection import engine
from src.presentation.inventory_routes import router as inventory_router
from src.presentation.order_routes import router as order_router
from src.presentation.report_routes import router as report_router

# Without this, logger.info()/logger.exception() calls anywhere in the app
# are silently dropped — Python's logging module only prints WARNING and
# above until something configures a handler, and nothing else here did.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("fouad.scheduler")

app = FastAPI(title="Fouad ")

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# 2. Add the CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory_router)
app.include_router(order_router)
app.include_router(report_router)


def _run_scheduled_monthly_export():
    """
    Runs automatically on the 1st of each month: generates the Excel report
    for the month that just ended (never the in-progress month, since it
    wouldn't be complete yet). The manual /reports/export/excel endpoint is
    separate and defaults to the current, still-in-progress month instead —
    use that any time you want an up-to-date snapshot mid-month.
    """
    today = date.today()
    prev_month = 12 if today.month == 1 else today.month - 1
    prev_year = today.year - 1 if today.month == 1 else today.year
    try:
        with engine.begin() as conn:
            filepath = generate_monthly_excel(conn, year=prev_year, month=prev_month)
        logger.info("Scheduled monthly export generated: %s", filepath)
    except Exception:
        logger.exception("Scheduled monthly export failed for %s-%02d", prev_year, prev_month)


scheduler = AsyncIOScheduler()


@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(
        _run_scheduled_monthly_export,
        trigger=CronTrigger(day=1, hour=0, minute=10),
        id="monthly_excel_export",
        replace_existing=True,
    )
    scheduler.start()


@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown(wait=False)


@app.get("/")
def read_root():
    return {"message": "Service Engine running smoothly."}