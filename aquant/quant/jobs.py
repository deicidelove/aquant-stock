"""量化异步任务运行器：DuckDB 落状态，线程池执行（测试可同步）。"""
from __future__ import annotations

import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable

import pandas as pd

from ..data import store

_SYNC = os.getenv("AQUANT_JOBS_SYNC") == "1"
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="quantjob")
_RUNNERS: dict[str, Callable[[dict], dict]] = {}


def register(kind: str, fn: Callable[[dict], dict]) -> None:
    _RUNNERS[kind] = fn


def _write(row: dict) -> None:
    store.save("quant_jobs", pd.DataFrame([row]))


def submit_job(kind: str, params: dict) -> str:
    job_id = uuid.uuid4().hex
    _write({"job_id": job_id, "kind": kind, "params_json": json.dumps(params),
            "status": "pending", "result_json": None, "error": None,
            "created_ts": datetime.now().isoformat(timespec="seconds")})
    if _SYNC:
        run_job(job_id)
    else:
        _EXECUTOR.submit(run_job, job_id)
    return job_id


def _row(job_id: str) -> dict | None:
    if not store.has_table("quant_jobs"):
        return None
    df = store.query("SELECT * FROM quant_jobs WHERE job_id = ?", [job_id])
    return df.iloc[0].to_dict() if not df.empty else None


def run_job(job_id: str) -> None:
    row = _row(job_id)
    if row is None:
        return
    kind, params = row["kind"], json.loads(row["params_json"])
    base = {"job_id": job_id, "kind": kind, "params_json": row["params_json"],
            "created_ts": row["created_ts"]}
    try:
        fn = _RUNNERS[kind]
        result = fn(params)
        _write({**base, "status": "done", "result_json": json.dumps(result), "error": None})
    except Exception as e:  # noqa: BLE001 任务失败要落库，不可吞
        _write({**base, "status": "error", "result_json": None, "error": str(e)[:500]})


def get_job(job_id: str) -> dict | None:
    row = _row(job_id)
    if row is None:
        return None
    result = json.loads(row["result_json"]) if row.get("result_json") else None
    return {"job_id": job_id, "kind": row["kind"], "status": row["status"],
            "result": result, "error": row.get("error"), "created_ts": row["created_ts"]}
