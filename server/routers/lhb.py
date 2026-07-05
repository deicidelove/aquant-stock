from fastapi import APIRouter

from aquant import lhb
from server.schemas.lhb import LhbTodayResp, LhbStockResp

router = APIRouter(prefix="/api/lhb", tags=["lhb"])


@router.get("/today", response_model=LhbTodayResp)
def get_today(limit: int = 50) -> LhbTodayResp:
    r = lhb.lhb_today(limit=limit)
    return LhbTodayResp(**r)


@router.get("/stock/{code}", response_model=LhbStockResp)
def get_stock(code: str, date: str | None = None) -> LhbStockResp:
    r = lhb.lhb_stock(code, date=date)
    return LhbStockResp(**r)
