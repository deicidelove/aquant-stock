import type { NorthFlow } from "../../api/types";
import { Card } from "../../ui/atoms";

export default function NorthFlowPanel({ data: d }: { data: NorthFlow }) {
  return (
    <Card title="北向资金">
      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-500">暂无北向数据。</p>
      ) : (
        <ul className="space-y-1">
          {d.rows.map((r) => {
            const v = r.net ?? 0;
            return (
              <li key={r.market} className="flex items-center justify-between text-sm">
                <span className="text-slate-300">{r.market}</span>
                <span className={`font-mono ${v >= 0 ? "text-red-400" : "text-green-400"}`}>
                  {v >= 0 ? "+" : ""}{v.toFixed(1)} 亿
                </span>
              </li>
            );
          })}
        </ul>
      )}
      <p className="mt-2 text-xs text-slate-600">沪深股通实时净额自2024-08停发，此处为可得口径。</p>
    </Card>
  );
}
