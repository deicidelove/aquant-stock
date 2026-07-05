import type { IndexRow } from "../../api/types";
import { Card, Stat } from "../../ui/atoms";

const NAME: Record<string, string> = { sh000300: "沪深300", sh000001: "上证指数", sz399006: "创业板指" };

export default function IndicesPanel({ rows }: { rows: IndexRow[] }) {
  return (
    <Card title="大盘指数">
      <div className="grid grid-cols-3 gap-3">
        {rows.map((r) => (
          <div key={r.code} className="rounded bg-slate-800 p-2">
            <div className="text-xs text-slate-400">{NAME[r.code] ?? r.code}</div>
            <div className="font-mono text-lg font-semibold text-slate-100">{r.close}</div>
            <div className={"text-xs " + ((r.ret_20d ?? 0) >= 0 ? "text-red-400" : "text-green-400")}>
              20日 {r.ret_20d ?? "—"}%
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
