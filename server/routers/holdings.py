from fastapi import APIRouter

from aquant.portfolio import holdings as h
from server.schemas.holdings import TradeIn, TradeCreated, TradesResp, HoldingsResp, PnlResp, Deleted

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.post("/trade", response_model=TradeCreated)
def add_trade(t: TradeIn) -> TradeCreated:
    tid = h.record_trade(t.date, t.code, t.side, t.shares, t.price, t.note)
    return TradeCreated(tid=tid)


@router.get("/trades", response_model=TradesResp)
def trades() -> TradesResp:
    df = h.list_trades()
    return TradesResp(rows=df.to_dict(orient="records") if not df.empty else [])


@router.delete("/trade/{tid}", response_model=Deleted)
def remove_trade(tid: int) -> Deleted:
    return Deleted(deleted=h.delete_trade(tid))


@router.get("", response_model=HoldingsResp)
def current() -> HoldingsResp:
    return HoldingsResp(rows=h.holdings_view())


@router.get("/pnl", response_model=PnlResp)
def pnl() -> PnlResp:
    return PnlResp(**h.pnl_summary())
