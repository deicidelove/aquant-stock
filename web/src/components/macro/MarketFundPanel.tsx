import type { MarketFund } from "../../api/types";
import { Card } from "../../ui/atoms";
import EChart from "../../charts/EChart";
import { buildMarketFundOption } from "../../charts/options";

export default function MarketFundPanel({ data }: { data: MarketFund }) {
  const tone = data.today >= 0 ? "text-red-400" : "text-green-400";
  return (
    <Card title="大盘资金" right={<span className={"font-mono " + tone}>今日 {data.today >= 0 ? "+" : ""}{data.today} 亿</span>}>
      <EChart option={buildMarketFundOption(data.series)} height={200} />
    </Card>
  );
}
