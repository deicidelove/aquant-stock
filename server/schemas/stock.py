from pydantic import BaseModel


class KlineResp(BaseModel):
    code: str
    bars: list[dict]


class ReportResp(BaseModel):
    code: str
    decision: dict
