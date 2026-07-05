import type { Holding } from "../api/types";

export default function HoldingsPanel({ rows, onPick }: { rows: Holding[]; onPick?: (code: string) => void }) {
  return (
    <section className="rounded-lg border border-slate-700 p-4">
      <h2 className="text-lg font-bold">我的持仓</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">暂无持仓，去“选票”建仓或在下方录入交易。</p>
      ) : (
        <table className="mt-2 w-full text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="text-left">代码</th><th className="text-left">名称</th>
              <th className="text-right">持股</th><th className="text-right">成本</th>
              <th className="text-right">现价</th><th className="text-right">浮盈亏%</th>
              <th className="text-left">提醒</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.code} className="cursor-pointer hover:bg-slate-800" onClick={() => onPick?.(r.code)}>
                <td>{r.code}</td><td>{r.name}</td>
                <td className="text-right">{r.shares}</td><td className="text-right">{r.avg_cost}</td>
                <td className="text-right">{r.last_price ?? "—"}</td>
                <td className={"text-right " + (r.unrealized_pct >= 0 ? "text-red-500" : "text-green-600")}>
                  {r.unrealized_pct >= 0 ? "+" : ""}{r.unrealized_pct}%
                </td>
                <td className="text-red-600">{r.alerts.map((a) => <span key={a} className="mr-1">{a}</span>)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
