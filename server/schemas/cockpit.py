from pydantic import BaseModel


class OverviewResp(BaseModel):
    breadth: dict
    regime: dict
    index: dict


class SectorsResp(BaseModel):
    as_of: str | None
    rows: list[dict]
    rotation: dict
