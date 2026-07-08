import type { ScorecardSummary as SS } from "../api/types";

function pct(v: number | null): string {
  return v == null ? "—" : `${(v * 100).toFixed(2)}%`;
}
function signPct(v: number | null): string {
  return v == null ? "—" : `${v >= 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;
}
function toneCls(v: number | null): string {
  if (v == null) return "text-slate-400";
  return v >= 0 ? "text-red-400" : "text-green-400";
}

export default function ScorecardSummary({ data: d }: { data: SS }) {
  const s = d.sample;
  if (s.picks === 0) {
    return (
      <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        <h2 className="text-lg font-bold text-slate-100">📈 推荐效果看板</h2>
        <p className="mt-2 text-sm text-slate-500">暂无推荐台账（每日收盘后落库，积累后显示）。</p>
      </section>
    );
  }
  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold text-slate-100">📈 推荐效果看板</h2>
        <span className="text-xs text-slate-500">{s.start} ~ {s.end}</span>
      </div>
      <p className="mt-1 text-xs text-slate-400">
        样本 {s.picks} 条 / {s.snapshots} 快照日 · 实时 {s.live} / 回放 {s.replay}
      </p>

      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-sm text-slate-100">
          <caption className="mb-1 text-left text-xs text-slate-400">Top-N 平均超额（相对沪深300，外部有效性头号指标）</caption>
          <thead className="text-xs text-slate-500">
            <tr className="border-b border-slate-700">
              <th className="py-1 text-left">持有期</th><th className="text-right">已结算</th>
              <th className="text-right">pending</th><th className="text-right">平均超额</th>
              <th className="text-right">胜率</th><th className="text-right">绝对收益</th>
            </tr>
          </thead>
          <tbody>
            {d.horizons.map((h) => (
              <tr key={h.h} className="border-b border-slate-800">
                <td className="py-1">T+{h.h}</td>
                <td className="text-right text-slate-400">{h.settled}</td>
                <td className="text-right text-slate-500">{h.pending}</td>
                <td className={`text-right font-mono ${toneCls(h.mean_excess)}`}>{signPct(h.mean_excess)}</td>
                <td className="text-right text-slate-300">{pct(h.win_rate)}</td>
                <td className={`text-right font-mono ${toneCls(h.mean_ret)}`}>{signPct(h.mean_ret)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-sm text-slate-100">
          <caption className="mb-1 text-left text-xs text-slate-400">Live Rank-IC（池内排序质量，非全市场多空）</caption>
          <thead className="text-xs text-slate-500">
            <tr className="border-b border-slate-700">
              <th className="py-1 text-left">持有期</th><th className="text-right">截面数</th>
              <th className="text-right">平均 Rank-IC</th><th className="text-right">IR</th>
            </tr>
          </thead>
          <tbody>
            {d.rank_ic.map((r) => (
              <tr key={r.h} className="border-b border-slate-800">
                <td className="py-1">T+{r.h}</td>
                <td className="text-right text-slate-400">{r.n}</td>
                <td className={`text-right font-mono ${toneCls(r.mean_ic)}`}>{r.mean_ic == null ? "—" : r.mean_ic.toFixed(4)}</td>
                <td className={`text-right font-mono ${toneCls(r.ir)}`}>{r.ir == null ? "—" : r.ir.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {d.delisted > 0 && (
        <p className="mt-2 text-xs text-amber-500">⚠ 含 {d.delisted} 条停牌/退市标的（前向收益用最后可得价，存幸存偏差）。</p>
      )}
      <p className="mt-1 text-xs text-slate-600">仅供研究参考，不构成投资建议。</p>
    </section>
  );
}
