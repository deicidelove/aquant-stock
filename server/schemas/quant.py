from pydantic import BaseModel


class BacktestIn(BaseModel):
    capital: float = 1_000_000
    weights: object = "ic"          # "ic"/"momentum" 或 {factor: weight}
    top_n: int = 5
    rebalance_every: int = 5
    start: str | None = None
    end: str | None = None
    min_history: int = 250


class FactorIcIn(BaseModel):
    factors: list[str] | None = None
    fwd: int = 5


class JobCreated(BaseModel):
    job_id: str


class JobResp(BaseModel):
    job_id: str
    kind: str
    status: str
    result: dict | None = None
    error: str | None = None


class WeightsResp(BaseModel):
    ic: dict
    momentum: dict
