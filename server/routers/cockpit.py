from fastapi import APIRouter

from aquant import market, sector, research
from aquant.data import store
from server.refresh import scores
from server.schemas.cockpit import OverviewResp, SectorsResp, TopScoresResp, PicksResp

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


@router.get("/top-scores", response_model=TopScoresResp)
def top_scores(top: int = 20) -> TopScoresResp:
    df = scores.read_top_scores(top=top)
    as_of = str(df["as_of"].iloc[0]) if not df.empty else None
    rows = df.drop(columns=["as_of"]).to_dict(orient="records") if not df.empty else []
    return TopScoresResp(as_of=as_of, rows=rows)


@router.get("/picks", response_model=PicksResp)
def picks(top: int = 3) -> PicksResp:
    df = research.daily_picks(top=top)
    rows = df.to_dict(orient="records") if not df.empty else []
    return PicksResp(rows=rows)
