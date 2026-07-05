import type { Pnl } from "../api/types";

export default function PnlSummary({ pnl }: { pnl: Pnl }) {
  const items = [
    { label: "已实现", value: pnl.realized },
    { label: "未实现", value: pnl.unrealized },
    { label: "合计", value: pnl.total },
  ];
  return (
    <section className="rounded-lg border border-slate-700 p-4">
      <h2 className="text-lg font-bold">盈亏汇总</h2>
      <div className="mt-2 grid grid-cols-3 gap-3 text-center">
        {items.map((it) => (
          <div key={it.label} className="rounded bg-slate-800 p-2">
            <div className="text-slate-400 text-sm">{it.label}</div>
            <div className={"text-base font-semibold " + (it.value >= 0 ? "text-red-500" : "text-green-600")}>
              <span>{it.value}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
