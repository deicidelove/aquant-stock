import type { Abnormal } from "../../api/types";
import { Card, Badge } from "../../ui/atoms";

export default function AbnormalPanel({ data }: { data: Abnormal }) {
  return (
    <Card title={"异常资金 · " + (data.scope === "sector" ? "板块" : "个股")}>
      {data.rows.length === 0 ? (
        <p className="text-sm text-slate-500">暂无显著异常（历史积累越多越准）。</p>
      ) : (
        <table className="w-full text-sm">
          <thead className="text-slate-400"><tr><th className="text-left">标的</th><th className="text-right">今日净额(亿)</th><th className="text-right">z</th></tr></thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={r.key} className="border-b border-slate-800">
                <td className="text-slate-200">{r.key}</td>
                <td className={"text-right " + (r.latest >= 0 ? "text-red-400" : "text-green-400")}>{(r.latest / 1e8).toFixed(2)}</td>
                <td className="text-right"><Badge tone={Math.abs(r.z) >= 3 ? "red" : "amber"}><span>{r.z}</span></Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
