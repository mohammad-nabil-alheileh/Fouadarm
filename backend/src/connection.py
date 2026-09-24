import os
import sys
from typing import Generator
from sqlalchemy import create_engine, MetaData

# 1. Grab the exact DATABASE_URL injected by Docker Compose
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Strict check: If it's missing, stop the app immediately
if not DATABASE_URL:
    print(
        "CRITICAL ERROR: DATABASE_URL environment variable is missing!", 
        file=sys.stderr
    )
    print(
        "Please ensure your .env file is configured and you are running via Docker Compose.", 
        file=sys.stderr
    )
    sys.exit(1) # Crash the application safely

# 3. Create the SQLAlchemy Engine using ONLY the environment variable
engine = create_engine(
    DATABASE_URL, 
    echo=True,
    pool_pre_ping=True  # Keeps connections alive/healthy in Docker environments
)

metadata = MetaData()

# 4. FastAPI Core Connection Dependency
def get_db_connection() -> Generator:
    """
    Context manager dependency for FastAPI endpoints.
    Automatically manages transactions (BEGIN, COMMIT, ROLLBACK).
    """
    with engine.begin() as connection:
        yield connection