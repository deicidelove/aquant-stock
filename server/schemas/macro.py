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


class RegimeResp(BaseModel):
    state: str
    score: float | int
    suggested_position: str | None = None
    note: str | None = None
    breadth: dict | None = None
    index: dict | None = None


class IndexSeriesResp(BaseModel):
    code: str
    points: list[dict]


class AmountTrendResp(BaseModel):
    series: list[dict]


class NewsSentimentResp(BaseModel):
    score: int
    label: str
    pos: int
    neg: int
    neutral: int
    items: list[dict]


class LimitLadderResp(BaseModel):
    date: str | None
    limit_up_count: int
    seal_rate: float | None
    break_rate: float | None
    max_boards: int
    ladder: list[dict]
    by_industry: list[dict]


class NorthFlowResp(BaseModel):
    date: str | None
    rows: list[dict]


class MarginResp(BaseModel):
    date: str | None
    total_fin: float | None
    total_bal: float | None
    series: list[dict]


class BlockTradeResp(BaseModel):
    rows: list[dict]
