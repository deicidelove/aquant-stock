import type { StockChart } from "../api/types";
import EChart from "../charts/EChart";
import { buildProKlineOption } from "../charts/options";

export default function ProKlineChart({ chart, plan }: {
  chart: StockChart; plan?: { stop_loss?: number; take_profit?: number };
}) {
  return <EChart option={buildProKlineOption(chart, plan)} height={480} />;
}
