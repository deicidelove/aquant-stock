#!/bin/bash
# 每日例程封装：供 cron / launchd 定时调度（A股收盘后约 15:30 跑）。
# 用法：bash scripts/run_daily.sh   或加入 crontab。
set -euo pipefail

PROJ="/Volumes/demon/code/ml/study/stock"
PY="$(command -v python3)"
cd "$PROJ"
export PYTHONPATH="$PROJ"

mkdir -p logs
LOG="logs/run_daily_$(date +%Y%m%d).log"

echo "===== run_daily $(date '+%Y-%m-%d %H:%M:%S') =====" >> "$LOG"
"$PY" -u -m aquant.cli run-daily >> "$LOG" 2>&1
echo "exit=$? $(date '+%H:%M:%S')" >> "$LOG"
