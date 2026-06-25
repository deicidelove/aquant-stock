from pydantic import BaseModel


class BriefingResp(BaseModel):
    rows: list[dict]


class ScorecardResp(BaseModel):
    as_of: str | None
    rows: list[dict]
