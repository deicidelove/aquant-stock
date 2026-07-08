import type { BlockTrade } from "../../api/types";
import { Card } from "../../ui/atoms";

export default function BlockTradePanel({ data: d }: { data: BlockTrade }) {
  return (
    <Card title="大宗交易">
      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-500">暂无大宗交易数据。</p>
      ) : (
        <ul className="space-y-1">
          {d.rows.slice(0, 6).map((r) => {
            const pr = r.premium_ratio;
            return (
              <li key={r.date} className="flex items-center justify-between text-sm">
                <span className="text-slate-400">{r.date.slice(5)}</span>
                <span className="font-mono text-slate-200">{r.total_amount ?? "-"} 亿</span>
                <span className={`font-mono text-xs ${pr != null && pr >= 0.5 ? "text-red-400" : "text-green-400"}`}>
                  溢价 {pr == null ? "-" : `${(pr * 100).toFixed(0)}%`}
                </span>
              </li>
            );
          })}
        </ul>
      )}
      <p className="mt-2 text-xs text-slate-600">溢价占比高 = 资金愿溢价接盘，偏积极。</p>
    </Card>
  );
}
