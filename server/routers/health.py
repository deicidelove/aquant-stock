from fastapi import APIRouter
from pydantic import BaseModel

from aquant.data import store

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    db: bool
    latest_bar_date: str | None


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    has = store.has_table("daily_bar")
    latest = store.max_date("daily_bar") if has else None
    return HealthResponse(status="ok", db=has, latest_bar_date=latest)
