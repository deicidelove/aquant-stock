import type { LimitLadder } from "../../api/types";
import { Card, Stat, Badge } from "../../ui/atoms";

function pct(v: number | null): string {
  return v == null ? "-" : `${(v * 100).toFixed(0)}%`;
}

export default function LimitLadderPanel({ data: d }: { data: LimitLadder }) {
  const sealTone = (d.seal_rate ?? 0) >= 0.7 ? "red" : (d.seal_rate ?? 0) >= 0.5 ? "amber" : "green";
  const maxCount = Math.max(1, ...d.ladder.map((x) => x.count));
  return (
    <Card title="涨停梯队 / 情绪" right={<Badge tone={sealTone}><span>封板 {pct(d.seal_rate)}</span></Badge>}>
      <div className="grid grid-cols-3 gap-2">
        <Stat label="涨停家数" value={d.limit_up_count} tone="up" />
        <Stat label="最高板" value={`${d.max_boards}板`} tone="up" />
        <Stat label="炸板率" value={pct(d.break_rate)} tone="down" />
      </div>
      {d.ladder.length > 0 && (
        <div className="mt-3 space-y-1">
          {d.ladder.map((row) => (
            <div key={row.boards} className="flex items-center gap-2 text-xs">
              <span className="w-10 shrink-0 text-right font-mono text-amber-400">{row.boards}板</span>
              <div className="h-4 rounded bg-red-500/60" style={{ width: `${(row.count / maxCount) * 60}%`, minWidth: "8px" }} />
              <span className="shrink-0 text-slate-400">{row.count}</span>
              <span className="truncate text-slate-300" title={row.names.join("、")}>{row.names.slice(0, 3).join(" ")}</span>
            </div>
          ))}
        </div>
      )}
      {d.by_industry.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {d.by_industry.map((s) => (
            <span key={s.industry} className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-300">
              {s.industry} <span className="text-amber-400">{s.count}</span>
            </span>
          ))}
        </div>
      )}
      {d.ladder.length === 0 && <p className="text-sm text-slate-500">暂无涨停数据（盘中/收盘后抓取）。</p>}
    </Card>
  );
}
