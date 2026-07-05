import type { ScorecardResp } from "../api/types";

export default function ScorecardPanel({ data }: { data: ScorecardResp }) {
  if (data.rows.length === 0) {
    return (
      <section className="rounded-lg border border-slate-700 p-4">
        <h2 className="text-lg font-bold">推荐记分卡</h2>
        <p className="mt-2 text-sm text-slate-500">暂无台账数据（需积累每日推荐快照或跑回放）。</p>
      </section>
    );
  }
  const cols = Object.keys(data.rows[0]);
  return (
    <section className="rounded-lg border border-slate-700 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">推荐记分卡</h2>
        <span className="text-xs text-slate-500">{data.as_of ?? "—"}</span>
      </div>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400"><tr>{cols.map((c) => <th key={c} className="text-left">{c}</th>)}</tr></thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={i} className="border-b border-slate-800">{cols.map((c) => <td key={c}>{String(row[c] ?? "—")}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
