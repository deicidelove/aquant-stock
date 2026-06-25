from fastapi import APIRouter

from aquant import research
from aquant.track import evaluate
from server.schemas.assist import BriefingResp, ScorecardResp

router = APIRouter(prefix="/api/assist", tags=["assist"])


@router.get("/briefing", response_model=BriefingResp)
def briefing(top: int = 12) -> BriefingResp:
    df = research.briefing(top=top, offline=True)
    return BriefingResp(rows=df.to_dict(orient="records") if not df.empty else [])


@router.get("/scorecard", response_model=ScorecardResp)
def scorecard() -> ScorecardResp:
    df = evaluate.forward_returns()
    if df.empty:
        return ScorecardResp(as_of=None, rows=[])
    as_of = str(df["as_of"].iloc[0]) if "as_of" in df.columns else None
    return ScorecardResp(as_of=as_of, rows=df.to_dict(orient="records"))
