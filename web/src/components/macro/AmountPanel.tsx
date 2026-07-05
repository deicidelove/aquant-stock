import type { AmountTrend } from "../../api/types";
import { Card } from "../../ui/atoms";
import EChart from "../../charts/EChart";
import { buildAmountBarOption } from "../../charts/options";

export default function AmountPanel({ data }: { data: AmountTrend }) {
  const last = data.series[data.series.length - 1];
  return (
    <Card title="两市量能" right={<span className="text-xs text-slate-400">{last ? `${last.amount} 亿` : ""}</span>}>
      <EChart option={buildAmountBarOption(data.series)} height={180} />
    </Card>
  );
}
