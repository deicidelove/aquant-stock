import type { Overview } from "../api/types";
import EChart from "../charts/EChart";
import { buildIndexBarOption } from "../charts/options";

export default function OverviewPanel({ data }: { data: Overview }) {
  const { breadth: b, regime, index } = data;
  return (
    <section className="rounded-lg border border-slate-700 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">大盘总览</h2>
        <span className="rounded bg-slate-800 px-2 py-1 text-sm">
          市场：<span>{regime.state}</span>（建议仓位 {regime.suggested_position ?? "—"}）
        </span>
      </div>
      <div className="mt-3 grid grid-cols-4 gap-3 text-center text-sm">
        <Stat label="上涨" value={b.up} />
        <Stat label="下跌" value={b.down} />
        <Stat label="涨停" value={b.limit_up} />
        <Stat label="上涨占比%" value={b.up_ratio} />
      </div>
      <div className="mt-3 text-sm text-slate-300">
        沪深300 收盘 <b>{index.close}</b>（20日 {index.ret_20d ?? "—"}% / 60日 {index.ret_60d ?? "—"}%）
      </div>
      <EChart option={buildIndexBarOption(b)} height={140} />
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded bg-slate-800 p-2">
      <div className="text-slate-400">{label}</div>
      <div className="text-base font-semibold">{value}</div>
    </div>
  );
}
