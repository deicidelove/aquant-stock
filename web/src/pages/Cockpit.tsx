import { useIndices, useSentiment, useMarketFund, useSectorFund, useAbnormal } from "../hooks/queries";
import { isTradingHours } from "../lib/tradingHours";
import { UpdatedAt } from "../ui/atoms";
import IndicesPanel from "../components/macro/IndicesPanel";
import SentimentPanel from "../components/macro/SentimentPanel";
import MarketFundPanel from "../components/macro/MarketFundPanel";
import SectorFundPanel from "../components/macro/SectorFundPanel";
import AbnormalPanel from "../components/macro/AbnormalPanel";

export default function Cockpit() {
  const indices = useIndices();
  const sentiment = useSentiment();
  const marketFund = useMarketFund();
  const sectorFund = useSectorFund();
  const abnormal = useAbnormal("stock");
  const now = new Date();
  return (
    <div className="space-y-4 p-4">
      <div className="flex items-baseline justify-between">
        <h1 className="text-2xl font-bold text-slate-100">🛰 驾驶舱</h1>
        <UpdatedAt at={now.toLocaleTimeString("zh-CN")} live={isTradingHours(now)} />
      </div>
      {indices.isSuccess && <IndicesPanel rows={indices.data.rows} />}
      <div className="grid gap-4 lg:grid-cols-2">
        {sentiment.isSuccess && <SentimentPanel data={sentiment.data} />}
        {marketFund.isSuccess && <MarketFundPanel data={marketFund.data} />}
        {sectorFund.isSuccess && <SectorFundPanel data={sectorFund.data} />}
        {abnormal.isSuccess && <AbnormalPanel data={abnormal.data} />}
      </div>
    </div>
  );
}
