from datetime import UTC, datetime
from fastapi import APIRouter
from sqlalchemy import text
from app.db import engine

router = APIRouter(tags=["System"])


@router.get("/health", summary="Check API and database health")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}
