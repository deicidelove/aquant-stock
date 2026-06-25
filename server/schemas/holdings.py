from pydantic import BaseModel


class TradeIn(BaseModel):
    date: str
    code: str
    side: str
    shares: float
    price: float
    note: str = ""


class TradeCreated(BaseModel):
    tid: int


class TradesResp(BaseModel):
    rows: list[dict]


class HoldingsResp(BaseModel):
    rows: list[dict]


class PnlResp(BaseModel):
    realized: float
    unrealized: float
    total: float


class Deleted(BaseModel):
    deleted: int
