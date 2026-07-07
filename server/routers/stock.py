from datetime import date

from fastapi import APIRouter, HTTPException

from aquant import research, chart, analysts
from aquant.data import store, research_cache
from aquant.quant import jobs
from server.schemas.stock import KlineResp, ReportResp, ChartResp, AiReportJob, AiReportResp

router = APIRouter(prefix="/api/stock", tags=["stock"])

_BAR_COLS = ["date", "open", "high", "low", "close", "volume"]


def _ai_report_runner(params: dict) -> dict:
    """异步任务：实网生成多智能体投研报告并缓存。"""
    code = params["code"]
    rep = analysts.ai_research(code, offline=False)
    as_of = rep.get("as_of") or date.today().isoformat()
    research_cache.save_report(code, as_of, rep)
    return rep


jobs.register("ai_research", _ai_report_runner)


@router.get("/{code}/kline", response_model=KlineResp)
def kline(code: str, n: int = 250) -> KlineResp:
    df = store.load_daily(code)
    if df.empty:
        raise HTTPException(status_code=404, detail="no data")
    bars = df[[c for c in _BAR_COLS if c in df.columns]].tail(n).to_dict(orient="records")
    return KlineResp(code=code, bars=bars)


@router.get("/{code}/report", response_model=ReportResp)
def report(code: str) -> ReportResp:
    d = research.decision(code, offline=True)
    if not d:
        raise HTTPException(status_code=404, detail="no data")
    return ReportResp(code=code, decision=d)


@router.get("/{code}/chart", response_model=ChartResp)
def stock_chart(code: str, n: int = 250) -> ChartResp:
    return ChartResp(**chart.stock_chart(code, n=n))


@router.post("/{code}/ai-report", response_model=AiReportJob)
def gen_ai_report(code: str) -> AiReportJob:
    """触发异步生成 AI 投研报告（LLM 走后台，非请求路径）。"""
    job_id = jobs.submit_job("ai_research", {"code": code})
    return AiReportJob(job_id=job_id)


@router.get("/{code}/ai-report", response_model=AiReportResp)
def get_ai_report(code: str) -> AiReportResp:
    """读缓存的 AI 投研报告（只读，无则 report=null）。"""
    return AiReportResp(report=research_cache.read_report(code))
