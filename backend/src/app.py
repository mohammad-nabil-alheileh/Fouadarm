from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.presentation.inventory_routes import router as inventory_router
from src.presentation.order_routes import router as order_router
from src.presentation.report_routes import router as report_router

app = FastAPI(title="Fouad ")

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# 2. Add the CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Allows requests from these domains
    allow_credentials=True,
    allow_methods=["*"],              # Allows all HTTP methods (GET, POST, PATCH, DELETE, etc.)
    allow_headers=["*"],              # Allows all headers
)

app.include_router(inventory_router)
app.include_router(order_router)
app.include_router(report_router)

@app.get("/")
def read_root():
    return {"message": "Service Engine running smoothly."}