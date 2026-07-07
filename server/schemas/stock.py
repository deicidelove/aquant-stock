from pydantic import BaseModel


class KlineResp(BaseModel):
    code: str
    bars: list[dict]


class ReportResp(BaseModel):
    code: str
    decision: dict


class ChartResp(BaseModel):
    code: str
    bars: list[dict]
    ma: dict
    macd: dict


class AiReportJob(BaseModel):
    job_id: str


class AiReportResp(BaseModel):
    report: dict | None
