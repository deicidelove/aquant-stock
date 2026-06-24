from fastapi import APIRouter

from aquant import market, sector
from aquant.data import store
from server.schemas.cockpit import OverviewResp, SectorsResp

router = APIRouter(prefix="/api/cockpit", tags=["cockpit"])


@router.get("/overview", response_model=OverviewResp)
def overview() -> OverviewResp:
    return OverviewResp(
        breadth=market.breadth(),
        regime=market.regime(),
        index=market.index_trend(),
    )


@router.get("/sectors", response_model=SectorsResp)
def sectors() -> SectorsResp:
    rows, as_of = [], None
    if store.has_table("sector_snapshot"):
        df = store.query(
            "SELECT * FROM sector_snapshot "
            "WHERE ts = (SELECT max(ts) FROM sector_snapshot) "
            "ORDER BY pct_chg DESC")
        if not df.empty:
            as_of = str(df["ts"].iloc[0])
            rows = df.drop(columns=["ts"]).to_dict(orient="records")
    return SectorsResp(as_of=as_of, rows=rows, rotation=sector.rotation())
