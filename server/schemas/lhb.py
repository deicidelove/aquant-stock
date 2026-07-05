from pydantic import BaseModel


class LhbTodayResp(BaseModel):
    date: str | None
    rows: list[dict]


class LhbStockResp(BaseModel):
    code: str
    name: str | None
    date: str | None
    reason: str | None
    buy: list[dict]
    sell: list[dict]
