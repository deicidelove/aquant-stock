import type { TopScores } from "../api/types";

export default function TopScoresPanel({ data, onPick }: { data: TopScores; onPick?: (code: string) => void }) {
  return (
    <section className="rounded-lg border border-slate-700 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">综合分高分股</h2>
        <span className="text-xs text-slate-500">{data.as_of ?? "—"}</span>
      </div>
      <table className="mt-2 w-full text-sm">
        <thead className="text-slate-400">
          <tr><th className="text-left">代码</th><th className="text-left">名称</th><th className="text-right">综合分</th></tr>
        </thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={r.code} className="cursor-pointer hover:bg-slate-800" onClick={() => onPick?.(r.code)}>
              <td>{r.code}</td><td>{r.name}</td><td className="text-right">{r.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
