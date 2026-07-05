import type { SectorFund } from "../../api/types";
import { Card } from "../../ui/atoms";
import EChart from "../../charts/EChart";
import { buildSectorFundTreemapOption } from "../../charts/options";

export default function SectorFundPanel({ data }: { data: SectorFund }) {
  const top = [...data.rows].sort((a, b) => b.main_net - a.main_net).slice(0, 6);
  return (
    <Card title="板块资金">
      <EChart option={buildSectorFundTreemapOption(data.rows)} height={220} />
      <ul className="mt-2 text-sm">
        {top.map((s) => (
          <li key={s.sector} className="flex justify-between border-b border-slate-800 py-1">
            <span className="text-slate-200">{s.sector}</span>
            <span className={s.main_net >= 0 ? "text-red-400" : "text-green-400"}>
              {(s.main_net / 1e8).toFixed(1)} 亿
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
