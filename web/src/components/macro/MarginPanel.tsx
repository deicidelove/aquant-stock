import type { Margin } from "../../api/types";
import { Card } from "../../ui/atoms";
import EChart from "../../charts/EChart";
import { buildSparklineOption } from "../../charts/options";

export default function MarginPanel({ data: d }: { data: Margin }) {
  const spark = d.series.map((s) => ({ date: s.date, close: s.total_fin }));
  const trend = d.series.length > 1 ? d.series[d.series.length - 1].total_fin - d.series[0].total_fin : 0;
  return (
    <Card title="融资融券（杠杆资金）">
      {d.total_fin == null ? (
        <p className="text-sm text-slate-500">暂无融资融券数据。</p>
      ) : (
        <>
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-slate-400">两市融资余额</span>
            <span className="font-mono text-lg font-semibold text-slate-100">{d.total_fin.toLocaleString()} 亿</span>
          </div>
          <div className="mt-1 text-xs text-slate-500">
            近{d.series.length}日 {trend >= 0 ? <span className="text-red-400">↑ +{trend.toFixed(0)}亿</span> : <span className="text-green-400">↓ {trend.toFixed(0)}亿</span>}
          </div>
          {spark.length > 1 && <div className="mt-2"><EChart option={buildSparklineOption(spark)} height={48} /></div>}
        </>
      )}
    </Card>
  );
}
