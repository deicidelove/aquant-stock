from fastapi import APIRouter

from aquant import market
from server.schemas.cockpit import OverviewResp

router = APIRouter(prefix="/api/cockpit", tags=["cockpit"])


@router.get("/overview", response_model=OverviewResp)
def overview() -> OverviewResp:
    return OverviewResp(
        breadth=market.breadth(),
        regime=market.regime(),
        index=market.index_trend(),
    )
