from fastapi import APIRouter, HTTPException

import aquant.quant  # noqa: F401 触发 backtest/factor_ic 任务注册
from aquant.quant import jobs
from aquant.select import scorer
from server.schemas.quant import BacktestIn, FactorIcIn, JobCreated, JobResp, WeightsResp

router = APIRouter(prefix="/api/quant", tags=["quant"])


@router.get("/weights", response_model=WeightsResp)
def weights() -> WeightsResp:
    return WeightsResp(ic=dict(scorer.IC_WEIGHTS), momentum=dict(scorer.MOMENTUM_WEIGHTS))


@router.post("/backtest", response_model=JobCreated)
def submit_backtest(body: BacktestIn) -> JobCreated:
    return JobCreated(job_id=jobs.submit_job("backtest", body.model_dump()))


@router.post("/factor-ic", response_model=JobCreated)
def submit_factor_ic(body: FactorIcIn) -> JobCreated:
    return JobCreated(job_id=jobs.submit_job("factor_ic", body.model_dump()))


def _job_or_404(job_id: str, kind: str) -> JobResp:
    job = jobs.get_job(job_id)
    if job is None or job["kind"] != kind:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResp(**job)


@router.get("/backtest/{job_id}", response_model=JobResp)
def backtest_status(job_id: str) -> JobResp:
    return _job_or_404(job_id, "backtest")


@router.get("/factor-ic/{job_id}", response_model=JobResp)
def factor_ic_status(job_id: str) -> JobResp:
    return _job_or_404(job_id, "factor_ic")
