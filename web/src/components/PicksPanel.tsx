import type { Picks } from "../api/types";

export default function PicksPanel({ data, onPick }: { data: Picks; onPick?: (code: string) => void }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">每日建仓名单</h2>
      <table className="mt-2 w-full text-sm">
        <thead className="text-gray-500">
          <tr><th className="text-left">代码</th><th className="text-left">名称</th><th className="text-right">综合分</th></tr>
        </thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={r.code} className="cursor-pointer hover:bg-gray-50" onClick={() => onPick?.(r.code)}>
              <td>{r.code}</td><td>{r.name}</td><td className="text-right">{r.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
