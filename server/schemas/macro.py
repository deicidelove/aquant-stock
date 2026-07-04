from pydantic import BaseModel


class IndicesResp(BaseModel):
    rows: list[dict]


class SentimentResp(BaseModel):
    up: int
    down: int
    limit_up: int
    limit_down: int
    amount: float
    score: float
    label: str


class MarketFundResp(BaseModel):
    today: float
    series: list[dict]


class SectorFundResp(BaseModel):
    as_of: str | None
    rows: list[dict]


class AbnormalResp(BaseModel):
    scope: str
    rows: list[dict]
