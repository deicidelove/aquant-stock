from pydantic import BaseModel


class OverviewResp(BaseModel):
    breadth: dict
    regime: dict
    index: dict
