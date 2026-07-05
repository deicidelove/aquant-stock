from fastapi import APIRouter, HTTPException

from aquant import research, chart
from aquant.data import store
from server.schemas.stock import KlineResp, ReportResp, ChartResp

router = APIRouter(prefix="/api/stock", tags=["stock"])

_BAR_COLS = ["date", "open", "high", "low", "close", "volume"]


@router.get("/{code}/kline", response_model=KlineResp)
def kline(code: str, n: int = 250) -> KlineResp:
    df = store.load_daily(code)
    if df.empty:
        raise HTTPException(status_code=404, detail="no data")
    bars = df[[c for c in _BAR_COLS if c in df.columns]].tail(n).to_dict(orient="records")
    return KlineResp(code=code, bars=bars)


@router.get("/{code}/report", response_model=ReportResp)
def report(code: str) -> ReportResp:
    d = research.decision(code, offline=True)
    if not d:
        raise HTTPException(status_code=404, detail="no data")
    return ReportResp(code=code, decision=d)


@router.get("/{code}/chart", response_model=ChartResp)
def stock_chart(code: str, n: int = 250) -> ChartResp:
    return ChartResp(**chart.stock_chart(code, n=n))
