from fastapi import APIRouter

from aquant.data import store

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict:
    has = store.has_table("daily_bar")
    latest = store.max_date("daily_bar") if has else None
    return {"status": "ok", "db": has, "latest_bar_date": latest}
