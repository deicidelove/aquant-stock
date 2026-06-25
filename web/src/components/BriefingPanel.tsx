import type { BriefingRow } from "../api/types";

const COLS: [string, string][] = [
  ["综合分", "综合分"], ["信号", "信号"], ["买点", "买点"], ["止损", "止损"], ["目标", "目标"],
];

export default function BriefingPanel({ rows, onPick }: { rows: BriefingRow[]; onPick?: (code: string) => void }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">研报速览</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-gray-400">暂无候选。</p>
      ) : (
        <table className="mt-2 w-full text-sm">
          <thead className="text-gray-500">
            <tr><th className="text-left">代码</th><th className="text-left">名称</th>{COLS.map(([, h]) => <th key={h} className="text-right">{h}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.code} className="cursor-pointer hover:bg-gray-50" onClick={() => onPick?.(r.code)}>
                <td>{r.code}</td><td>{String(r.name)}</td>
                {COLS.map(([k]) => <td key={k} className="text-right">{String(r[k] ?? "—")}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
