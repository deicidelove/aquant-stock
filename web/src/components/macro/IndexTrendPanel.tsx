import type { IndexSeries } from "../../api/types";
import { Card } from "../../ui/atoms";
import EChart from "../../charts/EChart";
import { buildIndexTrendOption } from "../../charts/options";

const NAME: Record<string, string> = { sh000300: "沪深300", sh000001: "上证指数", sz399006: "创业板指" };

export default function IndexTrendPanel({ data }: { data: IndexSeries }) {
  const last = data.points[data.points.length - 1];
  const tag = last && last.ma20 != null ? (last.close >= last.ma20 ? "站上MA20" : "跌破MA20") : "";
  return (
    <Card title={(NAME[data.code] ?? data.code) + " 走势"} right={<span className="text-xs text-slate-400">{tag}</span>}>
      <EChart option={buildIndexTrendOption(data.points)} height={260} />
    </Card>
  );
}
