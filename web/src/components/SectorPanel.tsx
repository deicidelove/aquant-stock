import type { Sectors } from "../api/types";
import EChart from "../charts/EChart";
import { buildSectorTreemapOption } from "../charts/options";

export default function SectorPanel({ data }: { data: Sectors }) {
  const top = [...data.rows].sort((a, b) => b.pct_chg - a.pct_chg).slice(0, 5);
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">板块概览</h2>
        <span className="text-xs text-gray-400">{data.as_of ?? "无快照"}</span>
      </div>
      <EChart option={buildSectorTreemapOption(data.rows)} height={260} />
      <ul className="mt-2 text-sm">
        {top.map((s) => (
          <li key={s.sector} className="flex justify-between border-b py-1">
            <span>{s.sector}</span>
            <span className={s.pct_chg >= 0 ? "text-red-500" : "text-green-600"}>
              {s.pct_chg >= 0 ? "+" : ""}{s.pct_chg}%
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
