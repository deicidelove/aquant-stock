import type { Regime } from "../../api/types";
import { Card, Badge } from "../../ui/atoms";

export default function RegimePanel({ data }: { data: Regime }) {
  if (!data.state) return <Card title="今日研判"><p className="text-sm text-slate-500">数据不足</p></Card>;
  const tone = data.state === "进攻" ? "red" : data.state === "防守" ? "green" : "amber";
  return (
    <Card title="今日研判">
      <div className="flex items-center gap-3">
        <Badge tone={tone}><span className="text-base">{data.state}</span></Badge>
        <span className="text-sm text-slate-300">建议仓位 {data.suggested_position ?? "—"}</span>
      </div>
      {data.note && <p className="mt-2 text-sm text-slate-400">{data.note}</p>}
    </Card>
  );
}
