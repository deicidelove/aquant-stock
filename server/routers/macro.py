from fastapi import APIRouter

from aquant import macro
from server.schemas.macro import IndicesResp, SentimentResp, MarketFundResp, SectorFundResp, AbnormalResp

router = APIRouter(prefix="/api/cockpit", tags=["macro"])


@router.get("/indices", response_model=IndicesResp)
def indices() -> IndicesResp:
    return IndicesResp(rows=macro.indices())


@router.get("/sentiment", response_model=SentimentResp)
def sentiment() -> SentimentResp:
    return SentimentResp(**macro.sentiment())


@router.get("/market-fund", response_model=MarketFundResp)
def market_fund(days: int = 10) -> MarketFundResp:
    return MarketFundResp(**macro.market_fund_trend(days=days))


@router.get("/sector-fund", response_model=SectorFundResp)
def sector_fund() -> SectorFundResp:
    return SectorFundResp(**macro.sector_fund_rank())


@router.get("/abnormal", response_model=AbnormalResp)
def abnormal(scope: str = "stock", n: int = 20, z: float = 2.0) -> AbnormalResp:
    return AbnormalResp(**macro.abnormal_fund(scope=scope, n=n, z=z))


from server.schemas.macro import RegimeResp, IndexSeriesResp, AmountTrendResp


@router.get("/regime", response_model=RegimeResp)
def regime() -> RegimeResp:
    d = macro.regime()
    return RegimeResp(**d) if d else RegimeResp(state="", score=0)


@router.get("/index-series", response_model=IndexSeriesResp)
def index_series(code: str = "sh000300", n: int = 120) -> IndexSeriesResp:
    return IndexSeriesResp(**macro.index_series(code=code, n=n))


@router.get("/amount-trend", response_model=AmountTrendResp)
def amount_trend(days: int = 20) -> AmountTrendResp:
    return AmountTrendResp(**macro.amount_trend(days=days))
